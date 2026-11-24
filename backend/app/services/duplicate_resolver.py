import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import cdist
import cv2
from .image_analyzer import BoundingBox

logger = logging.getLogger(__name__)

@dataclass
class DetectionCluster:
    """Represents a cluster of similar detections."""
    detections: List[BoundingBox]
    centroid: Tuple[float, float]
    confidence: float
    label: str
    cluster_id: int

class DuplicateResolver:
    """
    Advanced duplicate detection and resolution system.
    Uses spatial clustering, feature matching, and intelligent filtering.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.spatial_clusterer = SpatialClusterer(self.config["spatial_clustering"])
        self.feature_matcher = FeatureMatcher(self.config["feature_matching"])
        self.overlap_resolver = OverlapResolver(self.config["overlap_resolution"])
        
    def _default_config(self) -> Dict[str, Any]:
        return {
            "spatial_clustering": {
                "enabled": True,
                "method": "dbscan",
                "eps": 0.05,  # Reduced from 0.1 to be less aggressive
                "min_samples": 1,
                "metric": "euclidean"
            },
            "overlap_resolution": {
                "enabled": True,
                "iou_threshold": 0.3,  # Reduced from 0.5 to allow more overlap
                "confidence_weight": 0.7,
                "size_weight": 0.3
            },
            "feature_matching": {
                "enabled": True,
                "similarity_threshold": 0.8,
                "feature_type": "combined"  # "position", "size", "combined"
            },
            "size_filtering": {
                "enabled": True,
                "min_area": 0.001,
                "max_area": 0.5,
                "aspect_ratio_range": (0.2, 5.0)
            },
            "confidence_filtering": {
                "enabled": True,
                "min_confidence": 0.1,  # Keep low for soda cans
                "low_confidence_penalty": 0.5
            }
        }
    
    def resolve_duplicates(self, detections: List[BoundingBox]) -> Tuple[List[BoundingBox], Dict[str, Any]]:
        """
        Resolve duplicate detections using multiple techniques.
        For shelf items, be much less aggressive to avoid removing legitimate detections.
        """
        if not detections:
            return [], {"original_count": 0, "final_count": 0, "resolution_method": "empty"}
        
        try:
            metadata = {
                "original_count": len(detections),
                "resolution_steps": [],
                "filters_applied": []
            }
            
            # Step 1: Size filtering
            if self.config["size_filtering"]["enabled"]:
                detections, size_stats = self._filter_by_size(detections)
                metadata["resolution_steps"].append("size_filtering")
                metadata["filters_applied"].append(f"size: {size_stats}")
            
            # Step 2: Confidence filtering
            if self.config["confidence_filtering"]["enabled"]:
                detections, conf_stats = self._filter_by_confidence(detections)
                metadata["resolution_steps"].append("confidence_filtering")
                metadata["filters_applied"].append(f"confidence: {conf_stats}")
            
            # Step 3: Skip spatial clustering for shelf items (they're naturally close together)
            logger.info(f"Skipping spatial clustering for shelf items - keeping {len(detections)} individual detections")
            clustered_detections = detections
            metadata["resolution_steps"].append("spatial_clustering_skipped")
            metadata["clusters_found"] = len(detections)
            
            # Step 4: Overlap resolution (only for very high overlap)
            if self.config["overlap_resolution"]["enabled"] and len(clustered_detections) > 1:
                final_detections, overlap_stats = self.overlap_resolver.resolve_overlaps(
                    clustered_detections
                )
                metadata["resolution_steps"].append("overlap_resolution")
                metadata["filters_applied"].append(f"overlap: {overlap_stats}")
            else:
                final_detections = clustered_detections
            
            metadata.update({
                "final_count": len(final_detections),
                "reduction_ratio": 1.0 - (len(final_detections) / len(detections)) if detections else 0.0,
                "resolution_success": True
            })
            
            logger.info(f"Duplicate resolution: {len(detections)} -> {len(final_detections)} detections (less aggressive for shelf items)")
            return final_detections, metadata
            
        except Exception as e:
            logger.error(f"Duplicate resolution failed: {str(e)}")
            return detections, {"resolution_success": False, "error": str(e)}
    
    def _filter_by_size(self, detections: List[BoundingBox]) -> Tuple[List[BoundingBox], Dict[str, int]]:
        """Filter detections by size constraints."""
        config = self.config["size_filtering"]
        filtered = []
        
        min_area = config["min_area"]
        max_area = config["max_area"]
        min_ratio, max_ratio = config["aspect_ratio_range"]
        
        for detection in detections:
            area = (detection.x2 - detection.x1) * (detection.y2 - detection.y1)
            width = detection.x2 - detection.x1
            height = detection.y2 - detection.y1
            
            if width > 0 and height > 0:
                aspect_ratio = width / height
                
                if (min_area <= area <= max_area and 
                    min_ratio <= aspect_ratio <= max_ratio):
                    filtered.append(detection)
        
        stats = {
            "filtered_out": len(detections) - len(filtered),
            "remaining": len(filtered)
        }
        
        return filtered, stats
    
    def _filter_by_confidence(self, detections: List[BoundingBox]) -> Tuple[List[BoundingBox], Dict[str, int]]:
        """Filter detections by confidence thresholds."""
        config = self.config["confidence_filtering"]
        filtered = []
        
        min_confidence = config["min_confidence"]
        
        for detection in detections:
            if detection.confidence >= min_confidence:
                filtered.append(detection)
        
        stats = {
            "filtered_out": len(detections) - len(filtered),
            "remaining": len(filtered)
        }
        
        return filtered, stats
    
    def _resolve_cluster(self, cluster: DetectionCluster) -> BoundingBox:
        """
        Resolve a cluster of detections to a single detection.
        Uses weighted averaging based on confidence and size.
        """
        if len(cluster.detections) == 1:
            return cluster.detections[0]
        
        # Calculate weighted averages
        total_weight = 0
        weighted_x1 = 0
        weighted_y1 = 0
        weighted_x2 = 0
        weighted_y2 = 0
        weighted_confidence = 0
        
        for detection in cluster.detections:
            # Weight by confidence and area
            area = (detection.x2 - detection.x1) * (detection.y2 - detection.y1)
            weight = detection.confidence * np.sqrt(area)
            
            weighted_x1 += detection.x1 * weight
            weighted_y1 += detection.y1 * weight
            weighted_x2 += detection.x2 * weight
            weighted_y2 += detection.y2 * weight
            weighted_confidence += detection.confidence * weight
            total_weight += weight
        
        if total_weight > 0:
            # Create merged detection
            merged = BoundingBox(
                x1=weighted_x1 / total_weight,
                y1=weighted_y1 / total_weight,
                x2=weighted_x2 / total_weight,
                y2=weighted_y2 / total_weight,
                label=cluster.label,
                confidence=weighted_confidence / total_weight
            )
            return merged
        else:
            # Fallback to simple averaging
            return BoundingBox(
                x1=np.mean([d.x1 for d in cluster.detections]),
                y1=np.mean([d.y1 for d in cluster.detections]),
                x2=np.mean([d.x2 for d in cluster.detections]),
                y2=np.mean([d.y2 for d in cluster.detections]),
                label=cluster.label,
                confidence=np.mean([d.confidence for d in cluster.detections])
            )


class SpatialClusterer:
    """Handles spatial clustering of detections."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    def cluster_detections(self, detections: List[BoundingBox]) -> List[DetectionCluster]:
        """
        Cluster detections spatially using DBSCAN.
        
        Args:
            detections: List of bounding box detections
            
        Returns:
            List of detection clusters
        """
        if len(detections) <= 1:
            return [DetectionCluster(
                detections=detections,
                centroid=self._get_centroid(detections[0]),
                confidence=detections[0].confidence,
                label=detections[0].label,
                cluster_id=0
            )]
        
        try:
            # Extract center points for clustering
            centers = []
            for detection in detections:
                center_x = (detection.x1 + detection.x2) / 2
                center_y = (detection.y1 + detection.y2) / 2
                centers.append([center_x, center_y])
            
            centers_array = np.array(centers)
            
            # Apply DBSCAN clustering
            clustering = DBSCAN(
                eps=self.config["eps"],
                min_samples=self.config["min_samples"],
                metric=self.config["metric"]
            )
            
            cluster_labels = clustering.fit_predict(centers_array)
            
            # Group detections by cluster
            clusters = []
            unique_labels = set(cluster_labels)
            
            for cluster_id in unique_labels:
                if cluster_id == -1:  # Noise points
                    continue
                
                # Get detections in this cluster
                cluster_detections = [
                    detections[i] for i, label in enumerate(cluster_labels) 
                    if label == cluster_id
                ]
                
                if cluster_detections:
                    # Calculate cluster centroid
                    cluster_centers = centers_array[cluster_labels == cluster_id]
                    centroid = (
                        np.mean(cluster_centers[:, 0]),
                        np.mean(cluster_centers[:, 1])
                    )
                    
                    # Get dominant label and average confidence
                    labels = [d.label for d in cluster_detections]
                    dominant_label = max(set(labels), key=labels.count)
                    avg_confidence = np.mean([d.confidence for d in cluster_detections])
                    
                    cluster = DetectionCluster(
                        detections=cluster_detections,
                        centroid=centroid,
                        confidence=avg_confidence,
                        label=dominant_label,
                        cluster_id=int(cluster_id)
                    )
                    clusters.append(cluster)
            
            logger.info(f"Spatial clustering completed: {len(clusters)} clusters from {len(detections)} detections")
            return clusters
            
        except Exception as e:
            logger.error(f"Spatial clustering failed: {str(e)}")
            # Return individual detections as clusters
            return [
                DetectionCluster(
                    detections=[detection],
                    centroid=self._get_centroid(detection),
                    confidence=detection.confidence,
                    label=detection.label,
                    cluster_id=i
                )
                for i, detection in enumerate(detections)
            ]
    
    def _get_centroid(self, detection: BoundingBox) -> Tuple[float, float]:
        """Get centroid of a bounding box."""
        center_x = (detection.x1 + detection.x2) / 2
        center_y = (detection.y1 + detection.y2) / 2
        return (center_x, center_y)


class FeatureMatcher:
    """Handles feature-based matching of detections."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    def calculate_similarity(self, det1: BoundingBox, det2: BoundingBox) -> float:
        """
        Calculate similarity between two detections.
        
        Args:
            det1, det2: Bounding box detections
            
        Returns:
            Similarity score (0-1)
        """
        if self.config["feature_type"] == "position":
            return self._position_similarity(det1, det2)
        elif self.config["feature_type"] == "size":
            return self._size_similarity(det1, det2)
        elif self.config["feature_type"] == "combined":
            return self._combined_similarity(det1, det2)
        else:
            return 0.0
    
    def _position_similarity(self, det1: BoundingBox, det2: BoundingBox) -> float:
        """Calculate position-based similarity."""
        center1 = ((det1.x1 + det1.x2) / 2, (det1.y1 + det1.y2) / 2)
        center2 = ((det2.x1 + det2.x2) / 2, (det2.y1 + det2.y2) / 2)
        
        distance = np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)
        max_distance = np.sqrt(2)  # Maximum possible distance in normalized coordinates
        
        return 1.0 - (distance / max_distance)
    
    def _size_similarity(self, det1: BoundingBox, det2: BoundingBox) -> float:
        """Calculate size-based similarity."""
        area1 = (det1.x2 - det1.x1) * (det1.y2 - det1.y1)
        area2 = (det2.x2 - det2.x1) * (det2.y2 - det2.y1)
        
        if area1 == 0 or area2 == 0:
            return 0.0
        
        ratio = min(area1, area2) / max(area1, area2)
        return ratio
    
    def _combined_similarity(self, det1: BoundingBox, det2: BoundingBox) -> float:
        """Calculate combined position and size similarity."""
        pos_sim = self._position_similarity(det1, det2)
        size_sim = self._size_similarity(det1, det2)
        
        # Weighted combination
        return 0.6 * pos_sim + 0.4 * size_sim


class OverlapResolver:
    """Resolves overlapping bounding boxes."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    def resolve_overlaps(self, detections: List[BoundingBox]) -> Tuple[List[BoundingBox], Dict[str, int]]:
        """
        Resolve overlapping detections using Non-Maximum Suppression (NMS).
        
        Args:
            detections: List of bounding box detections
            
        Returns:
            Tuple of (filtered_detections, resolution_stats)
        """
        if len(detections) <= 1:
            return detections, {"overlaps_resolved": 0, "remaining": len(detections)}
        
        try:
            # Sort by confidence (highest first)
            sorted_detections = sorted(detections, key=lambda x: x.confidence, reverse=True)
            
            filtered = []
            overlaps_resolved = 0
            
            for i, detection in enumerate(sorted_detections):
                # Check if this detection overlaps with any already accepted detection
                should_keep = True
                
                for accepted in filtered:
                    iou = self._calculate_iou(detection, accepted)
                    
                    if iou > self.config["iou_threshold"]:
                        # Overlap detected - decide which to keep
                        if self._should_replace(detection, accepted):
                            # Replace the accepted detection
                            filtered.remove(accepted)
                            filtered.append(detection)
                        should_keep = False
                        overlaps_resolved += 1
                        break
                
                if should_keep:
                    filtered.append(detection)
            
            stats = {
                "overlaps_resolved": overlaps_resolved,
                "remaining": len(filtered)
            }
            
            logger.info(f"Overlap resolution: {overlaps_resolved} overlaps resolved")
            return filtered, stats
            
        except Exception as e:
            logger.error(f"Overlap resolution failed: {str(e)}")
            return detections, {"overlaps_resolved": 0, "remaining": len(detections)}
    
    def _calculate_iou(self, det1: BoundingBox, det2: BoundingBox) -> float:
        """Calculate Intersection over Union (IoU) between two bounding boxes."""
        # Calculate intersection
        x1 = max(det1.x1, det2.x1)
        y1 = max(det1.y1, det2.y1)
        x2 = min(det1.x2, det2.x2)
        y2 = min(det1.y2, det2.y2)
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        
        # Calculate union
        area1 = (det1.x2 - det1.x1) * (det1.y2 - det1.y1)
        area2 = (det2.x2 - det2.x1) * (det2.y2 - det2.y1)
        union = area1 + area2 - intersection
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _should_replace(self, new_det: BoundingBox, existing_det: BoundingBox) -> bool:
        """
        Decide if a new detection should replace an existing one.
        Uses weighted scoring based on confidence and size.
        """
        conf_weight = self.config["confidence_weight"]
        size_weight = self.config["size_weight"]
        
        # Calculate size scores
        new_area = (new_det.x2 - new_det.x1) * (new_det.y2 - new_det.y1)
        existing_area = (existing_det.x2 - existing_det.x1) * (existing_det.y2 - existing_det.y1)
        
        # Normalize areas (assuming max area of 1.0)
        new_size_score = min(new_area, 1.0)
        existing_size_score = min(existing_area, 1.0)
        
        # Calculate weighted scores
        new_score = (conf_weight * new_det.confidence + 
                    size_weight * new_size_score)
        existing_score = (conf_weight * existing_det.confidence + 
                         size_weight * existing_size_score)
        
        return new_score > existing_score

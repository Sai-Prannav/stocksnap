from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import random
import uuid

@dataclass
class BoundingBox:
    x1: float  # top-left x (normalized 0-1)
    y1: float  # top-left y (normalized 0-1)
    x2: float  # bottom-right x (normalized 0-1)
    y2: float  # bottom-right y (normalized 0-1)
    label: str
    confidence: float

@dataclass
class SegmentationMask:
    mask_type: str  # polygon, raster, base64
    mask_data: List[Dict[str, Any]]  # polygon points or other representation
    label: str
    confidence: Optional[float] = None

@dataclass
class AnalysisResult:
    count: int
    confidence: float
    bounding_boxes: List[BoundingBox]
    segmentation_masks: List[SegmentationMask]
    metadata: Dict[str, Any]

class ImageAnalyzer(ABC):
    """
    Abstract base class for image analysis services.
    This allows easy swapping between mock and real AI implementations.
    """
    
    @abstractmethod
    async def analyze_image(self, image_path: str) -> AnalysisResult:
        """
        Analyze an image and return detection results.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            AnalysisResult: Contains count, confidence, bounding boxes, and segmentation masks
        """
        pass

class MockImageAnalyzer(ImageAnalyzer):
    """
    Mock image analyzer that generates realistic dummy data.
    This simulates the structure of a real computer vision pipeline.
    """
    
    def __init__(self):
        # Common labels for inventory items
        self.labels = ["product", "shelf", "box", "item", "package", "container"]
        
    async def analyze_image(self, image_path: str) -> AnalysisResult:
        """
        Generate mock analysis results with realistic data.
        """
        # Generate random count between 1 and 30
        count = random.randint(1, 30)
        
        # Generate overall confidence (higher for better "detections")
        overall_confidence = random.uniform(0.75, 0.98)
        
        # Generate bounding boxes
        bounding_boxes = []
        for i in range(count):
            # Generate random but plausible bounding boxes
            x1 = random.uniform(0.05, 0.4)
            y1 = random.uniform(0.05, 0.6)
            width = random.uniform(0.1, 0.3)
            height = random.uniform(0.1, 0.3)
            
            x2 = min(x1 + width, 0.95)  # Ensure within bounds
            y2 = min(y1 + height, 0.95)
            
            label = random.choice(self.labels)
            confidence = random.uniform(0.8, 0.99)
            
            # Calculate area
            area = (x2 - x1) * (y2 - y1)
            
            bbox = BoundingBox(
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                label=label,
                confidence=confidence
            )
            bounding_boxes.append(bbox)
        
        # Generate segmentation masks (optional, for some detections)
        segmentation_masks = []
        mask_count = random.randint(0, min(count // 2, 5))  # Masks for subset of detections
        
        for i in range(mask_count):
            # Generate simple polygon mask (rectangle with some variation)
            base_bbox = random.choice(bounding_boxes)
            
            # Create polygon points around the bounding box with some variation
            polygon_points = [
                {"x": base_bbox.x1 + random.uniform(-0.02, 0.02), "y": base_bbox.y1 + random.uniform(-0.02, 0.02)},
                {"x": base_bbox.x2 + random.uniform(-0.02, 0.02), "y": base_bbox.y1 + random.uniform(-0.02, 0.02)},
                {"x": base_bbox.x2 + random.uniform(-0.02, 0.02), "y": base_bbox.y2 + random.uniform(-0.02, 0.02)},
                {"x": base_bbox.x1 + random.uniform(-0.02, 0.02), "y": base_bbox.y2 + random.uniform(-0.02, 0.02)}
            ]
            
            mask = SegmentationMask(
                mask_type="polygon",
                mask_data=[{"points": polygon_points}],
                label=base_bbox.label,
                confidence=base_bbox.confidence * random.uniform(0.9, 1.0)
            )
            segmentation_masks.append(mask)
        
        # Generate metadata
        metadata = {
            "analyzer_version": "mock-1.0.0",
            "processing_time_ms": random.randint(50, 500),
            "image_path": image_path,
            "detection_threshold": 0.5,
            "model_type": "mock_yolo",
            "analysis_id": str(uuid.uuid4())
        }
        
        return AnalysisResult(
            count=count,
            confidence=overall_confidence,
            bounding_boxes=bounding_boxes,
            segmentation_masks=segmentation_masks,
            metadata=metadata
        )

import pytest

# The 'advanced' pipeline is not wired into the app (the API uses YOLO11); its extra dependencies are optional.
pytest.importorskip("albumentations", reason="the unwired advanced pipeline's dependencies are not installed")
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

# Import the classes we need to test
from app.services.preprocessing_pipeline import PreprocessingPipeline, ShelfAngleDetector, LightingNormalizer, ImageEnhancer
from app.services.duplicate_resolver import DuplicateResolver, SpatialClusterer, FeatureMatcher, OverlapResolver
from app.services.advanced_image_analyzer import AdvancedImageAnalyzer
from app.services.image_analyzer import BoundingBox, AnalysisResult

class TestPreprocessingPipeline:
    """Test cases for the preprocessing pipeline."""
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        # Create a 640x480 RGB image with some patterns
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add some rectangular regions to simulate products
        cv2.rectangle(image, (100, 100), (200, 200), (255, 255, 255), -1)
        cv2.rectangle(image, (300, 150), (400, 250), (128, 128, 128), -1)
        cv2.rectangle(image, (500, 300), (600, 400), (64, 64, 64), -1)
        
        return image
    
    @pytest.fixture
    def temp_image_file(self, sample_image):
        """Create a temporary image file."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            # Convert RGB to BGR for OpenCV
            bgr_image = cv2.cvtColor(sample_image, cv2.COLOR_RGB2BGR)
            cv2.imwrite(tmp.name, bgr_image)
            yield tmp.name
        os.unlink(tmp.name)
    
    def test_preprocessing_pipeline_init(self):
        """Test preprocessing pipeline initialization."""
        pipeline = PreprocessingPipeline()
        assert pipeline.config is not None
        assert hasattr(pipeline, 'angle_detector')
        assert hasattr(pipeline, 'lighting_normalizer')
        assert hasattr(pipeline, 'enhancement_processor')
    
    def test_preprocessing_pipeline_with_config(self):
        """Test preprocessing pipeline with custom config."""
        config = {
            "angle_correction": {"enabled": False},
            "lighting_normalization": {"enabled": False},
            "enhancement": {"enabled": False}
        }
        pipeline = PreprocessingPipeline(config)
        assert pipeline.config["angle_correction"]["enabled"] is False
    
    @pytest.mark.asyncio
    async def test_process_image(self, temp_image_file):
        """Test complete image processing pipeline."""
        pipeline = PreprocessingPipeline()
        
        processed_images, metadata = pipeline.process_image(temp_image_file)
        
        assert len(processed_images) > 0
        assert "original_shape" in metadata
        assert "processing_steps" in metadata
        assert "quality_metrics" in metadata
        assert metadata["processing_success"] is True
    
    def test_quality_assessment(self, sample_image):
        """Test image quality assessment."""
        pipeline = PreprocessingPipeline()
        metrics = pipeline._assess_quality(sample_image)
        
        assert "blur_score" in metrics
        assert "brightness" in metrics
        assert "contrast" in metrics
        assert "sharpness" in metrics
        
        # Check that values are reasonable
        assert 0 <= metrics["brightness"] <= 1
        assert 0 <= metrics["contrast"] <= 1
        assert 0 <= metrics["sharpness"] <= 1

class TestShelfAngleDetector:
    """Test cases for shelf angle detection."""
    
    @pytest.fixture
    def angled_image(self):
        """Create an image with angled lines to simulate shelves."""
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add angled lines
        for i in range(5):
            y_start = 50 + i * 80
            y_end = y_start + 40
            cv2.line(image, (50, y_start), (590, y_end), (255, 255, 255), 3)
        
        return image
    
    def test_angle_detector_init(self):
        """Test angle detector initialization."""
        detector = ShelfAngleDetector()
        assert detector is not None
    
    def test_correct_shelf_angle_no_lines(self, sample_image):
        """Test angle correction with no clear lines."""
        detector = ShelfAngleDetector()
        config = {"angle_tolerance": 5.0, "min_line_length": 100, "max_line_gap": 10}
        
        corrected, angle_info = detector.correct_shelf_angle(sample_image, config)
        
        assert corrected.shape == sample_image.shape
        assert "angle" in angle_info
        assert "method" in angle_info
        assert angle_info["method"] == "hough_transform"
    
    def test_correct_shelf_angle_with_lines(self, angled_image):
        """Test angle correction with detectable lines."""
        detector = ShelfAngleDetector()
        config = {"angle_tolerance": 5.0, "min_line_length": 100, "max_line_gap": 10}
        
        corrected, angle_info = detector.correct_shelf_angle(angled_image, config)
        
        assert corrected.shape == angled_image.shape
        assert "angle" in angle_info
        assert "lines_detected" in angle_info

class TestDuplicateResolver:
    """Test cases for duplicate resolution system."""
    
    @pytest.fixture
    def sample_detections(self):
        """Create sample bounding box detections."""
        return [
            BoundingBox(0.1, 0.1, 0.3, 0.3, "product", 0.8),
            BoundingBox(0.12, 0.12, 0.32, 0.32, "product", 0.75),  # Overlapping
            BoundingBox(0.5, 0.5, 0.7, 0.7, "product", 0.9),      # Separate
            BoundingBox(0.8, 0.8, 0.95, 0.95, "product", 0.6),   # Low confidence
        ]
    
    def test_duplicate_resolver_init(self):
        """Test duplicate resolver initialization."""
        resolver = DuplicateResolver()
        assert resolver.config is not None
        assert hasattr(resolver, 'spatial_clusterer')
        assert hasattr(resolver, 'feature_matcher')
        assert hasattr(resolver, 'overlap_resolver')
    
    def test_resolve_duplicates_empty(self):
        """Test duplicate resolution with empty detections."""
        resolver = DuplicateResolver()
        filtered, metadata = resolver.resolve_duplicates([])
        
        assert len(filtered) == 0
        assert metadata["original_count"] == 0
        assert metadata["final_count"] == 0
    
    def test_resolve_duplicates(self, sample_detections):
        """Test duplicate resolution with sample detections."""
        resolver = DuplicateResolver()
        filtered, metadata = resolver.resolve_duplicates(sample_detections)
        
        assert len(filtered) <= len(sample_detections)
        assert metadata["original_count"] == len(sample_detections)
        assert metadata["final_count"] == len(filtered)
        assert "reduction_ratio" in metadata
        assert metadata["resolution_success"] is True
    
    def test_size_filtering(self, sample_detections):
        """Test size-based filtering."""
        resolver = DuplicateResolver()
        
        # Add very small and very large detections
        extended_detections = sample_detections + [
            BoundingBox(0.1, 0.1, 0.11, 0.11, "product", 0.9),  # Very small
            BoundingBox(0.0, 0.0, 0.9, 0.9, "product", 0.9),   # Very large
        ]
        
        filtered, stats = resolver._filter_by_size(extended_detections)
        
        assert len(filtered) < len(extended_detections)
        assert "filtered_out" in stats
        assert "remaining" in stats
    
    def test_confidence_filtering(self, sample_detections):
        """Test confidence-based filtering."""
        resolver = DuplicateResolver()
        
        filtered, stats = resolver._filter_by_confidence(sample_detections)
        
        # Should filter out low confidence detections
        assert all(d.confidence >= 0.3 for d in filtered)
        assert "filtered_out" in stats
        assert "remaining" in stats

class TestSpatialClusterer:
    """Test cases for spatial clustering."""
    
    @pytest.fixture
    def clustered_detections(self):
        """Create detections that should cluster together."""
        return [
            BoundingBox(0.1, 0.1, 0.2, 0.2, "product", 0.8),
            BoundingBox(0.12, 0.12, 0.22, 0.22, "product", 0.75),  # Close to first
            BoundingBox(0.5, 0.5, 0.6, 0.6, "product", 0.9),      # Separate cluster
            BoundingBox(0.52, 0.52, 0.62, 0.62, "product", 0.85), # Close to third
        ]
    
    def test_spatial_clusterer_init(self):
        """Test spatial clusterer initialization."""
        clusterer = SpatialClusterer({"eps": 0.1, "min_samples": 1, "metric": "euclidean"})
        assert clusterer.config is not None
    
    def test_cluster_detections(self, clustered_detections):
        """Test spatial clustering of detections."""
        clusterer = SpatialClusterer({"eps": 0.1, "min_samples": 1, "metric": "euclidean"})
        
        clusters = clusterer.cluster_detections(clustered_detections)
        
        assert len(clusters) > 0
        assert len(clusters) <= len(clustered_detections)
        
        # Check cluster structure
        for cluster in clusters:
            assert hasattr(cluster, 'detections')
            assert hasattr(cluster, 'centroid')
            assert hasattr(cluster, 'confidence')
            assert hasattr(cluster, 'label')
            assert hasattr(cluster, 'cluster_id')
            assert len(cluster.detections) >= 1

class TestFeatureMatcher:
    """Test cases for feature matching."""
    
    @pytest.fixture
    def sample_detections(self):
        """Create sample detections for feature matching."""
        return [
            BoundingBox(0.1, 0.1, 0.3, 0.3, "product", 0.8),
            BoundingBox(0.15, 0.15, 0.35, 0.35, "product", 0.75),  # Similar position
            BoundingBox(0.5, 0.5, 0.6, 0.6, "product", 0.9),      # Different position
        ]
    
    def test_feature_matcher_init(self):
        """Test feature matcher initialization."""
        matcher = FeatureMatcher({"similarity_threshold": 0.8, "feature_type": "combined"})
        assert matcher.config is not None
    
    def test_position_similarity(self, sample_detections):
        """Test position-based similarity calculation."""
        matcher = FeatureMatcher({"feature_type": "position"})
        
        similarity = matcher.calculate_similarity(sample_detections[0], sample_detections[1])
        assert 0 <= similarity <= 1
        
        # Similar detections should have higher similarity
        similarity_far = matcher.calculate_similarity(sample_detections[0], sample_detections[2])
        assert similarity > similarity_far
    
    def test_size_similarity(self, sample_detections):
        """Test size-based similarity calculation."""
        matcher = FeatureMatcher({"feature_type": "size"})
        
        similarity = matcher.calculate_similarity(sample_detections[0], sample_detections[1])
        assert 0 <= similarity <= 1
    
    def test_combined_similarity(self, sample_detections):
        """Test combined similarity calculation."""
        matcher = FeatureMatcher({"feature_type": "combined"})
        
        similarity = matcher.calculate_similarity(sample_detections[0], sample_detections[1])
        assert 0 <= similarity <= 1

class TestOverlapResolver:
    """Test cases for overlap resolution."""
    
    @pytest.fixture
    def overlapping_detections(self):
        """Create overlapping detections."""
        return [
            BoundingBox(0.1, 0.1, 0.3, 0.3, "product", 0.8),
            BoundingBox(0.15, 0.15, 0.35, 0.35, "product", 0.75),  # Overlapping
            BoundingBox(0.5, 0.5, 0.7, 0.7, "product", 0.9),      # Non-overlapping
        ]
    
    def test_overlap_resolver_init(self):
        """Test overlap resolver initialization."""
        resolver = OverlapResolver({"iou_threshold": 0.5, "confidence_weight": 0.7, "size_weight": 0.3})
        assert resolver.config is not None
    
    def test_calculate_iou(self, overlapping_detections):
        """Test IoU calculation."""
        resolver = OverlapResolver({})
        
        # Test overlapping detections
        iou = resolver._calculate_iou(overlapping_detections[0], overlapping_detections[1])
        assert iou > 0
        
        # Test non-overlapping detections
        iou = resolver._calculate_iou(overlapping_detections[0], overlapping_detections[2])
        assert iou == 0
    
    def test_resolve_overlaps(self, overlapping_detections):
        """Test overlap resolution."""
        resolver = OverlapResolver({"iou_threshold": 0.5, "confidence_weight": 0.7, "size_weight": 0.3})
        
        filtered, stats = resolver.resolve_overlaps(overlapping_detections)
        
        assert len(filtered) <= len(overlapping_detections)
        assert "overlaps_resolved" in stats
        assert "remaining" in stats

class TestAdvancedImageAnalyzer:
    """Test cases for the advanced image analyzer."""
    
    @pytest.fixture
    def temp_image_file(self):
        """Create a temporary image file."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            # Create a simple test image
            image = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.rectangle(image, (100, 100), (200, 200), (255, 255, 255), -1)
            
            bgr_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            cv2.imwrite(tmp.name, bgr_image)
            yield tmp.name
        os.unlink(tmp.name)
    
    def test_advanced_analyzer_init(self):
        """Test advanced analyzer initialization."""
        analyzer = AdvancedImageAnalyzer()
        assert analyzer.config is not None
        assert hasattr(analyzer, 'model_manager')
        assert hasattr(analyzer, 'duplicate_resolver')
        assert hasattr(analyzer, 'preprocessing_pipeline')
    
    @patch('app.services.advanced_image_analyzer.ModelManager')
    def test_analyze_image_with_mock(self, mock_model_manager, temp_image_file):
        """Test image analysis with mocked model manager."""
        # Mock the model manager
        mock_manager_instance = Mock()
        mock_manager_instance.load_yolo_model.return_value = True
        mock_manager_instance.preprocess_image.return_value = (
            [np.zeros((480, 640, 3), dtype=np.uint8)],
            {"preprocessing_method": "basic"}
        )
        mock_manager_instance.run_yolo_inference.return_value = {
            "detections": [
                {"x1": 0.1, "y1": 0.1, "x2": 0.3, "y2": 0.3, "confidence": 0.8, "label": "product", "class_id": 0}
            ],
            "inference_time": 100
        }
        mock_manager_instance.run_sam_inference.return_value = {"masks": []}
        mock_manager_instance.model_configs = {
            "yolo": {"confidence_threshold": 0.5},
            "sam": {"enabled": False}
        }
        mock_manager_instance.get_model_info.return_value = {"yolo_loaded": True}
        mock_model_manager.return_value = mock_manager_instance
        
        analyzer = AdvancedImageAnalyzer()
        
        # Test the analysis
        import asyncio
        result = asyncio.run(analyzer.analyze_image(temp_image_file))
        
        assert isinstance(result, AnalysisResult)
        assert result.count >= 0
        assert 0 <= result.confidence <= 1
        assert isinstance(result.bounding_boxes, list)
        assert isinstance(result.segmentation_masks, list)
        assert isinstance(result.metadata, dict)
    
    def test_quality_assurance(self):
        """Test quality assurance functionality."""
        analyzer = AdvancedImageAnalyzer()
        
        detections = [
            BoundingBox(0.1, 0.1, 0.3, 0.3, "product", 0.8),
            BoundingBox(0.5, 0.5, 0.7, 0.7, "product", 0.2),  # Low confidence
            BoundingBox(0.8, 0.8, 0.9, 0.9, "product", 0.9),
        ]
        
        filtered, qa_metadata = analyzer._apply_quality_assurance(detections)
        
        assert len(filtered) <= len(detections)
        assert "original_count" in qa_metadata
        assert "final_count" in qa_metadata
        assert "quality_metrics" in qa_metadata
        
        # Should filter out low confidence detections
        assert all(d.confidence >= 0.3 for d in filtered)
    
    def test_pattern_detection(self):
        """Test pattern detection in intelligent counting."""
        analyzer = AdvancedImageAnalyzer()
        
        # Create detections in a row pattern
        row_detections = [
            BoundingBox(0.1, 0.4, 0.2, 0.5, "product", 0.8),
            BoundingBox(0.3, 0.41, 0.4, 0.51, "product", 0.8),
            BoundingBox(0.5, 0.39, 0.6, 0.49, "product", 0.8),
        ]
        
        result = analyzer._detect_patterns(row_detections)
        assert "row_pattern" in result or "no_clear_pattern" in result
    
    def test_get_status(self):
        """Test status retrieval."""
        analyzer = AdvancedImageAnalyzer()
        status = analyzer.get_status()
        
        assert "analyzer_type" in status
        assert "version" in status
        assert "features" in status
        assert status["analyzer_type"] == "advanced"
        assert status["version"] == "2.0.0"

class TestIntegration:
    """Integration tests for the complete system."""
    
    @pytest.fixture
    def temp_image_file(self):
        """Create a temporary image file for integration testing."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            # Create a more complex test image
            image = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Add multiple rectangular regions
            for i in range(3):
                for j in range(2):
                    x = 100 + j * 200
                    y = 100 + i * 120
                    cv2.rectangle(image, (x, y), (x + 80, y + 80), (255, 255, 255), -1)
            
            bgr_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            cv2.imwrite(tmp.name, bgr_image)
            yield tmp.name
        os.unlink(tmp.name)
    
    @patch('app.services.advanced_image_analyzer.ModelManager')
    def test_end_to_end_processing(self, mock_model_manager, temp_image_file):
        """Test end-to-end processing pipeline."""
        # Mock complete model manager behavior
        mock_manager_instance = Mock()
        mock_manager_instance.load_yolo_model.return_value = True
        mock_manager_instance.preprocess_image.return_value = (
            [np.zeros((480, 640, 3), dtype=np.uint8)],
            {"preprocessing_method": "advanced", "processing_steps": ["angle_correction", "enhancement"]}
        )
        mock_manager_instance.run_yolo_inference.return_value = {
            "detections": [
                {"x1": 0.1, "y1": 0.1, "x2": 0.3, "y2": 0.3, "confidence": 0.8, "label": "product", "class_id": 0},
                {"x1": 0.15, "y1": 0.15, "x2": 0.35, "y2": 0.35, "confidence": 0.75, "label": "product", "class_id": 0},  # Duplicate
                {"x1": 0.5, "y1": 0.5, "x2": 0.7, "y2": 0.7, "confidence": 0.9, "label": "product", "class_id": 0},
            ],
            "inference_time": 150,
            "num_scales": 1,
            "total_detections_before_merge": 3,
            "final_detections": 3
        }
        mock_manager_instance.run_sam_inference.return_value = {"masks": [], "status": "disabled"}
        mock_manager_instance.model_configs = {
            "yolo": {"confidence_threshold": 0.5},
            "sam": {"enabled": False},
            "general": {"enable_advanced_preprocessing": True}
        }
        mock_manager_instance.get_model_info.return_value = {
            "yolo_loaded": True,
            "sam_loaded": False,
            "advanced_preprocessing_enabled": True
        }
        mock_model_manager.return_value = mock_manager_instance
        
        analyzer = AdvancedImageAnalyzer()
        
        # Run complete analysis
        import asyncio
        result = asyncio.run(analyzer.analyze_image(temp_image_file))
        
        # Verify results
        assert isinstance(result, AnalysisResult)
        assert result.count > 0
        assert result.confidence > 0
        
        # Check metadata contains processing steps
        assert "processing_metadata" in result.metadata
        processing_metadata = result.metadata["processing_metadata"]
        assert "processing_steps" in processing_metadata
        assert len(processing_metadata["processing_steps"]) > 0
        
        # Verify duplicate resolution occurred
        assert "duplicate_resolution_metadata" in processing_metadata
        dup_meta = processing_metadata["duplicate_resolution_metadata"]
        assert dup_meta["original_count"] >= dup_meta["final_count"]
        
        # Verify quality assurance was applied
        assert "quality_assurance_metadata" in processing_metadata

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

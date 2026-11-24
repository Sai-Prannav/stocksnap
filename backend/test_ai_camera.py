#!/usr/bin/env python3
"""
Standalone AI Camera Test Script
Isolates and tests YOLO detection pipeline separately from the main system
"""

import cv2
import numpy as np
from ultralytics import YOLO
import torch
import logging
from pathlib import Path
import json
import time
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StandaloneAICamera:
    """Standalone AI camera for testing YOLO detection pipeline"""
    
    def __init__(self, model_name: str = "yolov8n.pt"):
        """Initialize the standalone AI camera"""
        self.model_name = model_name
        self.model = None
        self.device = self._get_device()
        self.load_model()
    
    def _get_device(self) -> str:
        """Determine the best available device"""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    
    def load_model(self) -> bool:
        """Load YOLO model"""
        try:
            logger.info(f"Loading YOLO model: {self.model_name}")
            self.model = YOLO(self.model_name)
            logger.info(f"Model loaded successfully on device: {self.device}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return False
    
    def detect_objects(self, image_path: str, confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """
        Detect objects in image with detailed output
        
        Args:
            image_path: Path to the image file
            confidence_threshold: Confidence threshold for detections
            
        Returns:
            Dictionary containing detection results and metadata
        """
        try:
            # Load image
            logger.info(f"Loading image: {image_path}")
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            original_height, original_width = image.shape[:2]
            logger.info(f"Image size: {original_width}x{original_height}")
            
            # Run inference
            start_time = time.time()
            results = self.model(
                image,
                conf=confidence_threshold,
                iou=0.45,
                max_det=100,
                device=self.device,
                verbose=True  # Enable verbose output to see what YOLO detects
            )
            inference_time = time.time() - start_time
            
            logger.info(f"Inference completed in {inference_time:.3f} seconds")
            
            # Process results
            detections = []
            for result in results:
                logger.info(f"Raw result type: {type(result)}")
                logger.info(f"Result boxes: {result.boxes}")
                logger.info(f"Result names: {result.names}")
                
                boxes = result.boxes
                if boxes is not None:
                    logger.info(f"Number of boxes detected: {len(boxes)}")
                    
                    for i, box in enumerate(boxes):
                        # Get raw coordinates
                        xyxy = box.xyxy[0].cpu().numpy()
                        conf = float(box.conf[0].cpu().numpy())
                        cls = int(box.cls[0].cpu().numpy())
                        
                        # Get class name
                        class_name = result.names[cls]
                        
                        # Calculate normalized coordinates
                        x1_norm = float(xyxy[0] / original_width)
                        y1_norm = float(xyxy[1] / original_height)
                        x2_norm = float(xyxy[2] / original_width)
                        y2_norm = float(xyxy[3] / original_height)
                        
                        # Calculate area
                        area_norm = (x2_norm - x1_norm) * (y2_norm - y1_norm)
                        
                        detection = {
                            "detection_id": i,
                            "class_id": cls,
                            "class_name": class_name,
                            "confidence": conf,
                            "coordinates": {
                                "pixel": {
                                    "x1": float(xyxy[0]),
                                    "y1": float(xyxy[1]),
                                    "x2": float(xyxy[2]),
                                    "y2": float(xyxy[3])
                                },
                                "normalized": {
                                    "x1": x1_norm,
                                    "y1": y1_norm,
                                    "x2": x2_norm,
                                    "y2": y2_norm
                                }
                            },
                            "area_normalized": area_norm,
                            "width": x2_norm - x1_norm,
                            "height": y2_norm - y1_norm
                        }
                        
                        detections.append(detection)
                        
                        logger.info(f"Detection {i}: {class_name} (conf={conf:.3f}) "
                                  f"@ ({x1_norm:.3f},{y1_norm:.3f})-({x2_norm:.3f},{y2_norm:.3f})")
                else:
                    logger.warning("No boxes detected in result")
            
            # Calculate summary statistics
            summary = {
                "total_detections": len(detections),
                "unique_classes": list(set(d["class_name"] for d in detections)),
                "class_distribution": {},
                "avg_confidence": 0.0,
                "inference_time": inference_time
            }
            
            if detections:
                # Class distribution
                for detection in detections:
                    class_name = detection["class_name"]
                    summary["class_distribution"][class_name] = summary["class_distribution"].get(class_name, 0) + 1
                
                # Average confidence
                summary["avg_confidence"] = sum(d["confidence"] for d in detections) / len(detections)
            
            return {
                "success": True,
                "image_path": image_path,
                "image_size": {"width": original_width, "height": original_height},
                "model_info": {
                    "name": self.model_name,
                    "device": self.device,
                    "confidence_threshold": confidence_threshold
                },
                "detections": detections,
                "summary": summary,
                "raw_results_info": {
                    "num_results": len(results),
                    "has_boxes": results[0].boxes is not None if results else False
                }
            }
            
        except Exception as e:
            logger.error(f"Detection failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "image_path": image_path
            }
    
    def test_different_thresholds(self, image_path: str, thresholds: List[float] = None) -> Dict[str, Any]:
        """Test detection with different confidence thresholds"""
        if thresholds is None:
            thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        
        results = {}
        
        for threshold in thresholds:
            logger.info(f"\n=== Testing with confidence threshold: {threshold} ===")
            result = self.detect_objects(image_path, threshold)
            results[f"threshold_{threshold}"] = result
        
        return results
    
    def test_different_models(self, image_path: str, models: List[str] = None) -> Dict[str, Any]:
        """Test detection with different YOLO models"""
        if models is None:
            models = ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"]
        
        results = {}
        
        for model_name in models:
            logger.info(f"\n=== Testing with model: {model_name} ===")
            
            # Temporarily load different model
            original_model = self.model
            original_model_name = self.model_name
            
            if self.load_new_model(model_name):
                result = self.detect_objects(image_path, 0.3)
                results[model_name] = result
            else:
                results[model_name] = {"success": False, "error": f"Failed to load {model_name}"}
            
            # Restore original model
            self.model = original_model
            self.model_name = original_model_name
        
        return results
    
    def load_new_model(self, model_name: str) -> bool:
        """Load a new model"""
        try:
            self.model_name = model_name
            return self.load_model()
        except Exception as e:
            logger.error(f"Failed to load new model {model_name}: {str(e)}")
            return False
    
    def save_results(self, results: Dict[str, Any], output_path: str):
        """Save results to JSON file"""
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results saved to: {output_path}")
        except Exception as e:
            logger.error(f"Failed to save results: {str(e)}")

def main():
    """Main function for testing"""
    # Initialize camera
    camera = StandaloneAICamera()
    
    if not camera.model:
        logger.error("Failed to initialize camera")
        return
    
    # Test image path (you can modify this)
    test_images = [
        "uploads/images/afff1f39-cb28-44cb-b296-635bb2f0a138.jpg",  # Recent upload
        # Add more test images as needed
    ]
    
    for image_path in test_images:
        if not Path(image_path).exists():
            logger.warning(f"Image not found: {image_path}")
            continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"TESTING IMAGE: {image_path}")
        logger.info(f"{'='*60}")
        
        # Test 1: Basic detection with default threshold
        logger.info(f"\n--- BASIC DETECTION TEST ---")
        result = camera.detect_objects(image_path, 0.3)
        
        if result["success"]:
            logger.info(f"✅ Detection successful!")
            logger.info(f"📊 Total detections: {result['summary']['total_detections']}")
            logger.info(f"🏷️  Classes found: {result['summary']['unique_classes']}")
            logger.info(f"📈 Average confidence: {result['summary']['avg_confidence']:.3f}")
            logger.info(f"⏱️  Inference time: {result['summary']['inference_time']:.3f}s")
            
            # Print detailed detections
            for detection in result["detections"]:
                logger.info(f"  📦 {detection['class_name']}: {detection['confidence']:.3f} "
                          f"({detection['coordinates']['normalized']['x1']:.3f},"
                          f"{detection['coordinates']['normalized']['y1']:.3f})-"
                          f"({detection['coordinates']['normalized']['x2']:.3f},"
                          f"{detection['coordinates']['normalized']['y2']:.3f})")
        else:
            logger.error(f"❌ Detection failed: {result['error']}")
        
        # Test 2: Different confidence thresholds
        logger.info(f"\n--- CONFIDENCE THRESHOLD TEST ---")
        threshold_results = camera.test_different_thresholds(image_path, [0.1, 0.3, 0.5, 0.7])
        
        for threshold_key, threshold_result in threshold_results.items():
            if threshold_result["success"]:
                count = threshold_result["summary"]["total_detections"]
                avg_conf = threshold_result["summary"]["avg_confidence"]
                logger.info(f"  {threshold_key}: {count} detections (avg_conf: {avg_conf:.3f})")
            else:
                logger.error(f"  {threshold_key}: FAILED - {threshold_result['error']}")
        
        # Save results
        output_file = f"test_results_{Path(image_path).stem}.json"
        camera.save_results({
            "basic_test": result,
            "threshold_tests": threshold_results
        }, output_file)
        
        logger.info(f"\n--- TEST COMPLETE FOR {image_path} ---\n")

if __name__ == "__main__":
    main()

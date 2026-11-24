import logging
import os
import time
from pathlib import Path
from typing import List, Dict, Any
from ultralytics import YOLO
from .image_analyzer import ImageAnalyzer, BoundingBox, AnalysisResult

logger = logging.getLogger(__name__)

class RealImageAnalyzer(ImageAnalyzer):
    """YOLO11 object detector. Weights are downloaded automatically by ultralytics on first run."""

    MODEL_NAME = "yolo11n.pt"

    def __init__(self, model_name: str = MODEL_NAME):
        # Weights live in backend/weights/ (git-ignored). If the file is missing,
        # ultralytics downloads it from the official release assets.
        weights_dir = Path(__file__).resolve().parents[2] / "weights"
        weights_dir.mkdir(exist_ok=True)
        # Raises on failure so the caller can fall back to the mock analyzer.
        self.model = YOLO(str(weights_dir / model_name))
        logger.info("Loaded YOLO model: %s", model_name)

    async def analyze_image(self, image_path: str) -> AnalysisResult:
        if self.model is None:
            raise ValueError("AI model not initialized.")

        start_time = time.time()
        
        # 1. Run Inference with DEMO UPGRADES
        # imgsz=1280 makes it see small items much better
        # augment=True does multiple passes for higher confidence
        results = self.model.predict(
            source=image_path, 
            conf=0.10,      # Lower floor to catch more, we filter in the loop
            imgsz=1280,
            iou=0.3,     
            augment=True,
            agnostic_nms=True,  # Class-agnostic NMS to catch all items regardless of class   
            save=False
        )
        
        result = results[0]
        bounding_boxes = []
        
        # 2. Extract Detections
        for box in result.boxes:
            conf_value = float(box.conf[0])
            
            # Filter: Only keep detections above 25% for the final count
            if conf_value < 0.25:
                continue

            coords = box.xyxyn[0].tolist() 
            
            bbox = BoundingBox(
                x1=coords[0],
                y1=coords[1],
                x2=coords[2],
                y2=coords[3],
                label=result.names[int(box.cls)],
                confidence=conf_value
            )
            bounding_boxes.append(bbox)

        # 3. Calculate Summary
        total_count = len(bounding_boxes)
        avg_confidence = (
            sum(b.confidence for b in bounding_boxes) / total_count 
            if total_count > 0 else 0.0
        )

        processing_time = (time.time() - start_time) * 1000 

        return AnalysisResult(
            count=total_count,
            confidence=avg_confidence,
            bounding_boxes=bounding_boxes,
            segmentation_masks=[],
            metadata={
                "processing_time_ms": processing_time,
                "model": "yolov11n",
                "imgsz": 1280,
                "augment": True
            }
        )
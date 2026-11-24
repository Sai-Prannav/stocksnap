
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from ultralytics import YOLO
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Manages loading, caching, and configuration of AI models.
    Handles both YOLO and SAM models with proper error handling.
    """
    
    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.yolo_model = None
        self.sam_model = None
        self.model_configs = self._load_configurations()
        
        # Create model directories if they don't exist
        self.model_dir.mkdir(exist_ok=True)
        (self.model_dir / "yolo").mkdir(exist_ok=True)
        (self.model_dir / "sam").mkdir(exist_ok=True)
        (self.model_dir / "custom").mkdir(exist_ok=True)
    
    def _load_configurations(self) -> Dict[str, Any]:
        """Load model configurations from environment variables and defaults."""
        return {
            "yolo": {
                "model_name": os.getenv("YOLO_MODEL_NAME", "yolov8n.pt"),
                "confidence_threshold": float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", 0.5)),
                "iou_threshold": float(os.getenv("YOLO_IOU_THRESHOLD", 0.45)),
                "max_detections": int(os.getenv("YOLO_MAX_DETECTIONS", 100)),
                "device": os.getenv("YOLO_DEVICE", "cpu")  # "cpu", "cuda", "mps"
            },
            "sam": {
                "model_name": os.getenv("SAM_MODEL_NAME", "sam_vit_h_4b8939.pth"),
                "confidence_threshold": float(os.getenv("SAM_CONFIDENCE_THRESHOLD", 0.7)),
                "device": os.getenv("SAM_DEVICE", "cpu")
            },
            "general": {
                "max_image_size": int(os.getenv("MAX_IMAGE_SIZE", 1920)),
                "enable_gpu": os.getenv("ENABLE_GPU", "false").lower() == "true",
                "batch_size": int(os.getenv("BATCH_SIZE", 1))
            }
        }
    
    def load_yolo_model(self) -> bool:
        """
        Load YOLO model with error handling and fallback.
        Returns True if successful, False otherwise.
        """
        try:
            if self.yolo_model is not None:
                return True
            
            config = self.model_configs["yolo"]
            model_path = self.model_dir / "yolo" / config["model_name"]
            
            # If model doesn't exist locally, download it
            if not model_path.exists():
                logger.info(f"Downloading YOLO model: {config['model_name']}")
                self.yolo_model = YOLO(config["model_name"])
                # Save the model locally for future use
                model_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                logger.info(f"Loading YOLO model from: {model_path}")
                self.yolo_model = YOLO(str(model_path))
            
            # Configure model
            device = self._get_device()
            if device != "cpu":
                self.yolo_model.to(device)
            
            logger.info("YOLO model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {str(e)}")
            self.yolo_model = None
            return False
    
    def load_sam_model(self) -> bool:
        """
        Load SAM model with error handling.
        Returns True if successful, False otherwise.
        """
        try:
            if self.sam_model is not None:
                return True
            
            # SAM implementation would go here
            # For now, we'll implement a placeholder
            logger.info("SAM model not yet implemented")
            return False
            
        except Exception as e:
            logger.error(f"Failed to load SAM model: {str(e)}")
            self.sam_model = None
            return False
    
    def _get_device(self) -> str:
        """Determine the best available device for inference."""
        if not self.model_configs["general"]["enable_gpu"]:
            return "cpu"
        
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        
        return "cpu"
    
    def preprocess_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Preprocess image for model inference.
        Handles validation, resizing, and format conversion.
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return None
            
            # Convert BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Resize if too large
            max_size = self.model_configs["general"]["max_image_size"]
            height, width = image.shape[:2]
            
            if max(height, width) > max_size:
                scale = max_size / max(height, width)
                new_height = int(height * scale)
                new_width = int(width * scale)
                image = cv2.resize(image, (new_width, new_height))
            
            return image
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            return None
    
    def run_yolo_inference(self, image: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Run YOLO inference on preprocessed image.
        Returns detection results or None if failed.
        """
        try:
            if self.yolo_model is None:
                if not self.load_yolo_model():
                    return None
            
            config = self.model_configs["yolo"]
            device = self._get_device()
            
            # Run inference
            results = self.yolo_model(
                image,
                conf=config["confidence_threshold"],
                iou=config["iou_threshold"],
                max_det=config["max_detections"],
                device=device,
                verbose=False
            )
            
            # Process results
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get normalized coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Normalize coordinates to 0-1 range
                        height, width = image.shape[:2]
                        x1_norm = float(x1 / width)
                        y1_norm = float(y1 / height)
                        x2_norm = float(x2 / width)
                        y2_norm = float(y2 / height)
                        
                        detections.append({
                            "x1": x1_norm,
                            "y1": y1_norm,
                            "x2": x2_norm,
                            "y2": y2_norm,
                            "confidence": confidence,
                            "class_id": class_id,
                            "label": self._get_class_label(class_id)
                        })
            
            return {
                "detections": detections,
                "model_type": "yolov8",
                "inference_time": getattr(results[0].speed, 'inference', 0) if hasattr(results[0], 'speed') else 0
            }
            
        except Exception as e:
            logger.error(f"YOLO inference failed: {str(e)}")
            return None
    
    def run_sam_inference(self, image: np.ndarray, boxes: list) -> Optional[Dict[str, Any]]:
        """
        Run SAM inference for segmentation masks.
        Returns segmentation results or None if failed.
        """
        try:
            # SAM implementation would go here
            # For now, return empty results
            return {
                "masks": [],
                "model_type": "sam",
                "inference_time": 0
            }
            
        except Exception as e:
            logger.error(f"SAM inference failed: {str(e)}")
            return None
    
    def _get_class_label(self, class_id: int) -> str:
        """
        Map class ID to human-readable label.
        This can be customized based on the model's classes.
        """
        # Default YOLOv8 classes - customize for inventory items
        class_names = [
            "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
            "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
            "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
            "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
            "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
            "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
            "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
            "chair", "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop",
            "mouse", "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
            "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
        ]
        
        # Map common objects to inventory-related labels
        inventory_mapping = {
            0: "product",  # person -> product
            39: "bottle",  # bottle
            41: "cup",     # wine glass -> cup
            42: "product", # cup -> product
            44: "product", # bowl -> product
            46: "package", # banana -> package
            47: "product", # apple -> product
            48: "package", # sandwich -> package
            49: "product", # orange -> product
            50: "product", # broccoli -> product
            51: "product", # carrot -> product
            52: "package", # hot dog -> package
            53: "package", # pizza -> package
            54: "product", # donut -> product
            55: "product", # cake -> product
            56: "shelf",   # chair -> shelf
            57: "shelf",   # couch -> shelf
            58: "product", # potted plant -> product
            59: "product", # bed -> product
            60: "shelf",   # dining table -> shelf
            72: "product", # book -> product
            73: "product", # clock -> product
            74: "product", # vase -> product
            75: "package", # scissors -> package
        }
        
        if class_id < len(class_names):
            return inventory_mapping.get(class_id, class_names[class_id])
        else:
            return "object"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models and configuration."""
        return {
            "yolo_loaded": self.yolo_model is not None,
            "sam_loaded": self.sam_model is not None,
            "device": self._get_device(),
            "configs": self.model_configs,
            "model_dir": str(self.model_dir)
        }
    
    def unload_models(self):
        """Unload models to free memory."""
        self.yolo_model = None
        self.sam_model = None
        logger.info("Models unloaded from memory")

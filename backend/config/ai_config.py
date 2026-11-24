import os
from pathlib import Path
from typing import Dict, Any, Optional

class AIConfig:
    """
    Configuration management for AI models and inference parameters.
    Loads configuration from environment variables and provides defaults.
    """
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            # Model paths and settings
            "model_dir": os.getenv("AI_MODEL_DIR", "models"),
            "yolo_model_name": os.getenv("YOLO_MODEL_NAME", "yolov8n.pt"),
            "sam_model_name": os.getenv("SAM_MODEL_NAME", "sam_vit_h_4b8939.pth"),
            
            # Inference settings
            "enable_gpu": os.getenv("ENABLE_GPU", "false").lower() == "true",
            "yolo_device": os.getenv("YOLO_DEVICE", "cpu"),
            "sam_device": os.getenv("SAM_DEVICE", "cpu"),
            
            # Detection thresholds
            "yolo_confidence_threshold": float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", 0.5)),
            "yolo_iou_threshold": float(os.getenv("YOLO_IOU_THRESHOLD", 0.45)),
            "yolo_max_detections": int(os.getenv("YOLO_MAX_DETECTIONS", 100)),
            "sam_confidence_threshold": float(os.getenv("SAM_CONFIDENCE_THRESHOLD", 0.7)),
            
            # Image processing
            "max_image_size": int(os.getenv("MAX_IMAGE_SIZE", 1920)),
            "batch_size": int(os.getenv("BATCH_SIZE", 1)),
            "image_formats": os.getenv("SUPPORTED_IMAGE_FORMATS", "jpg,jpeg,png,bmp,tiff").split(","),
            
            # Performance settings
            "enable_model_caching": os.getenv("ENABLE_MODEL_CACHING", "true").lower() == "true",
            "max_cache_size_mb": int(os.getenv("MAX_CACHE_SIZE_MB", 1024)),
            "auto_download_models": os.getenv("AUTO_DOWNLOAD_MODELS", "true").lower() == "true",
            
            # Fallback settings
            "enable_fallback": os.getenv("ENABLE_FALLBACK", "true").lower() == "true",
            "fallback_timeout_ms": int(os.getenv("FALLBACK_TIMEOUT_MS", 5000)),
            
            # Logging and monitoring
            "enable_performance_logging": os.getenv("ENABLE_PERFORMANCE_LOGGING", "true").lower() == "true",
            "log_inference_times": os.getenv("LOG_INFERENCE_TIMES", "true").lower() == "true",
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value
    
    def get_model_dir(self) -> Path:
        """Get the model directory as a Path object."""
        return Path(self.config["model_dir"])
    
    def get_yolo_config(self) -> Dict[str, Any]:
        """Get YOLO-specific configuration."""
        return {
            "model_name": self.config["yolo_model_name"],
            "confidence_threshold": self.config["yolo_confidence_threshold"],
            "iou_threshold": self.config["yolo_iou_threshold"],
            "max_detections": self.config["yolo_max_detections"],
            "device": self.config["yolo_device"]
        }
    
    def get_sam_config(self) -> Dict[str, Any]:
        """Get SAM-specific configuration."""
        return {
            "model_name": self.config["sam_model_name"],
            "confidence_threshold": self.config["sam_confidence_threshold"],
            "device": self.config["sam_device"]
        }
    
    def get_image_config(self) -> Dict[str, Any]:
        """Get image processing configuration."""
        return {
            "max_size": self.config["max_image_size"],
            "batch_size": self.config["batch_size"],
            "supported_formats": self.config["image_formats"]
        }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance-related configuration."""
        return {
            "enable_gpu": self.config["enable_gpu"],
            "enable_model_caching": self.config["enable_model_caching"],
            "max_cache_size_mb": self.config["max_cache_size_mb"],
            "auto_download_models": self.config["auto_download_models"]
        }
    
    def update_from_dict(self, updates: Dict[str, Any]):
        """Update configuration from a dictionary."""
        self.config.update(updates)
    
    def save_to_env_file(self, file_path: str = ".env.ai"):
        """Save current configuration to an environment file."""
        env_content = []
        for key, value in self.config.items():
            if isinstance(value, bool):
                value = str(value).lower()
            env_content.append(f"{key.upper()}={value}")
        
        with open(file_path, 'w') as f:
            f.write('\n'.join(env_content))
    
    def validate_config(self) -> Dict[str, str]:
        """Validate configuration and return any issues."""
        issues = []
        
        # Check model directory
        model_dir = self.get_model_dir()
        if not model_dir.exists():
            try:
                model_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create model directory {model_dir}: {e}")
        
        # Check thresholds
        if not 0 <= self.config["yolo_confidence_threshold"] <= 1:
            issues.append("YOLO confidence threshold must be between 0 and 1")
        
        if not 0 <= self.config["yolo_iou_threshold"] <= 1:
            issues.append("YOLO IoU threshold must be between 0 and 1")
        
        if not 0 <= self.config["sam_confidence_threshold"] <= 1:
            issues.append("SAM confidence threshold must be between 0 and 1")
        
        # Check image size
        if self.config["max_image_size"] <= 0:
            issues.append("Max image size must be positive")
        
        # Check batch size
        if self.config["batch_size"] <= 0:
            issues.append("Batch size must be positive")
        
        return issues
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the configuration."""
        summary = []
        summary.append("AI Configuration Summary:")
        summary.append(f"  Model Directory: {self.config['model_dir']}")
        summary.append(f"  YOLO Model: {self.config['yolo_model_name']}")
        summary.append(f"  GPU Enabled: {self.config['enable_gpu']}")
        summary.append(f"  Max Image Size: {self.config['max_image_size']}px")
        summary.append(f"  YOLO Confidence Threshold: {self.config['yolo_confidence_threshold']}")
        summary.append(f"  Fallback Enabled: {self.config['enable_fallback']}")
        
        return '\n'.join(summary)

# Global configuration instance
ai_config = AIConfig()

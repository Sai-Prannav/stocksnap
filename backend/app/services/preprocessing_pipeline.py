import logging
import cv2
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
from skimage import exposure, restoration, transform, filters
from skimage.feature import canny
from scipy import ndimage
import albumentations as A
from PIL import Image, ImageEnhance
import exifread

logger = logging.getLogger(__name__)

class PreprocessingPipeline:
    """
    Advanced preprocessing pipeline for inventory image analysis.
    Handles angle correction, lighting normalization, and enhancement.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.angle_detector = ShelfAngleDetector()
        self.lighting_normalizer = LightingNormalizer()
        self.enhancement_processor = ImageEnhancer()
        
    def _default_config(self) -> Dict[str, Any]:
        return {
            "angle_correction": {
                "enabled": True,
                "method": "hough_transform",
                "angle_tolerance": 5.0,
                "min_line_length": 100,
                "max_line_gap": 10
            },
            "lighting_normalization": {
                "enabled": True,
                "method": "clahe",
                "clip_limit": 2.0,
                "tile_grid_size": (8, 8)
            },
            "enhancement": {
                "enabled": True,
                "sharpening": True,
                "noise_reduction": True,
                "contrast_enhancement": True
            },
            "multi_scale": {
                "enabled": True,
                "scales": [0.8, 1.0, 1.2],
                "merge_method": "weighted_average"
            },
            "quality_check": {
                "enabled": True,
                "min_resolution": (300, 300),
                "max_blur_score": 100.0,
                "min_brightness": 0.1,
                "max_brightness": 0.9
            }
        }
    
    def process_image(self, image_path: str) -> Tuple[List[np.ndarray], Dict[str, Any]]:
        """
        Process image through the complete preprocessing pipeline.
        
        Args:
            image_path: Path to the input image
            
        Returns:
            Tuple of (processed_images, metadata)
        """
        try:
            # Load original image
            original_image = cv2.imread(image_path)
            if original_image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
            
            # Extract EXIF data
            exif_data = self._extract_exif(image_path)
            
            # Quality assessment
            quality_metrics = self._assess_quality(image_rgb)
            
            # Initialize metadata
            metadata = {
                "original_shape": image_rgb.shape,
                "exif_data": exif_data,
                "quality_metrics": quality_metrics,
                "processing_steps": []
            }
            
            processed_images = []
            
            # Step 1: Angle correction
            if self.config["angle_correction"]["enabled"]:
                corrected_image, angle_info = self.angle_detector.correct_shelf_angle(
                    image_rgb, self.config["angle_correction"]
                )
                processed_images.append(corrected_image)
                metadata["processing_steps"].append(f"Angle correction: {angle_info}")
                metadata["angle_correction"] = angle_info
            else:
                processed_images.append(image_rgb)
                metadata["angle_correction"] = {"angle": 0.0, "method": "none"}
            
            # Step 2: Lighting normalization
            if self.config["lighting_normalization"]["enabled"]:
                normalized_image = self.lighting_normalizer.normalize_lighting(
                    processed_images[-1], self.config["lighting_normalization"]
                )
                processed_images.append(normalized_image)
                metadata["processing_steps"].append("Lighting normalization")
            else:
                processed_images.append(processed_images[-1])
            
            # Step 3: Enhancement
            if self.config["enhancement"]["enabled"]:
                enhanced_image = self.enhancement_processor.enhance_image(
                    processed_images[-1], self.config["enhancement"]
                )
                processed_images.append(enhanced_image)
                metadata["processing_steps"].append("Image enhancement")
            else:
                processed_images.append(processed_images[-1])
            
            # Step 4: Multi-scale processing
            if self.config["multi_scale"]["enabled"]:
                multi_scale_images = self._create_multi_scale_images(
                    processed_images[-1], self.config["multi_scale"]
                )
                processed_images.extend(multi_scale_images)
                metadata["processing_steps"].append(f"Multi-scale: {len(multi_scale_images)} scales")
            
            # Final processed image (last in the list)
            final_image = processed_images[-1]
            
            metadata.update({
                "final_shape": final_image.shape,
                "processing_success": True,
                "num_processed_images": len(processed_images)
            })
            
            logger.info(f"Preprocessing completed: {len(processed_images)} images generated")
            return processed_images, metadata
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {str(e)}")
            # Return original image as fallback
            original_image = cv2.imread(image_path)
            if original_image is not None:
                original_rgb = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
                return [original_rgb], {"processing_success": False, "error": str(e)}
            raise
    
    def _extract_exif(self, image_path: str) -> Dict[str, Any]:
        """Extract EXIF data from image."""
        try:
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f)
            
            exif_data = {}
            for tag, value in tags.items():
                if not tag.startswith('JPEGThumbnail'):
                    exif_data[tag] = str(value)
            
            return exif_data
        except Exception as e:
            logger.warning(f"Failed to extract EXIF data: {str(e)}")
            return {}
    
    def _assess_quality(self, image: np.ndarray) -> Dict[str, float]:
        """Assess image quality metrics."""
        try:
            # Convert to grayscale for some metrics
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Blur score (Laplacian variance)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Brightness
            brightness = np.mean(gray) / 255.0
            
            # Contrast (standard deviation)
            contrast = np.std(gray) / 255.0
            
            # Sharpness (gradient magnitude)
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            sharpness = np.mean(np.sqrt(grad_x**2 + grad_y**2)) / 255.0
            
            return {
                "blur_score": float(blur_score),
                "brightness": float(brightness),
                "contrast": float(contrast),
                "sharpness": float(sharpness)
            }
        except Exception as e:
            logger.warning(f"Quality assessment failed: {str(e)}")
            return {}
    
    def _create_multi_scale_images(self, image: np.ndarray, config: Dict[str, Any]) -> List[np.ndarray]:
        """Create multi-scale versions of the image."""
        scales = config["scales"]
        multi_scale_images = []
        
        for scale in scales:
            if scale == 1.0:
                continue  # Skip original scale
            
            height, width = image.shape[:2]
            new_height = int(height * scale)
            new_width = int(width * scale)
            
            scaled_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            multi_scale_images.append(scaled_image)
        
        return multi_scale_images


class ShelfAngleDetector:
    """Detects and corrects shelf angles in inventory images."""
    
    def correct_shelf_angle(self, image: np.ndarray, config: Dict[str, Any]) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Detect and correct shelf angle using Hough transform.
        
        Args:
            image: Input RGB image
            config: Configuration for angle detection
            
        Returns:
            Tuple of (corrected_image, angle_info)
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Apply edge detection
            edges = canny(gray, sigma=2)
            
            # Convert to uint8 for Hough transform
            edges_uint8 = (edges * 255).astype(np.uint8)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLinesP(
                edges_uint8,
                rho=1,
                theta=np.pi/180,
                threshold=50,
                minLineLength=config["min_line_length"],
                maxLineGap=config["max_line_gap"]
            )
            
            if lines is None:
                logger.warning("No lines detected for angle correction")
                return image, {"angle": 0.0, "method": "none", "lines_detected": 0}
            
            # Calculate angles of detected lines
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                angles.append(angle)
            
            # Find dominant angle (most frequent)
            if angles:
                # Convert angles to 0-90 degree range
                normalized_angles = []
                for angle in angles:
                    normalized = angle % 90
                    if normalized > 45:
                        normalized = 90 - normalized
                    normalized_angles.append(normalized)
                
                # Find most common angle
                angle_hist, bins = np.histogram(normalized_angles, bins=18, range=(0, 90))
                dominant_angle_bin = np.argmax(angle_hist)
                dominant_angle = (bins[dominant_angle_bin] + bins[dominant_angle_bin + 1]) / 2
                
                # Only correct if angle exceeds tolerance
                if dominant_angle > config["angle_tolerance"]:
                    corrected_image = self._rotate_image(image, -dominant_angle)
                    angle_info = {
                        "angle": dominant_angle,
                        "method": "hough_transform",
                        "lines_detected": len(lines),
                        "corrected": True
                    }
                    return corrected_image, angle_info
            
            # No correction needed
            angle_info = {
                "angle": 0.0,
                "method": "hough_transform",
                "lines_detected": len(lines),
                "corrected": False
            }
            return image, angle_info
            
        except Exception as e:
            logger.error(f"Angle correction failed: {str(e)}")
            return image, {"angle": 0.0, "method": "error", "error": str(e)}
    
    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by specified angle."""
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        
        # Calculate rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Apply rotation
        rotated = cv2.warpAffine(image, rotation_matrix, (width, height), 
                                borderMode=cv2.BORDER_REPLICATE)
        
        return rotated


class LightingNormalizer:
    """Normalizes lighting conditions in images."""
    
    def normalize_lighting(self, image: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
        """
        Normalize lighting using CLAHE or other methods.
        
        Args:
            image: Input RGB image
            config: Configuration for lighting normalization
            
        Returns:
            Normalized image
        """
        try:
            method = config.get("method", "clahe")
            
            if method == "clahe":
                return self._apply_clahe(image, config)
            elif method == "histogram_equalization":
                return self._apply_histogram_equalization(image)
            elif method == "gamma_correction":
                return self._apply_gamma_correction(image)
            else:
                logger.warning(f"Unknown normalization method: {method}")
                return image
                
        except Exception as e:
            logger.error(f"Lighting normalization failed: {str(e)}")
            return image
    
    def _apply_clahe(self, image: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
        """Apply Contrast Limited Adaptive Histogram Equalization."""
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=config["clip_limit"], 
                               tileGridSize=config["tile_grid_size"])
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        
        # Convert back to RGB
        normalized = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        return normalized
    
    def _apply_histogram_equalization(self, image: np.ndarray) -> np.ndarray:
        """Apply standard histogram equalization."""
        # Convert to YUV color space
        yuv = cv2.cvtColor(image, cv2.COLOR_RGB2YUV)
        
        # Apply histogram equalization to Y channel
        yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
        
        # Convert back to RGB
        normalized = cv2.cvtColor(yuv, cv2.COLOR_YUV2RGB)
        return normalized
    
    def _apply_gamma_correction(self, image: np.ndarray, gamma: float = 1.2) -> np.ndarray:
        """Apply gamma correction."""
        # Build lookup table
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        
        # Apply gamma correction
        corrected = cv2.LUT(image, table)
        return corrected


class ImageEnhancer:
    """Enhances image quality through various techniques."""
    
    def enhance_image(self, image: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
        """
        Apply image enhancement techniques.
        
        Args:
            image: Input RGB image
            config: Configuration for enhancement
            
        Returns:
            Enhanced image
        """
        try:
            enhanced = image.copy()
            
            if config.get("sharpening", True):
                enhanced = self._apply_sharpening(enhanced)
            
            if config.get("noise_reduction", True):
                enhanced = self._apply_noise_reduction(enhanced)
            
            if config.get("contrast_enhancement", True):
                enhanced = self._enhance_contrast(enhanced)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Image enhancement failed: {str(e)}")
            return image
    
    def _apply_sharpening(self, image: np.ndarray) -> np.ndarray:
        """Apply unsharp masking for sharpening."""
        # Create Gaussian blur
        blurred = cv2.GaussianBlur(image, (0, 0), 2.0)
        
        # Calculate sharpened image
        sharpened = cv2.addWeighted(image, 1.5, blurred, -0.5, 0)
        
        return np.clip(sharpened, 0, 255).astype(np.uint8)
    
    def _apply_noise_reduction(self, image: np.ndarray) -> np.ndarray:
        """Apply non-local means denoising."""
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        return denoised
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance contrast using adaptive techniques."""
        # Convert to PIL for enhancement
        pil_image = Image.fromarray(image)
        
        # Apply contrast enhancement
        enhancer = ImageEnhance.Contrast(pil_image)
        enhanced = enhancer.enhance(1.2)
        
        return np.array(enhanced)

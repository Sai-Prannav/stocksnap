from .image_analyzer import ImageAnalyzer, BoundingBox, AnalysisResult
from .real_image_analyzer import RealImageAnalyzer
from .storage import StorageService

# This ensures that when the app asks for an analyzer, 
# it gets the real one we just fixed.
__all__ = ["ImageAnalyzer", "RealImageAnalyzer", "StorageService", "BoundingBox", "AnalysisResult"]
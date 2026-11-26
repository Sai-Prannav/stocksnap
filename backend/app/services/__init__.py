from .image_analyzer import ImageAnalyzer, BoundingBox, AnalysisResult
from .storage import StorageService

__all__ = ["ImageAnalyzer", "RealImageAnalyzer", "StorageService", "BoundingBox", "AnalysisResult"]


def __getattr__(name):
    # YOLO11 (ultralytics + PyTorch) is imported only when it is actually used, so the package imports without it
    # (the tests and CI run on the mock analyzer)
    if name == "RealImageAnalyzer":
        from .real_image_analyzer import RealImageAnalyzer
        return RealImageAnalyzer
    raise AttributeError(name)

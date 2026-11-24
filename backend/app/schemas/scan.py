from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

from app import schemas
from .detection import DetectionResponse
from .segmentation_mask import SegmentationMaskResponse
from .store import StoreResponse
from .product import ProductResponse

class ScanBase(BaseModel):
    store_id: int
    product_id: int
    notes: Optional[str] = None

class ScanCreate(ScanBase):
    pass

class ScanResponse(BaseModel):
    id: int
    store_id: int
    product_id: int
    count: int
    confidence: float
    image_path: str
    
    timestamp: Optional[datetime] = None
    scanned_at: Optional[datetime] = None
    detections: Optional[List[dict]] = None
    
    store: Optional[schemas.StoreResponse] = None
    product: Optional[schemas.ProductResponse] = None

    class Config:
        from_attributes = True

class ScanDetail(ScanResponse):
    detections: List[DetectionResponse]
    segmentation_masks: List[SegmentationMaskResponse]

class ScanList(BaseModel):
    id: int
    image_path: str
    count: int
    confidence: float
    scanned_at: datetime
    store_name: str
    product_name: str

    class Config:
        from_attributes = True

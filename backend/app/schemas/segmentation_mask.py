from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class SegmentationMaskResponse(BaseModel):
    id: int
    mask_type: str
    mask_data: Dict[str, Any]
    label: str
    confidence: Optional[float] = None
    file_path: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

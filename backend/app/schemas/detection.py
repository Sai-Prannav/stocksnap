from pydantic import BaseModel
from typing import Optional, Dict, Any

class DetectionResponse(BaseModel):
    id: int
    x1: float
    y1: float
    x2: float
    y2: float
    label: str
    confidence: float
    area: Optional[float] = None
    properties: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

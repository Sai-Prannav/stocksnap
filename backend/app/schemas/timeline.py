from pydantic import BaseModel
from datetime import date
from typing import Optional

class TimelineDataPoint(BaseModel):
    date: date
    count: int
    avg_confidence: float
    scan_count: int

class TimelineRequest(BaseModel):
    store_id: Optional[int] = None
    product_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    group_by: str = "day"  # day, week, month

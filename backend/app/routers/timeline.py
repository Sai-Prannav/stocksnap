from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Optional
from datetime import datetime, timedelta
from app.db.database import get_db
from app.models.models import Scan
from app.schemas.timeline import TimelineRequest, TimelineDataPoint

router = APIRouter()

@router.post("/data", response_model=List[TimelineDataPoint])
async def get_timeline_data(
    request: TimelineRequest,
    db: Session = Depends(get_db)
):
    """Get timeline data for inventory counts over time."""
    
    # Build base query
    query = db.query(
        func.date(Scan.scanned_at).label('date'),
        func.avg(Scan.count).label('avg_count'),
        func.avg(Scan.confidence).label('avg_confidence'),
        func.count(Scan.id).label('scan_count')
    )
    
    # Apply filters
    if request.store_id:
        query = query.filter(Scan.store_id == request.store_id)
    if request.product_id:
        query = query.filter(Scan.product_id == request.product_id)
    if request.start_date:
        query = query.filter(func.date(Scan.scanned_at) >= request.start_date)
    if request.end_date:
        query = query.filter(func.date(Scan.scanned_at) <= request.end_date)
    
    # Group by date
    query = query.group_by(func.date(Scan.scanned_at))
    
    # Order by date
    query = query.order_by(func.date(Scan.scanned_at))
    
    # Execute query
    results = query.all()
    
    # Convert to response format
    timeline_data = []
    for result in results:
        timeline_data.append(TimelineDataPoint(
            date=result.date,
            count=int(result.avg_count),
            avg_confidence=float(result.avg_confidence),
            scan_count=result.scan_count
        ))
    
    return timeline_data

@router.get("/stats")
async def get_analysis_stats(
    store_id: Optional[int] = None,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get aggregate statistics for analysis data."""
    
    query = db.query(
        func.count(Scan.id).label('total_scans'),
        func.avg(Scan.count).label('avg_count'),
        func.avg(Scan.confidence).label('avg_confidence'),
        func.min(Scan.count).label('min_count'),
        func.max(Scan.count).label('max_count')
    )
    
    # Apply filters
    if store_id:
        query = query.filter(Scan.store_id == store_id)
    if product_id:
        query = query.filter(Scan.product_id == product_id)
    
    result = query.first()
    
    return {
        "total_scans": result.total_scans or 0,
        "avg_count": float(result.avg_count) if result.avg_count else 0,
        "avg_confidence": float(result.avg_confidence) if result.avg_confidence else 0,
        "min_count": result.min_count or 0,
        "max_count": result.max_count or 0
    }

@router.get("/summary")
async def get_timeline_summary(
    days: int = 7,
    store_id: Optional[int] = None,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get summary data for the last N days."""
    
    start_date = datetime.now() - timedelta(days=days)
    
    query = db.query(
        func.date(Scan.scanned_at).label('date'),
        func.sum(Scan.count).label('total_count'),
        func.count(Scan.id).label('scan_count')
    ).filter(Scan.scanned_at >= start_date)
    
    # Apply filters
    if store_id:
        query = query.filter(Scan.store_id == store_id)
    if product_id:
        query = query.filter(Scan.product_id == product_id)
    
    query = query.group_by(func.date(Scan.scanned_at)).order_by(func.date(Scan.scanned_at))
    
    results = query.all()
    
    summary = []
    for result in results:
        summary.append({
            "date": result.date,
            "total_count": result.total_count,
            "scan_count": result.scan_count,
            "avg_per_scan": result.total_count / result.scan_count if result.scan_count > 0 else 0
        })
    
    return summary

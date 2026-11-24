import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Scan
from app.services.storage import StorageService
from app.services.image_analyzer import MockImageAnalyzer
from app.services.real_image_analyzer import RealImageAnalyzer
from app.services.image_annotator import ImageAnnotator
from app import schemas
from app.models import models

router = APIRouter(tags=["scans"])

# Initialize Services
storage_service = StorageService()
image_annotator = ImageAnnotator()

# YOLO11 is the default analyzer; the mock is used only if the model cannot load
try:
    image_analyzer = RealImageAnalyzer()
    print("StockSnap detection: YOLO11 active")
except Exception as e:
    print(f"WARNING: YOLO11 could not be loaded, using the mock fallback analyzer: {e}")
    image_analyzer = MockImageAnalyzer()

@router.get("/{scan_id}/annotated")
async def get_annotated_image(scan_id: int, db: Session = Depends(get_db)):
    """Return the path (served under /uploads) of the image with detection boxes drawn."""
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    annotated = f"uploads/annotated/annotated_{os.path.basename(scan.image_path)}"
    if not os.path.exists(annotated):
        raise HTTPException(status_code=404, detail="Annotated image not found")
    return {"annotated_image_path": annotated}

@router.post("/", response_model=schemas.ScanResponse)
async def create_scan(
    store_id: int = Form(...),
    product_id: int = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Save the file
    file_path = await storage_service.save_upload_file(image)
    
    # 2. Run AI Analysis
    analysis = await image_analyzer.analyze_image(file_path)
    
    # 3. Create DB Record
    db_scan = Scan(
        store_id=store_id,
        product_id=product_id,
        image_path=file_path,
        count=analysis.count,
        confidence=analysis.confidence
    )
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)
    db_scan.store = db.query(models.Store).get(store_id)
    db_scan.product = db.query(models.Product).get(product_id)
    
    db_scan.detections = [
        {"box": [b.x1, b.y1, b.x2, b.y2], "confidence": b.confidence, "class_name": b.label}
        for b in analysis.bounding_boxes
    ]

    # 4. Draw Bold Bounding Boxes
    if image_annotator:
        detections = [
            {'box': [b.x1, b.y1, b.x2, b.y2], 'label': b.label, 'conf': b.confidence}
            for b in analysis.bounding_boxes
        ]
        image_annotator.annotate_image_with_boxes(file_path, detections)

    return db_scan

@router.get("/", response_model=List[schemas.ScanResponse])
def get_scans(db: Session = Depends(get_db)):
    return db.query(Scan).all()

@router.get("/{scan_id}")
def get_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan
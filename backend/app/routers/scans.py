import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Scan
from app.services.storage import StorageService
from app.services.image_analyzer import MockImageAnalyzer
from app.services.image_annotator import ImageAnnotator
from app import schemas
from app.models import models

router = APIRouter(tags=["scans"])

# Initialize Services
storage_service = StorageService()
image_annotator = ImageAnnotator()

# YOLO11 is the default analyzer; the mock is used if the model cannot load, or on purpose with
# STOCKSNAP_ANALYZER=mock (tests and CI, which do not install ultralytics / PyTorch)
def _make_analyzer():
    if os.environ.get("STOCKSNAP_ANALYZER") == "mock":
        return MockImageAnalyzer()
    try:
        from app.services.real_image_analyzer import RealImageAnalyzer
        analyzer = RealImageAnalyzer()
        print("StockSnap detection: YOLO11 active")
        return analyzer
    except Exception as e:
        print(f"WARNING: YOLO11 could not be loaded, using the mock fallback analyzer: {e}")
        return MockImageAnalyzer()


image_analyzer = _make_analyzer()

ALLOWED_IMAGE_TYPES = {"image/jpeg": {".jpg", ".jpeg"}, "image/png": {".png"}, "image/webp": {".webp"}}
MAX_UPLOAD_BYTES = int(float(os.environ.get("STOCKSNAP_MAX_UPLOAD_MB", "10")) * 1024 * 1024)


def check_upload(image: UploadFile) -> None:
    """Shelf photos only: JPEG / PNG / WebP (type and extension must agree), at most MAX_UPLOAD_BYTES."""
    ext = os.path.splitext(image.filename or "")[1].lower()
    if ext not in ALLOWED_IMAGE_TYPES.get(image.content_type or "", set()):
        raise HTTPException(status_code=415, detail="upload a JPEG, PNG or WebP photo")
    image.file.seek(0, os.SEEK_END)
    size = image.file.tell()
    image.file.seek(0)
    if size == 0:
        raise HTTPException(status_code=400, detail="the photo is empty")
    if size > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"the photo is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB")

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
    # 1. Check and save the file
    check_upload(image)
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
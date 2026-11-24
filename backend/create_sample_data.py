#!/usr/bin/env python3
"""
Script to create sample data for testing the inventory management system.
This creates stores, products, and sample scans with mock analysis data.
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal, engine, Base
from app.models.models import Store, Product, Scan
# from app.models.detection import Detection
# from app.models.segmentation_mask import SegmentationMask

def create_sample_data():
    """Create sample stores, products, and scans."""
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(Store).count() > 0:
            print("Sample data already exists. Skipping creation.")
            return
        
        # Create stores
        stores = [
            Store(name="Main Street Store", location="123 Main St, City, State", description="Primary retail location"),
            Store(name="Downtown Branch", location="456 Oak Ave, Downtown", description="Central business district location"),
            Store(name="Mall Outlet", location="789 Shopping Center, Mall", description="Shopping mall location"),
            Store(name="Airport Store", location="321 Terminal Rd, Airport", description="Travel hub location"),
            Store(name="Suburban Location", location="654 Residential Blvd, Suburbs", description="Residential area store")
        ]
        
        for store in stores:
            db.add(store)
        db.commit()
        
        print(f"Created {len(stores)} stores")
        
        # Refresh to get IDs
        for store in stores:
            db.refresh(store)
        
        # Create products
        products = [
            Product(name="Soda Can 12oz", sku="SDA-001", category="Beverages", description="Carbonated soft drink"),
            Product(name="Water Bottle 500ml", sku="WTR-002", category="Beverages", description="Purified drinking water"),
            Product(name="Chips Bag 200g", sku="CHP-003", category="Snacks", description="Potato chips"),
            Product(name="Chocolate Bar 100g", sku="CHC-004", category="Confectionery", description="Milk chocolate"),
            Product(name="Energy Drink 250ml", sku="ENG-005", category="Beverages", description="Caffeinated energy drink"),
            Product(name="Cookies Pack 300g", sku="COO-006", category="Snacks", description="Chocolate chip cookies"),
            Product(name="Juice Box 200ml", sku="JUC-007", category="Beverages", description="Orange juice"),
            Product(name="Granola Bar 40g", sku="GRN-008", category="Snacks", description="Oats and honey granola")
        ]
        
        for product in products:
            db.add(product)
        db.commit()
        
        print(f"Created {len(products)} products")
        
        # Refresh to get IDs
        for product in products:
            db.refresh(product)
        
        # Create sample scans with mock data
        scan_count = 0
        for store in stores:
            for product in products:
                # Create 2-5 scans per store-product combination
                num_scans = random.randint(2, 5)
                
                for i in range(num_scans):
                    # Random date within last 30 days
                    days_ago = random.randint(0, 30)
                    scan_date = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
                    
                    # Mock analysis results
                    count = random.randint(5, 50)
                    confidence = round(random.uniform(0.75, 0.98), 3)
                    
                    # Create scan
                    scan = Scan(
                        store_id=store.id,
                        product_id=product.id,
                        image_path=f"uploads/images/sample_{scan_count}.jpg",
                        count=count,
                        confidence=confidence,
                        scanned_at=scan_date,
                        notes=f"Sample scan #{scan_count + 1}"
                    )
                    db.add(scan)
                    db.commit()
                    db.refresh(scan)
                    
                    # Create detections (bounding boxes)
                    num_detections = random.randint(1, min(count, 10))
                    for j in range(num_detections):
                        detection = Detection(
                            scan_id=scan.id,
                            x1=round(random.uniform(0.05, 0.4), 3),
                            y1=round(random.uniform(0.05, 0.6), 3),
                            x2=round(random.uniform(0.5, 0.95), 3),
                            y2=round(random.uniform(0.5, 0.95), 3),
                            label=random.choice(["product", "item", "package", "container"]),
                            confidence=round(random.uniform(0.8, 0.99), 3),
                            area=round(random.uniform(0.01, 0.3), 4)
                        )
                        db.add(detection)
                    
                    # Create segmentation masks (for some detections)
                    num_masks = random.randint(0, min(num_detections // 2, 3))
                    for k in range(num_masks):
                        mask = SegmentationMask(
                            scan_id=scan.id,
                            mask_type="polygon",
                            mask_data={"points": [
                                {"x": round(random.uniform(0.1, 0.4), 3), "y": round(random.uniform(0.1, 0.4), 3)},
                                {"x": round(random.uniform(0.5, 0.8), 3), "y": round(random.uniform(0.1, 0.4), 3)},
                                {"x": round(random.uniform(0.5, 0.8), 3), "y": round(random.uniform(0.5, 0.8), 3)},
                                {"x": round(random.uniform(0.1, 0.4), 3), "y": round(random.uniform(0.5, 0.8), 3)}
                            ]},
                            label=random.choice(["product", "item", "package"]),
                            confidence=round(random.uniform(0.85, 0.95), 3)
                        )
                        db.add(mask)
                    
                    scan_count += 1
        
        db.commit()
        print(f"Created {scan_count} sample scans with detections and masks")
        
        # Print summary
        total_stores = db.query(Store).count()
        total_products = db.query(Product).count()
        total_scans = db.query(Scan).count()
        total_detections = db.query(Detection).count()
        total_masks = db.query(SegmentationMask).count()
        
        print("\n=== Sample Data Summary ===")
        print(f"Stores: {total_stores}")
        print(f"Products: {total_products}")
        print(f"Scans: {total_scans}")
        print(f"Detections: {total_detections}")
        print(f"Segmentation Masks: {total_masks}")
        print("========================")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()

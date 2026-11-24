#!/usr/bin/env python3
"""
API Documentation and Testing Guide
==================================

This document provides information about the Inventory Management API endpoints
and how to test them.

Base URL: http://localhost:8000

API Documentation (Swagger UI): http://localhost:8000/docs
ReDoc Documentation: http://localhost:8000/redoc

## Available Endpoints

### Stores (/api/stores)
- GET /api/stores/ - List all stores
- GET /api/stores/{id} - Get specific store
- POST /api/stores/ - Create new store
- PUT /api/stores/{id} - Update store
- DELETE /api/stores/{id} - Delete store

### Products (/api/products)
- GET /api/products/ - List all products
- GET /api/products/{id} - Get specific product
- POST /api/products/ - Create new product
- PUT /api/products/{id} - Update product
- DELETE /api/products/{id} - Delete product

### Scans (/api/scans)
- GET /api/scans/ - List scans with filtering
- GET /api/scans/{id} - Get detailed scan info
- POST /api/scans/ - Upload image and create scan
- DELETE /api/scans/{id} - Delete scan

### Timeline (/api/timeline)
- POST /api/timeline/data - Get timeline data
- GET /api/timeline/stats - Get analysis statistics
- GET /api/timeline/summary - Get summary data

### Static Files
- GET /uploads/* - Serve uploaded images

## Sample Requests

### Create a Store
```bash
curl -X POST "http://localhost:8000/api/stores/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Store",
    "location": "123 Test St",
    "description": "A test store"
  }'
```

### Create a Product
```bash
curl -X POST "http://localhost:8000/api/products/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Product",
    "sku": "TEST-001",
    "category": "Test Category",
    "description": "A test product"
  }'
```

### Upload Image for Analysis
```bash
curl -X POST "http://localhost:8000/api/scans/" \
  -F "store_id=1" \
  -F "product_id=1" \
  -F "notes=Test scan" \
  -F "image=@/path/to/image.jpg"
```

### Get Timeline Data
```bash
curl -X POST "http://localhost:8000/api/timeline/data" \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": 1,
    "product_id": 1,
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "group_by": "day"
  }'
```

## Database Schema

### Stores Table
- id (Integer, Primary Key)
- name (String, Required)
- location (String, Optional)
- description (String, Optional)
- created_at (DateTime)
- updated_at (DateTime, Optional)

### Products Table
- id (Integer, Primary Key)
- name (String, Required)
- sku (String, Optional, Unique)
- description (String, Optional)
- category (String, Optional)
- created_at (DateTime)
- updated_at (DateTime, Optional)

### Scans Table
- id (Integer, Primary Key)
- store_id (Integer, Foreign Key)
- product_id (Integer, Foreign Key)
- image_path (String, Required)
- count (Integer, Required)
- confidence (Float, Required)
- scanned_at (DateTime)
- notes (Text, Optional)

### Detections Table
- id (Integer, Primary Key)
- scan_id (Integer, Foreign Key)
- x1, y1, x2, y2 (Float, Required)
- label (String, Required)
- confidence (Float, Required)
- area (Float, Optional)

### Segmentation Masks Table
- id (Integer, Primary Key)
- scan_id (Integer, Foreign Key)
- mask_type (String, Required)
- mask_data (JSON, Required)
- label (String, Required)
- confidence (Float, Optional)

## Running the Application

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create sample data:
```bash
python create_sample_data.py
```

3. Start the server:
```bash
python main.py
```

4. Access the API at http://localhost:8000

## Testing with Frontend

The frontend should be able to connect to the backend at http://localhost:8000
and use all the API endpoints mentioned above.

## Image Analysis

The system includes a mock image analyzer that generates realistic detection
results. In production, you can replace the MockImageAnalyzer with a real
computer vision service.

## File Storage

Uploaded images are stored in the `uploads/` directory and served via the
`/uploads/` endpoint. The system supports various image formats and includes
proper file validation and cleanup.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Updated Imports to match your folder structure
from app.db.database import engine, Base
from app.models import models  # Essential to create the tables
from app.routers import stores, products, scans, timeline

# Create database tables
# This uses the models imported above to build app.db
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="StockSnap API",
    description="Inventory management with AI analysis",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    # the Vite dev server by default; set STOCKSNAP_CORS_ORIGINS (comma-separated) for a deployed frontend
    allow_origins=[o.strip() for o in os.environ.get("STOCKSNAP_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stores.router, prefix="/api/stores", tags=["stores"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(scans.router, prefix="/api/scans", tags=["scans"])
app.include_router(timeline.router, prefix="/api/timeline", tags=["timeline"])

# Setup Directories and Static Files
os.makedirs("uploads/annotated", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    return {"message": "StockSnap API is running"}

if __name__ == "__main__":
    import uvicorn
    # Changed to app.main:app because you're starting from the backend folder
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import Store
from app.schemas.store import StoreCreate, StoreResponse, StoreUpdate
from app import models, schemas

router = APIRouter(tags=["stores"])

@router.post("/", response_model=schemas.StoreResponse)
def create_store(store: schemas.StoreCreate, db: Session = Depends(get_db)):
    db_store = models.Store(**store.dict())
    db.add(db_store)
    db.commit()
    db.refresh(db_store)
    return db_store

@router.get("/", response_model=List[StoreResponse])
async def list_stores(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all stores with pagination."""
    stores = db.query(Store).offset(skip).limit(limit).all()
    return stores

@router.get("/{store_id}", response_model=StoreResponse)
async def get_store(store_id: int, db: Session = Depends(get_db)):
    """Get a specific store by ID."""
    store = db.query(Store).filter(Store.id == store_id).first()
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")
    return store

@router.put("/{store_id}", response_model=StoreResponse)
async def update_store(store_id: int, store_update: StoreUpdate, db: Session = Depends(get_db)):
    """Update a store."""
    store = db.query(Store).filter(Store.id == store_id).first()
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")
    
    update_data = store_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(store, field, value)
    
    db.commit()
    db.refresh(store)
    return store

@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store(store_id: int, db: Session = Depends(get_db)):
    """Delete a store."""
    store = db.query(Store).filter(Store.id == store_id).first()
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")
    
    db.delete(store)
    db.commit()
    return None

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from ..db.database import Base

class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    description = Column(String, nullable=True) 
    scans = relationship("Scan", back_populates="store")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    sku = Column(String, unique=True, index=True)
    category = Column(String, nullable=True)
    description = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scans = relationship("Scan", back_populates="product")

class Scan(Base):
    __tablename__ = "scans"
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    image_path = Column(String)
    count = Column(Integer)
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    store = relationship("Store", back_populates="scans")
    product = relationship("Product", back_populates="scans")

    @hybrid_property
    def scanned_at(self):
        """Alias used by the frontend."""
        return self.timestamp
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class ProductBase(BaseModel):
    name: str
    sku: str
    category: Optional[str] = None
    description: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    sku: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=100)

    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Product name cannot be empty')
            return v.strip()
        return v

    @validator('sku')
    def validate_sku(cls, v):
        if v is not None:
            return v.strip().upper()
        return v

class ProductResponse(ProductBase):
    id: int
    created_at: Optional[datetime] = None  # Change this line
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
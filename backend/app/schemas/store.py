from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class StoreBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Store name")
    location: Optional[str] = Field(None, max_length=200, description="Store location")
    description: Optional[str] = Field(None, max_length=500, description="Store description")

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Store name cannot be empty')
        return v.strip()

class StoreCreate(StoreBase):
    pass

class StoreUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=500)

    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Store name cannot be empty')
            return v.strip()
        return v

class StoreResponse(StoreBase):
    id: int
    created_at: Optional[datetime] = None  # Changed this line
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

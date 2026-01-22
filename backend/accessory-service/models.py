"""
Accessory Model Definition

This module defines the Accessory data model using Pydantic for validation
and type checking, following Azure CosmosDB best practices.
"""

import uuid
from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# Type definitions for accessory categories and sizes
AccessoryType = Literal["toy", "food", "collar", "bedding", "grooming", "other"]
AccessorySize = Literal["S", "M", "L", "XL"]


class AccessoryBase(BaseModel):
    """Base Accessory model with common fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Accessory name")
    type: AccessoryType = Field(..., description="Accessory type/category")
    price: float = Field(..., ge=0, description="Price (must be non-negative)")
    stock: int = Field(..., ge=0, description="Stock quantity (must be non-negative)")
    size: AccessorySize = Field(..., description="Size category (S, M, L, XL)")
    imageUrl: Optional[str] = Field(None, description="URL to accessory image")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed description")


class AccessoryCreate(AccessoryBase):
    """Model for creating a new accessory"""
    pass


class AccessoryUpdate(BaseModel):
    """Model for updating an existing accessory (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[AccessoryType] = None
    price: Optional[float] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    size: Optional[AccessorySize] = None
    imageUrl: Optional[str] = None
    description: Optional[str] = Field(None, max_length=2000)


class Accessory(AccessoryBase):
    """Complete Accessory model with ID and metadata"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique accessory identifier")
    createdAt: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updatedAt: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AccessorySearchFilters(BaseModel):
    """Model for search and filter parameters"""
    search: Optional[str] = Field(None, description="Search term for name or description")
    type: Optional[AccessoryType] = Field(None, description="Filter by accessory type")
    lowStockOnly: Optional[bool] = Field(False, description="Show only items with stock < 10")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")

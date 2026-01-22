"""
Accessory Model Definition

This module defines the Accessory data model using Pydantic for validation
and type checking, following Azure CosmosDB best practices.
"""

import uuid
from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class AccessoryBase(BaseModel):
    """Base Accessory model with common fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Accessory name")
    type: Literal["toy", "food", "collar", "bedding", "grooming", "other"] = Field(..., description="Accessory type")
    price: float = Field(..., ge=0, description="Price in decimal format")
    stock: int = Field(..., ge=0, description="Stock quantity")
    size: Literal["S", "M", "L", "XL"] = Field(..., description="Size category")
    imageUrl: Optional[str] = Field(None, description="URL to accessory image")
    description: Optional[str] = Field(None, max_length=2000, description="Description of the accessory")


class AccessoryCreate(AccessoryBase):
    """Model for creating a new accessory"""
    pass


class AccessoryUpdate(BaseModel):
    """Model for updating an existing accessory"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[Literal["toy", "food", "collar", "bedding", "grooming", "other"]] = None
    price: Optional[float] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    size: Optional[Literal["S", "M", "L", "XL"]] = None
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
    type: Optional[Literal["toy", "food", "collar", "bedding", "grooming", "other"]] = Field(None, description="Filter by accessory type")
    lowStockOnly: Optional[bool] = Field(None, description="Show only low stock items (stock < 10)")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")
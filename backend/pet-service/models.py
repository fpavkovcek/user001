"""
Pet Model Definition

This module defines the Pet data model using Pydantic for validation
and type checking, following Azure CosmosDB best practices.
"""

import uuid
from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class PetBase(BaseModel):
    """Base Pet model with common fields"""
    name: str = Field(..., min_length=1, max_length=100, description="Pet name")
    species: Literal["dog", "cat", "bird", "other"] = Field(..., description="Pet species")
    ageYears: int = Field(..., ge=0, le=50, description="Pet age in years")
    health: int = Field(..., ge=0, le=100, description="Health level (0-100)")
    happiness: int = Field(..., ge=0, le=100, description="Happiness level (0-100)")
    energy: int = Field(..., ge=0, le=100, description="Energy level (0-100)")
    avatarUrl: Optional[str] = Field(None, description="URL to pet avatar image")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes about the pet")


class PetCreate(PetBase):
    """Model for creating a new pet"""
    pass


class PetUpdate(BaseModel):
    """Model for updating an existing pet"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    species: Optional[Literal["dog", "cat", "bird", "other"]] = None
    ageYears: Optional[int] = Field(None, ge=0, le=50)
    health: Optional[int] = Field(None, ge=0, le=100)
    happiness: Optional[int] = Field(None, ge=0, le=100)
    energy: Optional[int] = Field(None, ge=0, le=100)
    avatarUrl: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)


class Pet(PetBase):
    """Complete Pet model with ID and metadata"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique pet identifier")
    createdAt: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updatedAt: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PetSearchFilters(BaseModel):
    """Model for search and filter parameters"""
    search: Optional[str] = Field(None, description="Search term for name or notes")
    species: Optional[Literal["dog", "cat", "bird", "other"]] = Field(None, description="Filter by species")
    status: Optional[str] = Field(None, description="Filter by status (reserved for future use)")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")
"""
Activity Model Definition

This module defines the Activity data model using Pydantic for validation
and type checking, following Azure CosmosDB best practices.
"""

import uuid
from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class ActivityBase(BaseModel):
    """Base Activity model with common fields"""
    petId: str = Field(..., description="ID of the pet this activity belongs to")
    type: Literal["feed", "walk", "play", "vet", "train"] = Field(..., description="Activity type")
    timestamp: datetime = Field(..., description="When the activity occurred")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes about the activity")


class ActivityCreate(ActivityBase):
    """Model for creating a new activity"""
    pass


class ActivityUpdate(BaseModel):
    """Model for updating an existing activity"""
    petId: Optional[str] = Field(None, description="ID of the pet this activity belongs to")
    type: Optional[Literal["feed", "walk", "play", "vet", "train"]] = None
    timestamp: Optional[datetime] = Field(None, description="When the activity occurred")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes about the activity")


class Activity(ActivityBase):
    """Complete Activity model with ID and metadata"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique activity identifier")
    createdAt: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updatedAt: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ActivitySearchFilters(BaseModel):
    """Model for search and filter parameters"""
    petId: Optional[str] = Field(None, description="Filter by pet ID")
    type: Optional[Literal["feed", "walk", "play", "vet", "train"]] = Field(None, description="Filter by activity type")
    from_timestamp: Optional[datetime] = Field(None, alias="from", description="Filter activities from this timestamp")
    to_timestamp: Optional[datetime] = Field(None, alias="to", description="Filter activities to this timestamp")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")

    class Config:
        populate_by_name = True  # Allow both 'from' and 'from_timestamp'
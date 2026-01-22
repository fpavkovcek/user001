"""
Discussion Service Models

This module defines the data models for the discussions service using Pydantic
for validation and type checking, following Azure CosmosDB best practices.

Data Model:
- Room: Discussion rooms (public or private) with membership management
- Message: Messages within rooms with support for threads and attachments
- Invitation: Invitations to private rooms
- Attachment: File attachments for messages
"""

import uuid
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# =============================================================================
# Room Models
# =============================================================================

class RoomBase(BaseModel):
    """Base Room model with common fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Room name")
    description: Optional[str] = Field(None, max_length=2000, description="Room description")
    is_private: bool = Field(False, description="Whether the room is private (invitation only)")
    owner_id: str = Field(..., min_length=1, max_length=100, description="User ID of room owner")


class RoomCreate(RoomBase):
    """Model for creating a new room"""
    pass


class RoomUpdate(BaseModel):
    """Model for updating an existing room"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    is_private: Optional[bool] = None


class Room(RoomBase):
    """Complete Room model with ID and metadata"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique room identifier")
    members: List[str] = Field(default_factory=list, description="List of member user IDs")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RoomResponse(Room):
    """Room response model for API"""
    member_count: int = Field(0, description="Number of members in the room")

    @classmethod
    def from_room(cls, room: Room) -> "RoomResponse":
        """Create RoomResponse from Room"""
        return cls(
            **room.model_dump(),
            member_count=len(room.members)
        )


# =============================================================================
# Message Models
# =============================================================================

class AttachmentBase(BaseModel):
    """Base Attachment model"""
    filename: str = Field(..., min_length=1, max_length=500, description="Original filename")
    content_type: str = Field(..., description="MIME type of the attachment")
    size_bytes: int = Field(..., ge=0, description="File size in bytes")
    url: str = Field(..., description="URL to access the attachment")


class AttachmentCreate(AttachmentBase):
    """Model for creating a new attachment"""
    pass


class Attachment(AttachmentBase):
    """Complete Attachment model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique attachment identifier")
    message_id: str = Field(..., description="ID of the message this attachment belongs to")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MessageBase(BaseModel):
    """Base Message model with common fields"""
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")
    author_id: str = Field(..., min_length=1, max_length=100, description="User ID of message author")


class MessageCreate(MessageBase):
    """Model for creating a new message"""
    room_id: str = Field(..., description="ID of the room to post message in")
    parent_message_id: Optional[str] = Field(None, description="Parent message ID for thread replies")
    attachments: Optional[List[AttachmentCreate]] = Field(None, description="List of attachments")


class MessageUpdate(BaseModel):
    """Model for updating an existing message"""
    content: Optional[str] = Field(None, min_length=1, max_length=10000)


class Message(MessageBase):
    """Complete Message model with ID and metadata"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique message identifier")
    room_id: str = Field(..., description="ID of the room this message belongs to")
    parent_message_id: Optional[str] = Field(None, description="Parent message ID for thread replies")
    attachments: List[Attachment] = Field(default_factory=list, description="List of attachments")
    reply_count: int = Field(0, description="Number of replies to this message")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    is_edited: bool = Field(False, description="Whether the message has been edited")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# =============================================================================
# Invitation Models
# =============================================================================

class InvitationBase(BaseModel):
    """Base Invitation model"""
    room_id: str = Field(..., description="ID of the room to invite to")
    invitee_id: str = Field(..., min_length=1, max_length=100, description="User ID of the invitee")
    inviter_id: str = Field(..., min_length=1, max_length=100, description="User ID of the inviter")
    message: Optional[str] = Field(None, max_length=500, description="Optional invitation message")


class InvitationCreate(BaseModel):
    """Model for creating a new invitation"""
    room_id: str = Field(..., description="ID of the room to invite to")
    invitee_id: str = Field(..., min_length=1, max_length=100, description="User ID of the invitee")
    message: Optional[str] = Field(None, max_length=500, description="Optional invitation message")


class Invitation(InvitationBase):
    """Complete Invitation model with ID and metadata"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique invitation identifier")
    status: Literal["pending", "accepted", "declined", "expired"] = Field(
        "pending", description="Invitation status"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    responded_at: Optional[datetime] = Field(None, description="Response timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InvitationResponse(BaseModel):
    """Model for responding to an invitation"""
    action: Literal["accept", "decline"] = Field(..., description="Response action")


# =============================================================================
# Membership Models
# =============================================================================

class MembershipAdd(BaseModel):
    """Model for adding a member to a room"""
    user_id: str = Field(..., min_length=1, max_length=100, description="User ID to add")


class MembershipRemove(BaseModel):
    """Model for removing a member from a room"""
    user_id: str = Field(..., min_length=1, max_length=100, description="User ID to remove")


# =============================================================================
# Query/Filter Models
# =============================================================================

class RoomSearchFilters(BaseModel):
    """Model for room search parameters"""
    search: Optional[str] = Field(None, description="Search term for name or description")
    is_private: Optional[bool] = Field(None, description="Filter by privacy setting")
    owner_id: Optional[str] = Field(None, description="Filter by owner")
    member_id: Optional[str] = Field(None, description="Filter by member")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class MessageSearchFilters(BaseModel):
    """Model for message search parameters"""
    room_id: Optional[str] = Field(None, description="Filter by room")
    author_id: Optional[str] = Field(None, description="Filter by author")
    search: Optional[str] = Field(None, description="Search term for content")
    parent_message_id: Optional[str] = Field(None, description="Filter by parent message (for threads)")
    has_attachments: Optional[bool] = Field(None, description="Filter messages with attachments")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class InvitationSearchFilters(BaseModel):
    """Model for invitation search parameters"""
    room_id: Optional[str] = Field(None, description="Filter by room")
    invitee_id: Optional[str] = Field(None, description="Filter by invitee")
    inviter_id: Optional[str] = Field(None, description="Filter by inviter")
    status: Optional[Literal["pending", "accepted", "declined", "expired"]] = Field(
        None, description="Filter by status"
    )
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")

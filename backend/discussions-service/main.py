"""
FastAPI Discussions Service API

This module implements a REST API for pet owner discussions using FastAPI and Azure CosmosDB.
Follows Azure best practices for error handling and API design.

Features:
- Discussion rooms (public and private)
- Message threads with attachments
- Room invitations and membership management
- No authentication required (simplified for demo)
"""

import logging
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from models import (
    Room, RoomCreate, RoomUpdate, RoomSearchFilters, RoomResponse,
    Message, MessageCreate, MessageUpdate, MessageSearchFilters,
    Invitation, InvitationCreate, InvitationSearchFilters, InvitationResponse,
    Attachment, AttachmentCreate,
    MembershipAdd, MembershipRemove
)
from database import get_database_service, DatabaseServiceBase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Discussions Service API")
    settings = get_settings()
    logger.info(f"Mock DB mode: {settings.use_mock_db}")
    
    yield
    
    logger.info("Shutting down Discussions Service API")


# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Discussion service API for pet owners with Azure CosmosDB backend",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get database service
def get_db() -> DatabaseServiceBase:
    """Dependency to get database service instance"""
    return get_database_service()


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred"}
    )


# =============================================================================
# Health Endpoints
# =============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "healthy"
    }


@app.get("/health", tags=["Health"])
async def health_check(db: DatabaseServiceBase = Depends(get_db)):
    """Health check endpoint"""
    try:
        health = db.health_check()
        if health.get("status") != "healthy":
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=health
            )
        return health
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e)}
        )


# =============================================================================
# Room Endpoints
# =============================================================================

@app.post("/api/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED, tags=["Rooms"])
async def create_room(room_data: RoomCreate, db: DatabaseServiceBase = Depends(get_db)):
    """Create a new discussion room"""
    try:
        room = db.create_room(room_data)
        return RoomResponse.from_room(room)
    except Exception as e:
        logger.error(f"Failed to create room: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create room: {str(e)}"
        )


@app.get("/api/rooms", response_model=List[RoomResponse], tags=["Rooms"])
async def list_rooms(
    search: Optional[str] = Query(None, description="Search in name or description"),
    is_private: Optional[bool] = Query(None, description="Filter by privacy"),
    owner_id: Optional[str] = Query(None, description="Filter by owner"),
    member_id: Optional[str] = Query(None, description="Filter by member"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: DatabaseServiceBase = Depends(get_db)
):
    """List rooms with optional filters"""
    filters = RoomSearchFilters(
        search=search,
        is_private=is_private,
        owner_id=owner_id,
        member_id=member_id,
        limit=limit,
        offset=offset
    )
    rooms = db.list_rooms(filters)
    return [RoomResponse.from_room(room) for room in rooms]


@app.get("/api/rooms/{room_id}", response_model=RoomResponse, tags=["Rooms"])
async def get_room(room_id: str, db: DatabaseServiceBase = Depends(get_db)):
    """Get a specific room by ID"""
    room = db.get_room(room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room not found: {room_id}"
        )
    return RoomResponse.from_room(room)


@app.patch("/api/rooms/{room_id}", response_model=RoomResponse, tags=["Rooms"])
async def update_room(
    room_id: str,
    room_data: RoomUpdate,
    db: DatabaseServiceBase = Depends(get_db)
):
    """Update a room"""
    room = db.update_room(room_id, room_data)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room not found: {room_id}"
        )
    return RoomResponse.from_room(room)


@app.delete("/api/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Rooms"])
async def delete_room(room_id: str, db: DatabaseServiceBase = Depends(get_db)):
    """Delete a room and all associated data"""
    success = db.delete_room(room_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room not found: {room_id}"
        )
    return None


# =============================================================================
# Room Membership Endpoints
# =============================================================================

@app.post("/api/rooms/{room_id}/members", response_model=RoomResponse, tags=["Membership"])
async def add_member(
    room_id: str,
    membership: MembershipAdd,
    db: DatabaseServiceBase = Depends(get_db)
):
    """Add a member to a room"""
    room = db.add_member(room_id, membership.user_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room not found: {room_id}"
        )
    return RoomResponse.from_room(room)


@app.delete("/api/rooms/{room_id}/members/{user_id}", response_model=RoomResponse, tags=["Membership"])
async def remove_member(
    room_id: str,
    user_id: str,
    db: DatabaseServiceBase = Depends(get_db)
):
    """Remove a member from a room"""
    room = db.remove_member(room_id, user_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room not found: {room_id}"
        )
    return RoomResponse.from_room(room)


# =============================================================================
# Message Endpoints
# =============================================================================

@app.post("/api/messages", response_model=Message, status_code=status.HTTP_201_CREATED, tags=["Messages"])
async def create_message(
    message_data: MessageCreate,
    db: DatabaseServiceBase = Depends(get_db)
):
    """Create a new message in a room"""
    # Verify room exists
    room = db.get_room(message_data.room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room not found: {message_data.room_id}"
        )
    
    # Verify parent message exists if specified
    if message_data.parent_message_id:
        parent = db.get_message(message_data.parent_message_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent message not found: {message_data.parent_message_id}"
            )
        if parent.room_id != message_data.room_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent message must be in the same room"
            )
    
    try:
        message = db.create_message(message_data)
        return message
    except Exception as e:
        logger.error(f"Failed to create message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create message: {str(e)}"
        )


@app.get("/api/messages", response_model=List[Message], tags=["Messages"])
async def list_messages(
    room_id: Optional[str] = Query(None, description="Filter by room"),
    author_id: Optional[str] = Query(None, description="Filter by author"),
    search: Optional[str] = Query(None, description="Search in content"),
    parent_message_id: Optional[str] = Query(None, description="Filter by parent (thread)"),
    has_attachments: Optional[bool] = Query(None, description="Filter by attachment presence"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: DatabaseServiceBase = Depends(get_db)
):
    """List messages with optional filters"""
    filters = MessageSearchFilters(
        room_id=room_id,
        author_id=author_id,
        search=search,
        parent_message_id=parent_message_id,
        has_attachments=has_attachments,
        limit=limit,
        offset=offset
    )
    return db.list_messages(filters)


@app.get("/api/rooms/{room_id}/messages", response_model=List[Message], tags=["Messages"])
async def list_room_messages(
    room_id: str,
    author_id: Optional[str] = Query(None, description="Filter by author"),
    search: Optional[str] = Query(None, description="Search in content"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: DatabaseServiceBase = Depends(get_db)
):
    """List messages in a specific room"""
    # Verify room exists
    room = db.get_room(room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room not found: {room_id}"
        )
    
    filters = MessageSearchFilters(
        room_id=room_id,
        author_id=author_id,
        search=search,
        limit=limit,
        offset=offset
    )
    return db.list_messages(filters)


@app.get("/api/messages/{message_id}", response_model=Message, tags=["Messages"])
async def get_message(message_id: str, db: DatabaseServiceBase = Depends(get_db)):
    """Get a specific message by ID"""
    message = db.get_message(message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message not found: {message_id}"
        )
    return message


@app.get("/api/messages/{message_id}/replies", response_model=List[Message], tags=["Messages"])
async def get_message_replies(
    message_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: DatabaseServiceBase = Depends(get_db)
):
    """Get replies to a message (thread)"""
    message = db.get_message(message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message not found: {message_id}"
        )
    
    filters = MessageSearchFilters(
        parent_message_id=message_id,
        limit=limit,
        offset=offset
    )
    return db.list_messages(filters)


@app.patch("/api/messages/{message_id}", response_model=Message, tags=["Messages"])
async def update_message(
    message_id: str,
    message_data: MessageUpdate,
    db: DatabaseServiceBase = Depends(get_db)
):
    """Update a message"""
    message = db.update_message(message_id, message_data)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message not found: {message_id}"
        )
    return message


@app.delete("/api/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Messages"])
async def delete_message(message_id: str, db: DatabaseServiceBase = Depends(get_db)):
    """Delete a message"""
    success = db.delete_message(message_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message not found: {message_id}"
        )
    return None


# =============================================================================
# Invitation Endpoints
# =============================================================================

@app.post("/api/invitations", response_model=Invitation, status_code=status.HTTP_201_CREATED, tags=["Invitations"])
async def create_invitation(
    invitation_data: InvitationCreate,
    inviter_id: str = Query(..., description="User ID of the inviter"),
    db: DatabaseServiceBase = Depends(get_db)
):
    """Create a new invitation to a room"""
    # Verify room exists and is private
    room = db.get_room(invitation_data.room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room not found: {invitation_data.room_id}"
        )
    
    if not room.is_private:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitations are only needed for private rooms"
        )
    
    # Verify inviter is a member
    if inviter_id not in room.members:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only room members can send invitations"
        )
    
    # Check if invitee is already a member
    if invitation_data.invitee_id in room.members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this room"
        )
    
    try:
        invitation = db.create_invitation(invitation_data, inviter_id)
        return invitation
    except Exception as e:
        logger.error(f"Failed to create invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invitation: {str(e)}"
        )


@app.get("/api/invitations", response_model=List[Invitation], tags=["Invitations"])
async def list_invitations(
    room_id: Optional[str] = Query(None, description="Filter by room"),
    invitee_id: Optional[str] = Query(None, description="Filter by invitee"),
    inviter_id: Optional[str] = Query(None, description="Filter by inviter"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: DatabaseServiceBase = Depends(get_db)
):
    """List invitations with optional filters"""
    filters = InvitationSearchFilters(
        room_id=room_id,
        invitee_id=invitee_id,
        inviter_id=inviter_id,
        status=status_filter,
        limit=limit,
        offset=offset
    )
    return db.list_invitations(filters)


@app.get("/api/invitations/{invitation_id}", response_model=Invitation, tags=["Invitations"])
async def get_invitation(invitation_id: str, db: DatabaseServiceBase = Depends(get_db)):
    """Get a specific invitation by ID"""
    invitation = db.get_invitation(invitation_id)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invitation not found: {invitation_id}"
        )
    return invitation


@app.post("/api/invitations/{invitation_id}/respond", response_model=Invitation, tags=["Invitations"])
async def respond_to_invitation(
    invitation_id: str,
    response: InvitationResponse,
    db: DatabaseServiceBase = Depends(get_db)
):
    """Accept or decline an invitation"""
    invitation = db.get_invitation(invitation_id)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invitation not found: {invitation_id}"
        )
    
    if invitation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invitation has already been {invitation.status}"
        )
    
    accept = response.action == "accept"
    updated_invitation = db.respond_to_invitation(invitation_id, accept)
    
    if not updated_invitation:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to respond to invitation"
        )
    
    return updated_invitation


@app.delete("/api/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Invitations"])
async def delete_invitation(invitation_id: str, db: DatabaseServiceBase = Depends(get_db)):
    """Delete an invitation"""
    success = db.delete_invitation(invitation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invitation not found: {invitation_id}"
        )
    return None


# =============================================================================
# Attachment Endpoints
# =============================================================================

@app.post("/api/messages/{message_id}/attachments", response_model=Attachment, status_code=status.HTTP_201_CREATED, tags=["Attachments"])
async def create_attachment(
    message_id: str,
    attachment_data: AttachmentCreate,
    db: DatabaseServiceBase = Depends(get_db)
):
    """Add an attachment to a message"""
    message = db.get_message(message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message not found: {message_id}"
        )
    
    try:
        attachment = db.create_attachment(message_id, attachment_data)
        return attachment
    except Exception as e:
        logger.error(f"Failed to create attachment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create attachment: {str(e)}"
        )


@app.get("/api/messages/{message_id}/attachments", response_model=List[Attachment], tags=["Attachments"])
async def list_message_attachments(
    message_id: str,
    db: DatabaseServiceBase = Depends(get_db)
):
    """List attachments for a message"""
    message = db.get_message(message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message not found: {message_id}"
        )
    
    return db.list_attachments_for_message(message_id)


@app.get("/api/attachments/{attachment_id}", response_model=Attachment, tags=["Attachments"])
async def get_attachment(attachment_id: str, db: DatabaseServiceBase = Depends(get_db)):
    """Get a specific attachment by ID"""
    attachment = db.get_attachment(attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment not found: {attachment_id}"
        )
    return attachment


@app.delete("/api/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Attachments"])
async def delete_attachment(attachment_id: str, db: DatabaseServiceBase = Depends(get_db)):
    """Delete an attachment"""
    success = db.delete_attachment(attachment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment not found: {attachment_id}"
        )
    return None

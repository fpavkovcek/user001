"""
Database Service for Discussions Service

This module provides a service layer for interacting with Azure CosmosDB
following Azure best practices for authentication, error handling, and performance.

Supports both mock mode (for testing) and real CosmosDB connections.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from config import get_settings
from models import (
    Room, RoomCreate, RoomUpdate, RoomSearchFilters, RoomResponse,
    Message, MessageCreate, MessageUpdate, MessageSearchFilters,
    Invitation, InvitationCreate, InvitationSearchFilters,
    Attachment, AttachmentCreate
)

# Configure logging
logger = logging.getLogger(__name__)


class DatabaseServiceBase(ABC):
    """Abstract base class for database operations"""

    # Room operations
    @abstractmethod
    def create_room(self, room_data: RoomCreate) -> Room:
        pass

    @abstractmethod
    def get_room(self, room_id: str) -> Optional[Room]:
        pass

    @abstractmethod
    def update_room(self, room_id: str, room_data: RoomUpdate) -> Optional[Room]:
        pass

    @abstractmethod
    def delete_room(self, room_id: str) -> bool:
        pass

    @abstractmethod
    def list_rooms(self, filters: RoomSearchFilters) -> List[Room]:
        pass

    @abstractmethod
    def add_member(self, room_id: str, user_id: str) -> Optional[Room]:
        pass

    @abstractmethod
    def remove_member(self, room_id: str, user_id: str) -> Optional[Room]:
        pass

    # Message operations
    @abstractmethod
    def create_message(self, message_data: MessageCreate) -> Message:
        pass

    @abstractmethod
    def get_message(self, message_id: str) -> Optional[Message]:
        pass

    @abstractmethod
    def update_message(self, message_id: str, message_data: MessageUpdate) -> Optional[Message]:
        pass

    @abstractmethod
    def delete_message(self, message_id: str) -> bool:
        pass

    @abstractmethod
    def list_messages(self, filters: MessageSearchFilters) -> List[Message]:
        pass

    # Invitation operations
    @abstractmethod
    def create_invitation(self, invitation_data: InvitationCreate, inviter_id: str) -> Invitation:
        pass

    @abstractmethod
    def get_invitation(self, invitation_id: str) -> Optional[Invitation]:
        pass

    @abstractmethod
    def respond_to_invitation(self, invitation_id: str, accept: bool) -> Optional[Invitation]:
        pass

    @abstractmethod
    def list_invitations(self, filters: InvitationSearchFilters) -> List[Invitation]:
        pass

    @abstractmethod
    def delete_invitation(self, invitation_id: str) -> bool:
        pass

    # Attachment operations
    @abstractmethod
    def create_attachment(self, message_id: str, attachment_data: AttachmentCreate) -> Attachment:
        pass

    @abstractmethod
    def get_attachment(self, attachment_id: str) -> Optional[Attachment]:
        pass

    @abstractmethod
    def delete_attachment(self, attachment_id: str) -> bool:
        pass

    @abstractmethod
    def list_attachments_for_message(self, message_id: str) -> List[Attachment]:
        pass

    # Health check
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        pass


class MockDatabaseService(DatabaseServiceBase):
    """
    Mock database service for testing and development
    
    Stores data in memory for fast testing without CosmosDB dependency.
    """

    def __init__(self):
        self._rooms: Dict[str, Room] = {}
        self._messages: Dict[str, Message] = {}
        self._invitations: Dict[str, Invitation] = {}
        self._attachments: Dict[str, Attachment] = {}
        logger.info("MockDatabaseService initialized")

    def clear(self):
        """Clear all data (useful for testing)"""
        self._rooms.clear()
        self._messages.clear()
        self._invitations.clear()
        self._attachments.clear()

    # Room operations
    def create_room(self, room_data: RoomCreate) -> Room:
        room = Room(
            **room_data.model_dump(),
            members=[room_data.owner_id]  # Owner is automatically a member
        )
        self._rooms[room.id] = room
        logger.info(f"Created room: {room.id}")
        return room

    def get_room(self, room_id: str) -> Optional[Room]:
        return self._rooms.get(room_id)

    def update_room(self, room_id: str, room_data: RoomUpdate) -> Optional[Room]:
        room = self._rooms.get(room_id)
        if not room:
            return None
        
        update_data = room_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(room, key, value)
        room.updated_at = datetime.utcnow()
        
        self._rooms[room_id] = room
        logger.info(f"Updated room: {room_id}")
        return room

    def delete_room(self, room_id: str) -> bool:
        if room_id not in self._rooms:
            return False
        
        del self._rooms[room_id]
        
        # Also delete associated messages and invitations
        messages_to_delete = [m_id for m_id, m in self._messages.items() if m.room_id == room_id]
        for m_id in messages_to_delete:
            del self._messages[m_id]
        
        invitations_to_delete = [i_id for i_id, i in self._invitations.items() if i.room_id == room_id]
        for i_id in invitations_to_delete:
            del self._invitations[i_id]
        
        logger.info(f"Deleted room: {room_id}")
        return True

    def list_rooms(self, filters: RoomSearchFilters) -> List[Room]:
        rooms = list(self._rooms.values())
        
        # Apply filters
        if filters.search:
            search_lower = filters.search.lower()
            rooms = [r for r in rooms if 
                     search_lower in r.name.lower() or 
                     (r.description and search_lower in r.description.lower())]
        
        if filters.is_private is not None:
            rooms = [r for r in rooms if r.is_private == filters.is_private]
        
        if filters.owner_id:
            rooms = [r for r in rooms if r.owner_id == filters.owner_id]
        
        if filters.member_id:
            rooms = [r for r in rooms if filters.member_id in r.members]
        
        # Sort by created_at descending
        rooms.sort(key=lambda r: r.created_at, reverse=True)
        
        # Apply pagination
        return rooms[filters.offset:filters.offset + filters.limit]

    def add_member(self, room_id: str, user_id: str) -> Optional[Room]:
        room = self._rooms.get(room_id)
        if not room:
            return None
        
        if user_id not in room.members:
            room.members.append(user_id)
            room.updated_at = datetime.utcnow()
            self._rooms[room_id] = room
            logger.info(f"Added member {user_id} to room {room_id}")
        
        return room

    def remove_member(self, room_id: str, user_id: str) -> Optional[Room]:
        room = self._rooms.get(room_id)
        if not room:
            return None
        
        if user_id in room.members:
            room.members.remove(user_id)
            room.updated_at = datetime.utcnow()
            self._rooms[room_id] = room
            logger.info(f"Removed member {user_id} from room {room_id}")
        
        return room

    # Message operations
    def create_message(self, message_data: MessageCreate) -> Message:
        # Create attachments first
        attachments = []
        if message_data.attachments:
            for att_data in message_data.attachments:
                attachment = Attachment(
                    **att_data.model_dump(),
                    message_id=""  # Will be updated below
                )
                attachments.append(attachment)
        
        message = Message(
            content=message_data.content,
            author_id=message_data.author_id,
            room_id=message_data.room_id,
            parent_message_id=message_data.parent_message_id,
            attachments=[]
        )
        
        # Update attachment message_ids and store them
        for att in attachments:
            att.message_id = message.id
            self._attachments[att.id] = att
            message.attachments.append(att)
        
        self._messages[message.id] = message
        
        # Update reply count on parent message if this is a reply
        if message_data.parent_message_id:
            parent = self._messages.get(message_data.parent_message_id)
            if parent:
                parent.reply_count += 1
                self._messages[parent.id] = parent
        
        logger.info(f"Created message: {message.id}")
        return message

    def get_message(self, message_id: str) -> Optional[Message]:
        return self._messages.get(message_id)

    def update_message(self, message_id: str, message_data: MessageUpdate) -> Optional[Message]:
        message = self._messages.get(message_id)
        if not message:
            return None
        
        update_data = message_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(message, key, value)
        message.updated_at = datetime.utcnow()
        message.is_edited = True
        
        self._messages[message_id] = message
        logger.info(f"Updated message: {message_id}")
        return message

    def delete_message(self, message_id: str) -> bool:
        if message_id not in self._messages:
            return False
        
        message = self._messages[message_id]
        
        # Update parent reply count if this was a reply
        if message.parent_message_id:
            parent = self._messages.get(message.parent_message_id)
            if parent:
                parent.reply_count = max(0, parent.reply_count - 1)
                self._messages[parent.id] = parent
        
        # Delete associated attachments
        attachments_to_delete = [a_id for a_id, a in self._attachments.items() if a.message_id == message_id]
        for a_id in attachments_to_delete:
            del self._attachments[a_id]
        
        del self._messages[message_id]
        logger.info(f"Deleted message: {message_id}")
        return True

    def list_messages(self, filters: MessageSearchFilters) -> List[Message]:
        messages = list(self._messages.values())
        
        # Apply filters
        if filters.room_id:
            messages = [m for m in messages if m.room_id == filters.room_id]
        
        if filters.author_id:
            messages = [m for m in messages if m.author_id == filters.author_id]
        
        if filters.search:
            search_lower = filters.search.lower()
            messages = [m for m in messages if search_lower in m.content.lower()]
        
        if filters.parent_message_id is not None:
            # Filter for thread replies (or top-level messages if None)
            messages = [m for m in messages if m.parent_message_id == filters.parent_message_id]
        
        if filters.has_attachments is not None:
            if filters.has_attachments:
                messages = [m for m in messages if len(m.attachments) > 0]
            else:
                messages = [m for m in messages if len(m.attachments) == 0]
        
        # Sort by created_at ascending (chronological order for messages)
        messages.sort(key=lambda m: m.created_at)
        
        # Apply pagination
        return messages[filters.offset:filters.offset + filters.limit]

    # Invitation operations
    def create_invitation(self, invitation_data: InvitationCreate, inviter_id: str) -> Invitation:
        invitation = Invitation(
            room_id=invitation_data.room_id,
            invitee_id=invitation_data.invitee_id,
            inviter_id=inviter_id,
            message=invitation_data.message
        )
        self._invitations[invitation.id] = invitation
        logger.info(f"Created invitation: {invitation.id}")
        return invitation

    def get_invitation(self, invitation_id: str) -> Optional[Invitation]:
        return self._invitations.get(invitation_id)

    def respond_to_invitation(self, invitation_id: str, accept: bool) -> Optional[Invitation]:
        invitation = self._invitations.get(invitation_id)
        if not invitation:
            return None
        
        if invitation.status != "pending":
            return invitation  # Already responded
        
        invitation.status = "accepted" if accept else "declined"
        invitation.responded_at = datetime.utcnow()
        self._invitations[invitation_id] = invitation
        
        # If accepted, add user to room
        if accept:
            self.add_member(invitation.room_id, invitation.invitee_id)
        
        logger.info(f"Responded to invitation {invitation_id}: {'accepted' if accept else 'declined'}")
        return invitation

    def list_invitations(self, filters: InvitationSearchFilters) -> List[Invitation]:
        invitations = list(self._invitations.values())
        
        # Apply filters
        if filters.room_id:
            invitations = [i for i in invitations if i.room_id == filters.room_id]
        
        if filters.invitee_id:
            invitations = [i for i in invitations if i.invitee_id == filters.invitee_id]
        
        if filters.inviter_id:
            invitations = [i for i in invitations if i.inviter_id == filters.inviter_id]
        
        if filters.status:
            invitations = [i for i in invitations if i.status == filters.status]
        
        # Sort by created_at descending
        invitations.sort(key=lambda i: i.created_at, reverse=True)
        
        # Apply pagination
        return invitations[filters.offset:filters.offset + filters.limit]

    def delete_invitation(self, invitation_id: str) -> bool:
        if invitation_id not in self._invitations:
            return False
        
        del self._invitations[invitation_id]
        logger.info(f"Deleted invitation: {invitation_id}")
        return True

    # Attachment operations
    def create_attachment(self, message_id: str, attachment_data: AttachmentCreate) -> Attachment:
        attachment = Attachment(
            **attachment_data.model_dump(),
            message_id=message_id
        )
        self._attachments[attachment.id] = attachment
        
        # Add to message
        message = self._messages.get(message_id)
        if message:
            message.attachments.append(attachment)
            self._messages[message_id] = message
        
        logger.info(f"Created attachment: {attachment.id}")
        return attachment

    def get_attachment(self, attachment_id: str) -> Optional[Attachment]:
        return self._attachments.get(attachment_id)

    def delete_attachment(self, attachment_id: str) -> bool:
        if attachment_id not in self._attachments:
            return False
        
        attachment = self._attachments[attachment_id]
        
        # Remove from message
        message = self._messages.get(attachment.message_id)
        if message:
            message.attachments = [a for a in message.attachments if a.id != attachment_id]
            self._messages[message.id] = message
        
        del self._attachments[attachment_id]
        logger.info(f"Deleted attachment: {attachment_id}")
        return True

    def list_attachments_for_message(self, message_id: str) -> List[Attachment]:
        return [a for a in self._attachments.values() if a.message_id == message_id]

    # Health check
    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "database": "mock",
            "rooms_count": len(self._rooms),
            "messages_count": len(self._messages),
            "invitations_count": len(self._invitations),
            "attachments_count": len(self._attachments)
        }


class CosmosDBService(DatabaseServiceBase):
    """
    CosmosDB service for production use
    
    Implements Azure best practices:
    - Uses key-based authentication for local dev, Entra ID for Azure
    - Implements proper error handling and retry logic
    - Uses connection pooling and proper resource management
    """

    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.database = None
        self.rooms_container = None
        self.messages_container = None
        self.invitations_container = None
        self.attachments_container = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of CosmosDB client and containers"""
        if self._initialized:
            return

        try:
            from azure.cosmos import CosmosClient, PartitionKey
            from azure.identity import DefaultAzureCredential

            logger.info("Initializing CosmosDB connection")

            # Build client options based on environment
            if self.settings.is_local:
                logger.info("Using key-based authentication (local development)")
                
                # Check if SSL verification should be disabled (for emulator)
                disable_ssl_verify = os.getenv(
                    "COSMOS_EMULATOR_DISABLE_SSL_VERIFY", "0").lower() in ("1", "true", "yes")
                
                client_options = {
                    "url": self.settings.cosmos_endpoint,
                    "credential": self.settings.cosmos_key,
                }
                
                if disable_ssl_verify:
                    client_options["connection_verify"] = False
                    logger.warning("SSL verification disabled (emulator mode)")
                
                self.client = CosmosClient(**client_options)
            else:
                logger.info("Using Entra ID authentication (Azure)")
                credential = DefaultAzureCredential()
                self.client = CosmosClient(
                    url=self.settings.cosmos_endpoint,
                    credential=credential
                )

            # Get or create database
            self.database = self.client.create_database_if_not_exists(
                id=self.settings.cosmos_database_name
            )
            logger.info(f"Connected to database: {self.settings.cosmos_database_name}")

            # Get or create containers with appropriate partition keys
            self.rooms_container = self.database.create_container_if_not_exists(
                id=self.settings.cosmos_rooms_container,
                partition_key=PartitionKey(path="/id")
            )
            
            self.messages_container = self.database.create_container_if_not_exists(
                id=self.settings.cosmos_messages_container,
                partition_key=PartitionKey(path="/room_id")
            )
            
            self.invitations_container = self.database.create_container_if_not_exists(
                id=self.settings.cosmos_invitations_container,
                partition_key=PartitionKey(path="/room_id")
            )
            
            self.attachments_container = self.database.create_container_if_not_exists(
                id=self.settings.cosmos_attachments_container,
                partition_key=PartitionKey(path="/message_id")
            )

            logger.info("All containers initialized successfully")
            self._initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize CosmosDB: {e}")
            raise

    # Room operations
    def create_room(self, room_data: RoomCreate) -> Room:
        self._ensure_initialized()
        
        room = Room(
            **room_data.model_dump(),
            members=[room_data.owner_id]
        )
        
        room_dict = room.model_dump()
        room_dict["created_at"] = room.created_at.isoformat()
        room_dict["updated_at"] = room.updated_at.isoformat()
        
        self.rooms_container.create_item(room_dict)
        logger.info(f"Created room in CosmosDB: {room.id}")
        return room

    def get_room(self, room_id: str) -> Optional[Room]:
        self._ensure_initialized()
        
        try:
            item = self.rooms_container.read_item(item=room_id, partition_key=room_id)
            return self._dict_to_room(item)
        except Exception as e:
            logger.debug(f"Room not found: {room_id}")
            return None

    def _dict_to_room(self, item: Dict) -> Room:
        """Convert CosmosDB document to Room model"""
        if isinstance(item.get("created_at"), str):
            item["created_at"] = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
        if isinstance(item.get("updated_at"), str):
            item["updated_at"] = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
        return Room(**item)

    def update_room(self, room_id: str, room_data: RoomUpdate) -> Optional[Room]:
        self._ensure_initialized()
        
        room = self.get_room(room_id)
        if not room:
            return None
        
        update_data = room_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(room, key, value)
        room.updated_at = datetime.utcnow()
        
        room_dict = room.model_dump()
        room_dict["created_at"] = room.created_at.isoformat()
        room_dict["updated_at"] = room.updated_at.isoformat()
        
        self.rooms_container.replace_item(item=room_id, body=room_dict)
        logger.info(f"Updated room in CosmosDB: {room_id}")
        return room

    def delete_room(self, room_id: str) -> bool:
        self._ensure_initialized()
        
        try:
            self.rooms_container.delete_item(item=room_id, partition_key=room_id)
            
            # Delete associated messages
            query = "SELECT * FROM c WHERE c.room_id = @room_id"
            params = [{"name": "@room_id", "value": room_id}]
            messages = list(self.messages_container.query_items(query, parameters=params))
            for msg in messages:
                self.messages_container.delete_item(item=msg["id"], partition_key=room_id)
            
            # Delete associated invitations
            invitations = list(self.invitations_container.query_items(query, parameters=params))
            for inv in invitations:
                self.invitations_container.delete_item(item=inv["id"], partition_key=room_id)
            
            logger.info(f"Deleted room from CosmosDB: {room_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete room: {e}")
            return False

    def list_rooms(self, filters: RoomSearchFilters) -> List[Room]:
        self._ensure_initialized()
        
        query_parts = ["SELECT * FROM c"]
        conditions = []
        params = []
        
        if filters.is_private is not None:
            conditions.append("c.is_private = @is_private")
            params.append({"name": "@is_private", "value": filters.is_private})
        
        if filters.owner_id:
            conditions.append("c.owner_id = @owner_id")
            params.append({"name": "@owner_id", "value": filters.owner_id})
        
        if filters.member_id:
            conditions.append("ARRAY_CONTAINS(c.members, @member_id)")
            params.append({"name": "@member_id", "value": filters.member_id})
        
        if filters.search:
            conditions.append("(CONTAINS(LOWER(c.name), @search) OR CONTAINS(LOWER(c.description), @search))")
            params.append({"name": "@search", "value": filters.search.lower()})
        
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
        
        query_parts.append("ORDER BY c.created_at DESC")
        query_parts.append(f"OFFSET {filters.offset} LIMIT {filters.limit}")
        
        query = " ".join(query_parts)
        items = list(self.rooms_container.query_items(query, parameters=params, enable_cross_partition_query=True))
        
        return [self._dict_to_room(item) for item in items]

    def add_member(self, room_id: str, user_id: str) -> Optional[Room]:
        room = self.get_room(room_id)
        if not room:
            return None
        
        if user_id not in room.members:
            room.members.append(user_id)
            room.updated_at = datetime.utcnow()
            
            room_dict = room.model_dump()
            room_dict["created_at"] = room.created_at.isoformat()
            room_dict["updated_at"] = room.updated_at.isoformat()
            
            self.rooms_container.replace_item(item=room_id, body=room_dict)
            logger.info(f"Added member {user_id} to room {room_id}")
        
        return room

    def remove_member(self, room_id: str, user_id: str) -> Optional[Room]:
        room = self.get_room(room_id)
        if not room:
            return None
        
        if user_id in room.members:
            room.members.remove(user_id)
            room.updated_at = datetime.utcnow()
            
            room_dict = room.model_dump()
            room_dict["created_at"] = room.created_at.isoformat()
            room_dict["updated_at"] = room.updated_at.isoformat()
            
            self.rooms_container.replace_item(item=room_id, body=room_dict)
            logger.info(f"Removed member {user_id} from room {room_id}")
        
        return room

    # Message operations
    def create_message(self, message_data: MessageCreate) -> Message:
        self._ensure_initialized()
        
        message = Message(
            content=message_data.content,
            author_id=message_data.author_id,
            room_id=message_data.room_id,
            parent_message_id=message_data.parent_message_id,
            attachments=[]
        )
        
        # Handle attachments
        if message_data.attachments:
            for att_data in message_data.attachments:
                attachment = Attachment(
                    **att_data.model_dump(),
                    message_id=message.id
                )
                message.attachments.append(attachment)
                
                # Store attachment separately
                att_dict = attachment.model_dump()
                att_dict["uploaded_at"] = attachment.uploaded_at.isoformat()
                self.attachments_container.create_item(att_dict)
        
        msg_dict = message.model_dump()
        msg_dict["created_at"] = message.created_at.isoformat()
        msg_dict["updated_at"] = message.updated_at.isoformat()
        # Convert attachments
        msg_dict["attachments"] = [
            {**a.model_dump(), "uploaded_at": a.uploaded_at.isoformat()} 
            for a in message.attachments
        ]
        
        self.messages_container.create_item(msg_dict)
        
        # Update parent reply count
        if message_data.parent_message_id:
            parent = self.get_message(message_data.parent_message_id)
            if parent:
                parent.reply_count += 1
                self._update_message_internal(parent)
        
        logger.info(f"Created message in CosmosDB: {message.id}")
        return message

    def _update_message_internal(self, message: Message):
        """Internal method to update message in CosmosDB"""
        msg_dict = message.model_dump()
        msg_dict["created_at"] = message.created_at.isoformat()
        msg_dict["updated_at"] = message.updated_at.isoformat()
        msg_dict["attachments"] = [
            {**a.model_dump(), "uploaded_at": a.uploaded_at.isoformat()} 
            for a in message.attachments
        ]
        self.messages_container.replace_item(item=message.id, body=msg_dict)

    def get_message(self, message_id: str) -> Optional[Message]:
        self._ensure_initialized()
        
        try:
            # Need cross-partition query since we don't know room_id
            query = "SELECT * FROM c WHERE c.id = @id"
            params = [{"name": "@id", "value": message_id}]
            items = list(self.messages_container.query_items(
                query, parameters=params, enable_cross_partition_query=True
            ))
            if items:
                return self._dict_to_message(items[0])
            return None
        except Exception as e:
            logger.debug(f"Message not found: {message_id}")
            return None

    def _dict_to_message(self, item: Dict) -> Message:
        """Convert CosmosDB document to Message model"""
        if isinstance(item.get("created_at"), str):
            item["created_at"] = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
        if isinstance(item.get("updated_at"), str):
            item["updated_at"] = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
        
        # Convert attachments
        attachments = []
        for att in item.get("attachments", []):
            if isinstance(att.get("uploaded_at"), str):
                att["uploaded_at"] = datetime.fromisoformat(att["uploaded_at"].replace("Z", "+00:00"))
            attachments.append(Attachment(**att))
        item["attachments"] = attachments
        
        return Message(**item)

    def update_message(self, message_id: str, message_data: MessageUpdate) -> Optional[Message]:
        self._ensure_initialized()
        
        message = self.get_message(message_id)
        if not message:
            return None
        
        update_data = message_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(message, key, value)
        message.updated_at = datetime.utcnow()
        message.is_edited = True
        
        self._update_message_internal(message)
        logger.info(f"Updated message in CosmosDB: {message_id}")
        return message

    def delete_message(self, message_id: str) -> bool:
        self._ensure_initialized()
        
        try:
            message = self.get_message(message_id)
            if not message:
                return False
            
            # Update parent reply count
            if message.parent_message_id:
                parent = self.get_message(message.parent_message_id)
                if parent:
                    parent.reply_count = max(0, parent.reply_count - 1)
                    self._update_message_internal(parent)
            
            # Delete attachments
            for att in message.attachments:
                try:
                    self.attachments_container.delete_item(item=att.id, partition_key=message_id)
                except Exception:
                    pass
            
            # Delete message
            self.messages_container.delete_item(item=message_id, partition_key=message.room_id)
            logger.info(f"Deleted message from CosmosDB: {message_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")
            return False

    def list_messages(self, filters: MessageSearchFilters) -> List[Message]:
        self._ensure_initialized()
        
        query_parts = ["SELECT * FROM c"]
        conditions = []
        params = []
        
        if filters.room_id:
            conditions.append("c.room_id = @room_id")
            params.append({"name": "@room_id", "value": filters.room_id})
        
        if filters.author_id:
            conditions.append("c.author_id = @author_id")
            params.append({"name": "@author_id", "value": filters.author_id})
        
        if filters.search:
            conditions.append("CONTAINS(LOWER(c.content), @search)")
            params.append({"name": "@search", "value": filters.search.lower()})
        
        if filters.parent_message_id is not None:
            if filters.parent_message_id:
                conditions.append("c.parent_message_id = @parent_id")
                params.append({"name": "@parent_id", "value": filters.parent_message_id})
            else:
                conditions.append("(NOT IS_DEFINED(c.parent_message_id) OR c.parent_message_id = null)")
        
        if filters.has_attachments is not None:
            if filters.has_attachments:
                conditions.append("ARRAY_LENGTH(c.attachments) > 0")
            else:
                conditions.append("(NOT IS_DEFINED(c.attachments) OR ARRAY_LENGTH(c.attachments) = 0)")
        
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
        
        query_parts.append("ORDER BY c.created_at ASC")
        query_parts.append(f"OFFSET {filters.offset} LIMIT {filters.limit}")
        
        query = " ".join(query_parts)
        items = list(self.messages_container.query_items(
            query, parameters=params, enable_cross_partition_query=True
        ))
        
        return [self._dict_to_message(item) for item in items]

    # Invitation operations
    def create_invitation(self, invitation_data: InvitationCreate, inviter_id: str) -> Invitation:
        self._ensure_initialized()
        
        invitation = Invitation(
            room_id=invitation_data.room_id,
            invitee_id=invitation_data.invitee_id,
            inviter_id=inviter_id,
            message=invitation_data.message
        )
        
        inv_dict = invitation.model_dump()
        inv_dict["created_at"] = invitation.created_at.isoformat()
        if invitation.responded_at:
            inv_dict["responded_at"] = invitation.responded_at.isoformat()
        if invitation.expires_at:
            inv_dict["expires_at"] = invitation.expires_at.isoformat()
        
        self.invitations_container.create_item(inv_dict)
        logger.info(f"Created invitation in CosmosDB: {invitation.id}")
        return invitation

    def get_invitation(self, invitation_id: str) -> Optional[Invitation]:
        self._ensure_initialized()
        
        try:
            query = "SELECT * FROM c WHERE c.id = @id"
            params = [{"name": "@id", "value": invitation_id}]
            items = list(self.invitations_container.query_items(
                query, parameters=params, enable_cross_partition_query=True
            ))
            if items:
                return self._dict_to_invitation(items[0])
            return None
        except Exception:
            return None

    def _dict_to_invitation(self, item: Dict) -> Invitation:
        """Convert CosmosDB document to Invitation model"""
        if isinstance(item.get("created_at"), str):
            item["created_at"] = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
        if isinstance(item.get("responded_at"), str):
            item["responded_at"] = datetime.fromisoformat(item["responded_at"].replace("Z", "+00:00"))
        if isinstance(item.get("expires_at"), str):
            item["expires_at"] = datetime.fromisoformat(item["expires_at"].replace("Z", "+00:00"))
        return Invitation(**item)

    def respond_to_invitation(self, invitation_id: str, accept: bool) -> Optional[Invitation]:
        self._ensure_initialized()
        
        invitation = self.get_invitation(invitation_id)
        if not invitation or invitation.status != "pending":
            return invitation
        
        invitation.status = "accepted" if accept else "declined"
        invitation.responded_at = datetime.utcnow()
        
        inv_dict = invitation.model_dump()
        inv_dict["created_at"] = invitation.created_at.isoformat()
        inv_dict["responded_at"] = invitation.responded_at.isoformat()
        if invitation.expires_at:
            inv_dict["expires_at"] = invitation.expires_at.isoformat()
        
        self.invitations_container.replace_item(item=invitation_id, body=inv_dict)
        
        if accept:
            self.add_member(invitation.room_id, invitation.invitee_id)
        
        logger.info(f"Responded to invitation {invitation_id}: {'accepted' if accept else 'declined'}")
        return invitation

    def list_invitations(self, filters: InvitationSearchFilters) -> List[Invitation]:
        self._ensure_initialized()
        
        query_parts = ["SELECT * FROM c"]
        conditions = []
        params = []
        
        if filters.room_id:
            conditions.append("c.room_id = @room_id")
            params.append({"name": "@room_id", "value": filters.room_id})
        
        if filters.invitee_id:
            conditions.append("c.invitee_id = @invitee_id")
            params.append({"name": "@invitee_id", "value": filters.invitee_id})
        
        if filters.inviter_id:
            conditions.append("c.inviter_id = @inviter_id")
            params.append({"name": "@inviter_id", "value": filters.inviter_id})
        
        if filters.status:
            conditions.append("c.status = @status")
            params.append({"name": "@status", "value": filters.status})
        
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
        
        query_parts.append("ORDER BY c.created_at DESC")
        query_parts.append(f"OFFSET {filters.offset} LIMIT {filters.limit}")
        
        query = " ".join(query_parts)
        items = list(self.invitations_container.query_items(
            query, parameters=params, enable_cross_partition_query=True
        ))
        
        return [self._dict_to_invitation(item) for item in items]

    def delete_invitation(self, invitation_id: str) -> bool:
        self._ensure_initialized()
        
        try:
            invitation = self.get_invitation(invitation_id)
            if not invitation:
                return False
            
            self.invitations_container.delete_item(
                item=invitation_id, partition_key=invitation.room_id
            )
            logger.info(f"Deleted invitation from CosmosDB: {invitation_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete invitation: {e}")
            return False

    # Attachment operations
    def create_attachment(self, message_id: str, attachment_data: AttachmentCreate) -> Attachment:
        self._ensure_initialized()
        
        attachment = Attachment(
            **attachment_data.model_dump(),
            message_id=message_id
        )
        
        att_dict = attachment.model_dump()
        att_dict["uploaded_at"] = attachment.uploaded_at.isoformat()
        
        self.attachments_container.create_item(att_dict)
        
        # Add to message
        message = self.get_message(message_id)
        if message:
            message.attachments.append(attachment)
            self._update_message_internal(message)
        
        logger.info(f"Created attachment in CosmosDB: {attachment.id}")
        return attachment

    def get_attachment(self, attachment_id: str) -> Optional[Attachment]:
        self._ensure_initialized()
        
        try:
            query = "SELECT * FROM c WHERE c.id = @id"
            params = [{"name": "@id", "value": attachment_id}]
            items = list(self.attachments_container.query_items(
                query, parameters=params, enable_cross_partition_query=True
            ))
            if items:
                item = items[0]
                if isinstance(item.get("uploaded_at"), str):
                    item["uploaded_at"] = datetime.fromisoformat(item["uploaded_at"].replace("Z", "+00:00"))
                return Attachment(**item)
            return None
        except Exception:
            return None

    def delete_attachment(self, attachment_id: str) -> bool:
        self._ensure_initialized()
        
        try:
            attachment = self.get_attachment(attachment_id)
            if not attachment:
                return False
            
            # Remove from message
            message = self.get_message(attachment.message_id)
            if message:
                message.attachments = [a for a in message.attachments if a.id != attachment_id]
                self._update_message_internal(message)
            
            self.attachments_container.delete_item(
                item=attachment_id, partition_key=attachment.message_id
            )
            logger.info(f"Deleted attachment from CosmosDB: {attachment_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete attachment: {e}")
            return False

    def list_attachments_for_message(self, message_id: str) -> List[Attachment]:
        self._ensure_initialized()
        
        query = "SELECT * FROM c WHERE c.message_id = @message_id"
        params = [{"name": "@message_id", "value": message_id}]
        items = list(self.attachments_container.query_items(
            query, parameters=params
        ))
        
        attachments = []
        for item in items:
            if isinstance(item.get("uploaded_at"), str):
                item["uploaded_at"] = datetime.fromisoformat(item["uploaded_at"].replace("Z", "+00:00"))
            attachments.append(Attachment(**item))
        
        return attachments

    # Health check
    def health_check(self) -> Dict[str, Any]:
        self._ensure_initialized()
        
        try:
            # Simple query to verify connection
            list(self.rooms_container.query_items(
                "SELECT VALUE COUNT(1) FROM c",
                enable_cross_partition_query=True
            ))
            
            return {
                "status": "healthy",
                "database": self.settings.cosmos_database_name,
                "connection": "cosmos"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global service instances
_mock_service: Optional[MockDatabaseService] = None
_cosmos_service: Optional[CosmosDBService] = None


def get_database_service() -> DatabaseServiceBase:
    """Get the appropriate database service based on configuration"""
    global _mock_service, _cosmos_service
    
    settings = get_settings()
    
    if settings.use_mock_db:
        if _mock_service is None:
            _mock_service = MockDatabaseService()
        return _mock_service
    else:
        if _cosmos_service is None:
            _cosmos_service = CosmosDBService()
        return _cosmos_service


def get_mock_service() -> MockDatabaseService:
    """Get mock service instance (for testing)"""
    global _mock_service
    if _mock_service is None:
        _mock_service = MockDatabaseService()
    return _mock_service


def reset_mock_service():
    """Reset mock service (for testing)"""
    global _mock_service
    if _mock_service:
        _mock_service.clear()

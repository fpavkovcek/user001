"""
Unit Tests for Discussions Service API

Run with: python -m pytest test_main.py -v

These tests use the mock database service to test API endpoints
without requiring a real CosmosDB connection.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os

# Set mock mode before importing app
os.environ["USE_MOCK_DB"] = "true"

from main import app
from database import get_mock_service, reset_mock_service
from models import Room, Message, Invitation, Attachment


client = TestClient(app)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def reset_database():
    """Reset mock database before each test"""
    reset_mock_service()
    yield


@pytest.fixture
def sample_room_data():
    """Sample room creation data"""
    return {
        "name": "Pet Lovers Chat",
        "description": "A room for pet enthusiasts to share stories",
        "is_private": False,
        "owner_id": "user-001"
    }


@pytest.fixture
def sample_private_room_data():
    """Sample private room creation data"""
    return {
        "name": "VIP Pet Club",
        "description": "Exclusive discussions for premium members",
        "is_private": True,
        "owner_id": "user-001"
    }


@pytest.fixture
def sample_message_data():
    """Sample message creation data"""
    return {
        "content": "Hello everyone! My dog just learned a new trick!",
        "author_id": "user-001",
        "room_id": ""  # Will be set in tests
    }


@pytest.fixture
def sample_attachment_data():
    """Sample attachment creation data"""
    return {
        "filename": "my_pet.jpg",
        "content_type": "image/jpeg",
        "size_bytes": 102400,
        "url": "https://storage.example.com/attachments/my_pet.jpg"
    }


@pytest.fixture
def created_room(sample_room_data):
    """Create a room and return its data"""
    response = client.post("/api/rooms", json=sample_room_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def created_private_room(sample_private_room_data):
    """Create a private room and return its data"""
    response = client.post("/api/rooms", json=sample_private_room_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def created_message(created_room, sample_message_data):
    """Create a message in a room and return its data"""
    sample_message_data["room_id"] = created_room["id"]
    response = client.post("/api/messages", json=sample_message_data)
    assert response.status_code == 201
    return response.json()


# =============================================================================
# Health Endpoint Tests
# =============================================================================

class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root_endpoint(self):
        """Test root endpoint returns welcome message"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["status"] == "healthy"
        assert "Discussions Service" in data["message"]

    def test_health_check_success(self):
        """Test health check returns healthy status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "mock"


# =============================================================================
# Room CRUD Tests
# =============================================================================

class TestRoomCRUD:
    """Test room CRUD operations"""

    def test_create_room_success(self, sample_room_data):
        """Test successful room creation"""
        response = client.post("/api/rooms", json=sample_room_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == sample_room_data["name"]
        assert data["description"] == sample_room_data["description"]
        assert data["is_private"] == sample_room_data["is_private"]
        assert data["owner_id"] == sample_room_data["owner_id"]
        assert "id" in data
        assert "created_at" in data
        assert "member_count" in data
        assert data["member_count"] == 1  # Owner is automatically a member

    def test_create_private_room(self, sample_private_room_data):
        """Test creating a private room"""
        response = client.post("/api/rooms", json=sample_private_room_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["is_private"] is True

    def test_create_room_missing_required_field(self):
        """Test room creation fails with missing required field"""
        invalid_data = {"name": "Test Room"}  # Missing owner_id
        response = client.post("/api/rooms", json=invalid_data)
        assert response.status_code == 422

    def test_create_room_invalid_name(self):
        """Test room creation fails with invalid name"""
        invalid_data = {
            "name": "",  # Empty name
            "owner_id": "user-001"
        }
        response = client.post("/api/rooms", json=invalid_data)
        assert response.status_code == 422

    def test_get_room_success(self, created_room):
        """Test successful room retrieval"""
        room_id = created_room["id"]
        response = client.get(f"/api/rooms/{room_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == room_id
        assert data["name"] == created_room["name"]

    def test_get_room_not_found(self):
        """Test room retrieval for non-existent room"""
        response = client.get("/api/rooms/nonexistent-id")
        assert response.status_code == 404

    def test_update_room_success(self, created_room):
        """Test successful room update"""
        room_id = created_room["id"]
        update_data = {"name": "Updated Room Name", "description": "New description"}
        
        response = client.patch(f"/api/rooms/{room_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Updated Room Name"
        assert data["description"] == "New description"

    def test_update_room_partial(self, created_room):
        """Test partial room update"""
        room_id = created_room["id"]
        update_data = {"description": "Only updating description"}
        
        response = client.patch(f"/api/rooms/{room_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == created_room["name"]  # Unchanged
        assert data["description"] == "Only updating description"

    def test_update_room_not_found(self):
        """Test room update for non-existent room"""
        response = client.patch("/api/rooms/nonexistent-id", json={"name": "Test"})
        assert response.status_code == 404

    def test_delete_room_success(self, created_room):
        """Test successful room deletion"""
        room_id = created_room["id"]
        response = client.delete(f"/api/rooms/{room_id}")
        assert response.status_code == 204
        
        # Verify room is deleted
        response = client.get(f"/api/rooms/{room_id}")
        assert response.status_code == 404

    def test_delete_room_not_found(self):
        """Test room deletion for non-existent room"""
        response = client.delete("/api/rooms/nonexistent-id")
        assert response.status_code == 404

    def test_list_rooms_empty(self):
        """Test listing rooms when empty"""
        response = client.get("/api/rooms")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_rooms_with_data(self, sample_room_data):
        """Test listing rooms with data"""
        # Create multiple rooms
        for i in range(3):
            room_data = {**sample_room_data, "name": f"Room {i}"}
            client.post("/api/rooms", json=room_data)
        
        response = client.get("/api/rooms")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_rooms_with_filters(self, sample_room_data, sample_private_room_data):
        """Test listing rooms with filters"""
        client.post("/api/rooms", json=sample_room_data)
        client.post("/api/rooms", json=sample_private_room_data)
        
        # Filter by privacy
        response = client.get("/api/rooms?is_private=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_private"] is True

    def test_list_rooms_with_search(self, sample_room_data):
        """Test listing rooms with search"""
        client.post("/api/rooms", json=sample_room_data)
        
        response = client.get("/api/rooms?search=Pet%20Lovers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_list_rooms_pagination(self, sample_room_data):
        """Test room listing pagination"""
        # Create 5 rooms
        for i in range(5):
            room_data = {**sample_room_data, "name": f"Room {i}"}
            client.post("/api/rooms", json=room_data)
        
        # Get first 2
        response = client.get("/api/rooms?limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2
        
        # Get next 2
        response = client.get("/api/rooms?limit=2&offset=2")
        assert response.status_code == 200
        assert len(response.json()) == 2


# =============================================================================
# Room Membership Tests
# =============================================================================

class TestRoomMembership:
    """Test room membership operations"""

    def test_add_member_success(self, created_room):
        """Test successfully adding a member"""
        room_id = created_room["id"]
        
        response = client.post(
            f"/api/rooms/{room_id}/members",
            json={"user_id": "user-002"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["member_count"] == 2
        assert "user-002" in data["members"]

    def test_add_member_already_exists(self, created_room):
        """Test adding a member who is already in the room"""
        room_id = created_room["id"]
        owner_id = created_room["owner_id"]
        
        response = client.post(
            f"/api/rooms/{room_id}/members",
            json={"user_id": owner_id}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["member_count"] == 1  # Still just one member

    def test_add_member_room_not_found(self):
        """Test adding member to non-existent room"""
        response = client.post(
            "/api/rooms/nonexistent-id/members",
            json={"user_id": "user-002"}
        )
        assert response.status_code == 404

    def test_remove_member_success(self, created_room):
        """Test successfully removing a member"""
        room_id = created_room["id"]
        
        # First add a member
        client.post(f"/api/rooms/{room_id}/members", json={"user_id": "user-002"})
        
        # Then remove them
        response = client.delete(f"/api/rooms/{room_id}/members/user-002")
        assert response.status_code == 200
        
        data = response.json()
        assert data["member_count"] == 1
        assert "user-002" not in data["members"]

    def test_remove_member_room_not_found(self):
        """Test removing member from non-existent room"""
        response = client.delete("/api/rooms/nonexistent-id/members/user-002")
        assert response.status_code == 404


# =============================================================================
# Message CRUD Tests
# =============================================================================

class TestMessageCRUD:
    """Test message CRUD operations"""

    def test_create_message_success(self, created_room, sample_message_data):
        """Test successful message creation"""
        sample_message_data["room_id"] = created_room["id"]
        
        response = client.post("/api/messages", json=sample_message_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["content"] == sample_message_data["content"]
        assert data["author_id"] == sample_message_data["author_id"]
        assert data["room_id"] == created_room["id"]
        assert "id" in data
        assert "created_at" in data

    def test_create_message_with_attachments(self, created_room, sample_attachment_data):
        """Test creating message with attachments"""
        message_data = {
            "content": "Check out my pet!",
            "author_id": "user-001",
            "room_id": created_room["id"],
            "attachments": [sample_attachment_data]
        }
        
        response = client.post("/api/messages", json=message_data)
        assert response.status_code == 201
        
        data = response.json()
        assert len(data["attachments"]) == 1
        assert data["attachments"][0]["filename"] == sample_attachment_data["filename"]

    def test_create_message_room_not_found(self, sample_message_data):
        """Test message creation with non-existent room"""
        sample_message_data["room_id"] = "nonexistent-room"
        
        response = client.post("/api/messages", json=sample_message_data)
        assert response.status_code == 404

    def test_create_message_missing_content(self, created_room):
        """Test message creation without content"""
        message_data = {
            "author_id": "user-001",
            "room_id": created_room["id"]
        }
        
        response = client.post("/api/messages", json=message_data)
        assert response.status_code == 422

    def test_create_reply_message(self, created_message):
        """Test creating a reply to a message"""
        reply_data = {
            "content": "That's awesome! What trick?",
            "author_id": "user-002",
            "room_id": created_message["room_id"],
            "parent_message_id": created_message["id"]
        }
        
        response = client.post("/api/messages", json=reply_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["parent_message_id"] == created_message["id"]
        
        # Verify parent reply count increased
        parent_response = client.get(f"/api/messages/{created_message['id']}")
        assert parent_response.json()["reply_count"] == 1

    def test_create_reply_parent_not_found(self, created_room):
        """Test creating reply to non-existent parent"""
        reply_data = {
            "content": "Reply to nothing",
            "author_id": "user-001",
            "room_id": created_room["id"],
            "parent_message_id": "nonexistent-message"
        }
        
        response = client.post("/api/messages", json=reply_data)
        assert response.status_code == 404

    def test_get_message_success(self, created_message):
        """Test successful message retrieval"""
        message_id = created_message["id"]
        
        response = client.get(f"/api/messages/{message_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == message_id
        assert data["content"] == created_message["content"]

    def test_get_message_not_found(self):
        """Test message retrieval for non-existent message"""
        response = client.get("/api/messages/nonexistent-id")
        assert response.status_code == 404

    def test_update_message_success(self, created_message):
        """Test successful message update"""
        message_id = created_message["id"]
        update_data = {"content": "Updated message content"}
        
        response = client.patch(f"/api/messages/{message_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["content"] == "Updated message content"
        assert data["is_edited"] is True

    def test_update_message_not_found(self):
        """Test message update for non-existent message"""
        response = client.patch("/api/messages/nonexistent-id", json={"content": "Test"})
        assert response.status_code == 404

    def test_delete_message_success(self, created_message):
        """Test successful message deletion"""
        message_id = created_message["id"]
        
        response = client.delete(f"/api/messages/{message_id}")
        assert response.status_code == 204
        
        # Verify message is deleted
        response = client.get(f"/api/messages/{message_id}")
        assert response.status_code == 404

    def test_delete_message_updates_parent_reply_count(self, created_message):
        """Test that deleting a reply updates parent reply count"""
        # Create a reply
        reply_data = {
            "content": "Reply message",
            "author_id": "user-002",
            "room_id": created_message["room_id"],
            "parent_message_id": created_message["id"]
        }
        reply_response = client.post("/api/messages", json=reply_data)
        reply_id = reply_response.json()["id"]
        
        # Delete the reply
        client.delete(f"/api/messages/{reply_id}")
        
        # Verify parent reply count decreased
        parent_response = client.get(f"/api/messages/{created_message['id']}")
        assert parent_response.json()["reply_count"] == 0

    def test_delete_message_not_found(self):
        """Test message deletion for non-existent message"""
        response = client.delete("/api/messages/nonexistent-id")
        assert response.status_code == 404

    def test_list_messages_in_room(self, created_room, sample_message_data):
        """Test listing messages in a room"""
        sample_message_data["room_id"] = created_room["id"]
        
        # Create multiple messages
        for i in range(3):
            msg_data = {**sample_message_data, "content": f"Message {i}"}
            client.post("/api/messages", json=msg_data)
        
        response = client.get(f"/api/rooms/{created_room['id']}/messages")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_list_messages_room_not_found(self):
        """Test listing messages for non-existent room"""
        response = client.get("/api/rooms/nonexistent-id/messages")
        assert response.status_code == 404

    def test_get_message_replies(self, created_message):
        """Test getting replies to a message"""
        # Create some replies
        for i in range(2):
            reply_data = {
                "content": f"Reply {i}",
                "author_id": f"user-00{i+2}",
                "room_id": created_message["room_id"],
                "parent_message_id": created_message["id"]
            }
            client.post("/api/messages", json=reply_data)
        
        response = client.get(f"/api/messages/{created_message['id']}/replies")
        assert response.status_code == 200
        assert len(response.json()) == 2


# =============================================================================
# Invitation Tests
# =============================================================================

class TestInvitations:
    """Test invitation operations"""

    def test_create_invitation_success(self, created_private_room):
        """Test successful invitation creation"""
        room_id = created_private_room["id"]
        owner_id = created_private_room["owner_id"]
        
        invitation_data = {
            "room_id": room_id,
            "invitee_id": "user-002",
            "message": "Join our exclusive pet club!"
        }
        
        response = client.post(
            f"/api/invitations?inviter_id={owner_id}",
            json=invitation_data
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["room_id"] == room_id
        assert data["invitee_id"] == "user-002"
        assert data["inviter_id"] == owner_id
        assert data["status"] == "pending"

    def test_create_invitation_public_room_fails(self, created_room):
        """Test that invitations can't be created for public rooms"""
        room_id = created_room["id"]
        owner_id = created_room["owner_id"]
        
        invitation_data = {
            "room_id": room_id,
            "invitee_id": "user-002"
        }
        
        response = client.post(
            f"/api/invitations?inviter_id={owner_id}",
            json=invitation_data
        )
        assert response.status_code == 400

    def test_create_invitation_non_member_fails(self, created_private_room):
        """Test that non-members can't create invitations"""
        room_id = created_private_room["id"]
        
        invitation_data = {
            "room_id": room_id,
            "invitee_id": "user-003"
        }
        
        response = client.post(
            "/api/invitations?inviter_id=user-999",  # Not a member
            json=invitation_data
        )
        assert response.status_code == 403

    def test_create_invitation_already_member_fails(self, created_private_room):
        """Test that can't invite existing members"""
        room_id = created_private_room["id"]
        owner_id = created_private_room["owner_id"]
        
        invitation_data = {
            "room_id": room_id,
            "invitee_id": owner_id  # Owner is already a member
        }
        
        response = client.post(
            f"/api/invitations?inviter_id={owner_id}",
            json=invitation_data
        )
        assert response.status_code == 400

    def test_get_invitation_success(self, created_private_room):
        """Test successful invitation retrieval"""
        room_id = created_private_room["id"]
        owner_id = created_private_room["owner_id"]
        
        # Create invitation
        invitation_data = {
            "room_id": room_id,
            "invitee_id": "user-002"
        }
        create_response = client.post(
            f"/api/invitations?inviter_id={owner_id}",
            json=invitation_data
        )
        invitation_id = create_response.json()["id"]
        
        # Get invitation
        response = client.get(f"/api/invitations/{invitation_id}")
        assert response.status_code == 200
        assert response.json()["id"] == invitation_id

    def test_get_invitation_not_found(self):
        """Test invitation retrieval for non-existent invitation"""
        response = client.get("/api/invitations/nonexistent-id")
        assert response.status_code == 404

    def test_accept_invitation(self, created_private_room):
        """Test accepting an invitation"""
        room_id = created_private_room["id"]
        owner_id = created_private_room["owner_id"]
        
        # Create invitation
        invitation_data = {
            "room_id": room_id,
            "invitee_id": "user-002"
        }
        create_response = client.post(
            f"/api/invitations?inviter_id={owner_id}",
            json=invitation_data
        )
        invitation_id = create_response.json()["id"]
        
        # Accept invitation
        response = client.post(
            f"/api/invitations/{invitation_id}/respond",
            json={"action": "accept"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "accepted"
        
        # Verify user was added to room
        room_response = client.get(f"/api/rooms/{room_id}")
        assert "user-002" in room_response.json()["members"]

    def test_decline_invitation(self, created_private_room):
        """Test declining an invitation"""
        room_id = created_private_room["id"]
        owner_id = created_private_room["owner_id"]
        
        # Create invitation
        invitation_data = {
            "room_id": room_id,
            "invitee_id": "user-002"
        }
        create_response = client.post(
            f"/api/invitations?inviter_id={owner_id}",
            json=invitation_data
        )
        invitation_id = create_response.json()["id"]
        
        # Decline invitation
        response = client.post(
            f"/api/invitations/{invitation_id}/respond",
            json={"action": "decline"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "declined"
        
        # Verify user was NOT added to room
        room_response = client.get(f"/api/rooms/{room_id}")
        assert "user-002" not in room_response.json()["members"]

    def test_respond_to_already_responded_invitation(self, created_private_room):
        """Test responding to an already responded invitation"""
        room_id = created_private_room["id"]
        owner_id = created_private_room["owner_id"]
        
        # Create and accept invitation
        invitation_data = {
            "room_id": room_id,
            "invitee_id": "user-002"
        }
        create_response = client.post(
            f"/api/invitations?inviter_id={owner_id}",
            json=invitation_data
        )
        invitation_id = create_response.json()["id"]
        
        client.post(f"/api/invitations/{invitation_id}/respond", json={"action": "accept"})
        
        # Try to respond again
        response = client.post(
            f"/api/invitations/{invitation_id}/respond",
            json={"action": "decline"}
        )
        assert response.status_code == 400

    def test_list_invitations(self, created_private_room):
        """Test listing invitations"""
        room_id = created_private_room["id"]
        owner_id = created_private_room["owner_id"]
        
        # Create multiple invitations
        for i in range(3):
            invitation_data = {
                "room_id": room_id,
                "invitee_id": f"user-00{i+2}"
            }
            client.post(
                f"/api/invitations?inviter_id={owner_id}",
                json=invitation_data
            )
        
        response = client.get("/api/invitations")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_list_invitations_with_filters(self, created_private_room):
        """Test listing invitations with filters"""
        room_id = created_private_room["id"]
        owner_id = created_private_room["owner_id"]
        
        # Create invitations
        for i in range(2):
            invitation_data = {
                "room_id": room_id,
                "invitee_id": f"user-00{i+2}"
            }
            client.post(
                f"/api/invitations?inviter_id={owner_id}",
                json=invitation_data
            )
        
        # Filter by invitee
        response = client.get("/api/invitations?invitee_id=user-002")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_delete_invitation(self, created_private_room):
        """Test deleting an invitation"""
        room_id = created_private_room["id"]
        owner_id = created_private_room["owner_id"]
        
        # Create invitation
        invitation_data = {
            "room_id": room_id,
            "invitee_id": "user-002"
        }
        create_response = client.post(
            f"/api/invitations?inviter_id={owner_id}",
            json=invitation_data
        )
        invitation_id = create_response.json()["id"]
        
        # Delete invitation
        response = client.delete(f"/api/invitations/{invitation_id}")
        assert response.status_code == 204
        
        # Verify invitation is deleted
        response = client.get(f"/api/invitations/{invitation_id}")
        assert response.status_code == 404


# =============================================================================
# Attachment Tests
# =============================================================================

class TestAttachments:
    """Test attachment operations"""

    def test_create_attachment_success(self, created_message, sample_attachment_data):
        """Test successful attachment creation"""
        message_id = created_message["id"]
        
        response = client.post(
            f"/api/messages/{message_id}/attachments",
            json=sample_attachment_data
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["filename"] == sample_attachment_data["filename"]
        assert data["message_id"] == message_id

    def test_create_attachment_message_not_found(self, sample_attachment_data):
        """Test attachment creation for non-existent message"""
        response = client.post(
            "/api/messages/nonexistent-id/attachments",
            json=sample_attachment_data
        )
        assert response.status_code == 404

    def test_get_attachment_success(self, created_message, sample_attachment_data):
        """Test successful attachment retrieval"""
        message_id = created_message["id"]
        
        # Create attachment
        create_response = client.post(
            f"/api/messages/{message_id}/attachments",
            json=sample_attachment_data
        )
        attachment_id = create_response.json()["id"]
        
        # Get attachment
        response = client.get(f"/api/attachments/{attachment_id}")
        assert response.status_code == 200
        assert response.json()["id"] == attachment_id

    def test_get_attachment_not_found(self):
        """Test attachment retrieval for non-existent attachment"""
        response = client.get("/api/attachments/nonexistent-id")
        assert response.status_code == 404

    def test_list_message_attachments(self, created_message, sample_attachment_data):
        """Test listing attachments for a message"""
        message_id = created_message["id"]
        
        # Create multiple attachments
        for i in range(2):
            att_data = {**sample_attachment_data, "filename": f"file{i}.jpg"}
            client.post(f"/api/messages/{message_id}/attachments", json=att_data)
        
        response = client.get(f"/api/messages/{message_id}/attachments")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_delete_attachment_success(self, created_message, sample_attachment_data):
        """Test successful attachment deletion"""
        message_id = created_message["id"]
        
        # Create attachment
        create_response = client.post(
            f"/api/messages/{message_id}/attachments",
            json=sample_attachment_data
        )
        attachment_id = create_response.json()["id"]
        
        # Delete attachment
        response = client.delete(f"/api/attachments/{attachment_id}")
        assert response.status_code == 204
        
        # Verify attachment is deleted
        response = client.get(f"/api/attachments/{attachment_id}")
        assert response.status_code == 404

    def test_delete_attachment_not_found(self):
        """Test attachment deletion for non-existent attachment"""
        response = client.delete("/api/attachments/nonexistent-id")
        assert response.status_code == 404


# =============================================================================
# Integration Flow Tests
# =============================================================================

class TestIntegrationFlows:
    """Test complete workflows"""

    def test_complete_public_room_workflow(self):
        """Test complete workflow: create room, add members, post messages, reply"""
        # 1. Create a public room
        room_data = {
            "name": "Dog Lovers Unite",
            "description": "For all dog enthusiasts",
            "is_private": False,
            "owner_id": "user-001"
        }
        room_response = client.post("/api/rooms", json=room_data)
        assert room_response.status_code == 201
        room = room_response.json()
        
        # 2. Add members
        client.post(f"/api/rooms/{room['id']}/members", json={"user_id": "user-002"})
        client.post(f"/api/rooms/{room['id']}/members", json={"user_id": "user-003"})
        
        # 3. Post a message
        message_data = {
            "content": "Welcome everyone! Share your dog stories!",
            "author_id": "user-001",
            "room_id": room["id"]
        }
        msg_response = client.post("/api/messages", json=message_data)
        assert msg_response.status_code == 201
        message = msg_response.json()
        
        # 4. Reply to the message
        reply_data = {
            "content": "My golden retriever loves to swim!",
            "author_id": "user-002",
            "room_id": room["id"],
            "parent_message_id": message["id"]
        }
        reply_response = client.post("/api/messages", json=reply_data)
        assert reply_response.status_code == 201
        
        # 5. Verify the thread
        replies_response = client.get(f"/api/messages/{message['id']}/replies")
        assert len(replies_response.json()) == 1
        
        # 6. Clean up - delete room (should cascade delete messages)
        delete_response = client.delete(f"/api/rooms/{room['id']}")
        assert delete_response.status_code == 204

    def test_complete_private_room_workflow(self):
        """Test complete workflow for private room with invitations"""
        # 1. Create a private room
        room_data = {
            "name": "Premium Pet Club",
            "description": "Exclusive discussions",
            "is_private": True,
            "owner_id": "user-001"
        }
        room_response = client.post("/api/rooms", json=room_data)
        assert room_response.status_code == 201
        room = room_response.json()
        
        # 2. Send invitation
        invitation_data = {
            "room_id": room["id"],
            "invitee_id": "user-002",
            "message": "You're invited to our exclusive club!"
        }
        inv_response = client.post(
            "/api/invitations?inviter_id=user-001",
            json=invitation_data
        )
        assert inv_response.status_code == 201
        invitation = inv_response.json()
        
        # 3. Accept invitation
        accept_response = client.post(
            f"/api/invitations/{invitation['id']}/respond",
            json={"action": "accept"}
        )
        assert accept_response.status_code == 200
        
        # 4. Verify member was added
        room_response = client.get(f"/api/rooms/{room['id']}")
        assert "user-002" in room_response.json()["members"]
        
        # 5. New member posts a message
        message_data = {
            "content": "Thanks for the invite! Happy to be here!",
            "author_id": "user-002",
            "room_id": room["id"]
        }
        msg_response = client.post("/api/messages", json=message_data)
        assert msg_response.status_code == 201

    def test_message_with_attachments_workflow(self):
        """Test complete workflow with message attachments"""
        # 1. Create room
        room_data = {
            "name": "Pet Photos",
            "is_private": False,
            "owner_id": "user-001"
        }
        room = client.post("/api/rooms", json=room_data).json()
        
        # 2. Post message with inline attachment
        message_data = {
            "content": "Check out my cat!",
            "author_id": "user-001",
            "room_id": room["id"],
            "attachments": [{
                "filename": "my_cat.jpg",
                "content_type": "image/jpeg",
                "size_bytes": 204800,
                "url": "https://storage.example.com/my_cat.jpg"
            }]
        }
        msg_response = client.post("/api/messages", json=message_data)
        assert msg_response.status_code == 201
        message = msg_response.json()
        assert len(message["attachments"]) == 1
        
        # 3. Add another attachment
        att_data = {
            "filename": "cat_video.mp4",
            "content_type": "video/mp4",
            "size_bytes": 5242880,
            "url": "https://storage.example.com/cat_video.mp4"
        }
        att_response = client.post(
            f"/api/messages/{message['id']}/attachments",
            json=att_data
        )
        assert att_response.status_code == 201
        
        # 4. List attachments
        atts_response = client.get(f"/api/messages/{message['id']}/attachments")
        assert len(atts_response.json()) == 2

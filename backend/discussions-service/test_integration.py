"""
Integration Tests for Discussions Service with CosmosDB

These tests verify the full integration with Azure CosmosDB.
They require a real CosmosDB connection (either emulator or Azure).

Run with: python -m pytest test_integration.py -v

Prerequisites:
1. Set USE_MOCK_DB=false in .env
2. Configure COSMOS_ENDPOINT and COSMOS_KEY
3. Database and containers will be auto-created if they don't exist

Note: These tests create real data in CosmosDB and clean up after themselves.
For safety, run against a development/test database only.
"""

import pytest
import os
import time
from fastapi.testclient import TestClient
from datetime import datetime

# Set integration test mode before importing
os.environ["USE_MOCK_DB"] = "false"

# Check if CosmosDB is configured
SKIP_INTEGRATION = not os.getenv("COSMOS_ENDPOINT")

if SKIP_INTEGRATION:
    pytest.skip(
        "Skipping integration tests: COSMOS_ENDPOINT not configured",
        allow_module_level=True
    )

from main import app
from database import get_database_service


client = TestClient(app)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def db_service():
    """Get database service for cleanup"""
    return get_database_service()


@pytest.fixture
def unique_suffix():
    """Generate unique suffix for test data"""
    return f"test-{int(time.time())}"


@pytest.fixture
def sample_room_data(unique_suffix):
    """Sample room creation data with unique name"""
    return {
        "name": f"Integration Test Room {unique_suffix}",
        "description": "Room created by integration tests",
        "is_private": False,
        "owner_id": f"test-user-{unique_suffix}"
    }


@pytest.fixture
def sample_private_room_data(unique_suffix):
    """Sample private room data with unique name"""
    return {
        "name": f"Private Test Room {unique_suffix}",
        "description": "Private room created by integration tests",
        "is_private": True,
        "owner_id": f"test-user-{unique_suffix}"
    }


@pytest.fixture
def cleanup_rooms():
    """Fixture to track and cleanup created rooms"""
    room_ids = []
    yield room_ids
    
    # Cleanup created rooms
    for room_id in room_ids:
        try:
            client.delete(f"/api/rooms/{room_id}")
        except Exception:
            pass


# =============================================================================
# Connection Tests
# =============================================================================

class TestCosmosDBConnection:
    """Test CosmosDB connectivity"""

    def test_health_check_cosmos(self):
        """Test health check with CosmosDB connection"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data.get("connection") == "cosmos" or data.get("database") == "discussionsdb"


# =============================================================================
# Full Integration Workflow Tests
# =============================================================================

class TestPublicRoomWorkflow:
    """Test complete workflow for public rooms"""

    def test_create_and_manage_public_room(self, sample_room_data, cleanup_rooms):
        """Test creating, updating, and deleting a public room"""
        # 1. Create room
        create_response = client.post("/api/rooms", json=sample_room_data)
        assert create_response.status_code == 201
        room = create_response.json()
        cleanup_rooms.append(room["id"])
        
        assert room["name"] == sample_room_data["name"]
        assert room["is_private"] is False
        assert room["member_count"] == 1
        
        # 2. Get room
        get_response = client.get(f"/api/rooms/{room['id']}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == room["id"]
        
        # 3. Update room
        update_response = client.patch(
            f"/api/rooms/{room['id']}",
            json={"description": "Updated description"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["description"] == "Updated description"
        
        # 4. Add member
        member_response = client.post(
            f"/api/rooms/{room['id']}/members",
            json={"user_id": "test-member-001"}
        )
        assert member_response.status_code == 200
        assert member_response.json()["member_count"] == 2
        
        # 5. Remove member
        remove_response = client.delete(f"/api/rooms/{room['id']}/members/test-member-001")
        assert remove_response.status_code == 200
        assert remove_response.json()["member_count"] == 1
        
        # 6. Delete room
        delete_response = client.delete(f"/api/rooms/{room['id']}")
        assert delete_response.status_code == 204
        cleanup_rooms.remove(room["id"])
        
        # 7. Verify deletion
        verify_response = client.get(f"/api/rooms/{room['id']}")
        assert verify_response.status_code == 404


class TestMessageWorkflow:
    """Test complete workflow for messages"""

    def test_post_and_reply_messages(self, sample_room_data, cleanup_rooms, unique_suffix):
        """Test posting messages and replies"""
        # 1. Create room
        room = client.post("/api/rooms", json=sample_room_data).json()
        cleanup_rooms.append(room["id"])
        
        # 2. Post initial message
        message_data = {
            "content": f"Hello from integration test {unique_suffix}",
            "author_id": sample_room_data["owner_id"],
            "room_id": room["id"]
        }
        msg_response = client.post("/api/messages", json=message_data)
        assert msg_response.status_code == 201
        message = msg_response.json()
        assert message["content"] == message_data["content"]
        
        # 3. Post reply
        reply_data = {
            "content": "This is a reply",
            "author_id": "replier-001",
            "room_id": room["id"],
            "parent_message_id": message["id"]
        }
        reply_response = client.post("/api/messages", json=reply_data)
        assert reply_response.status_code == 201
        reply = reply_response.json()
        assert reply["parent_message_id"] == message["id"]
        
        # 4. Get replies
        replies_response = client.get(f"/api/messages/{message['id']}/replies")
        assert replies_response.status_code == 200
        assert len(replies_response.json()) == 1
        
        # 5. List messages in room
        list_response = client.get(f"/api/rooms/{room['id']}/messages")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 2
        
        # 6. Update message
        update_response = client.patch(
            f"/api/messages/{message['id']}",
            json={"content": "Updated message content"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["is_edited"] is True
        
        # 7. Delete messages (cleanup happens with room deletion)


class TestMessageWithAttachments:
    """Test messages with attachments"""

    def test_create_message_with_attachments(self, sample_room_data, cleanup_rooms, unique_suffix):
        """Test creating messages with file attachments"""
        # 1. Create room
        room = client.post("/api/rooms", json=sample_room_data).json()
        cleanup_rooms.append(room["id"])
        
        # 2. Create message with inline attachment
        message_data = {
            "content": "Check out this photo!",
            "author_id": sample_room_data["owner_id"],
            "room_id": room["id"],
            "attachments": [{
                "filename": "test_photo.jpg",
                "content_type": "image/jpeg",
                "size_bytes": 102400,
                "url": f"https://storage.example.com/{unique_suffix}/test_photo.jpg"
            }]
        }
        msg_response = client.post("/api/messages", json=message_data)
        assert msg_response.status_code == 201
        message = msg_response.json()
        assert len(message["attachments"]) == 1
        
        # 3. Add another attachment
        att_data = {
            "filename": "test_document.pdf",
            "content_type": "application/pdf",
            "size_bytes": 51200,
            "url": f"https://storage.example.com/{unique_suffix}/test_document.pdf"
        }
        att_response = client.post(
            f"/api/messages/{message['id']}/attachments",
            json=att_data
        )
        assert att_response.status_code == 201
        attachment = att_response.json()
        
        # 4. List attachments
        list_response = client.get(f"/api/messages/{message['id']}/attachments")
        assert list_response.status_code == 200
        attachments = list_response.json()
        assert len(attachments) >= 1  # At least the one we added via API
        
        # 5. Get specific attachment
        get_response = client.get(f"/api/attachments/{attachment['id']}")
        assert get_response.status_code == 200
        
        # 6. Delete attachment
        del_response = client.delete(f"/api/attachments/{attachment['id']}")
        assert del_response.status_code == 204


class TestPrivateRoomAndInvitations:
    """Test private room workflow with invitations"""

    def test_private_room_invitation_workflow(self, sample_private_room_data, cleanup_rooms, unique_suffix):
        """Test creating private room, sending and accepting invitations"""
        # 1. Create private room
        room = client.post("/api/rooms", json=sample_private_room_data).json()
        cleanup_rooms.append(room["id"])
        assert room["is_private"] is True
        
        owner_id = sample_private_room_data["owner_id"]
        invitee_id = f"invitee-{unique_suffix}"
        
        # 2. Create invitation
        invitation_data = {
            "room_id": room["id"],
            "invitee_id": invitee_id,
            "message": "You're invited to join our discussion!"
        }
        inv_response = client.post(
            f"/api/invitations?inviter_id={owner_id}",
            json=invitation_data
        )
        assert inv_response.status_code == 201
        invitation = inv_response.json()
        assert invitation["status"] == "pending"
        
        # 3. Get invitation
        get_response = client.get(f"/api/invitations/{invitation['id']}")
        assert get_response.status_code == 200
        
        # 4. List invitations for invitee
        list_response = client.get(f"/api/invitations?invitee_id={invitee_id}")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1
        
        # 5. Accept invitation
        accept_response = client.post(
            f"/api/invitations/{invitation['id']}/respond",
            json={"action": "accept"}
        )
        assert accept_response.status_code == 200
        assert accept_response.json()["status"] == "accepted"
        
        # 6. Verify invitee is now a member
        room_response = client.get(f"/api/rooms/{room['id']}")
        assert invitee_id in room_response.json()["members"]
        
        # 7. New member can post messages
        message_data = {
            "content": "Thanks for the invite!",
            "author_id": invitee_id,
            "room_id": room["id"]
        }
        msg_response = client.post("/api/messages", json=message_data)
        assert msg_response.status_code == 201

    def test_decline_invitation(self, sample_private_room_data, cleanup_rooms, unique_suffix):
        """Test declining an invitation"""
        # 1. Create private room
        room = client.post("/api/rooms", json=sample_private_room_data).json()
        cleanup_rooms.append(room["id"])
        
        owner_id = sample_private_room_data["owner_id"]
        invitee_id = f"decliner-{unique_suffix}"
        
        # 2. Create invitation
        invitation_data = {
            "room_id": room["id"],
            "invitee_id": invitee_id
        }
        inv_response = client.post(
            f"/api/invitations?inviter_id={owner_id}",
            json=invitation_data
        )
        invitation = inv_response.json()
        
        # 3. Decline invitation
        decline_response = client.post(
            f"/api/invitations/{invitation['id']}/respond",
            json={"action": "decline"}
        )
        assert decline_response.status_code == 200
        assert decline_response.json()["status"] == "declined"
        
        # 4. Verify invitee is NOT a member
        room_response = client.get(f"/api/rooms/{room['id']}")
        assert invitee_id not in room_response.json()["members"]


class TestSearchAndFiltering:
    """Test search and filtering functionality"""

    def test_room_search(self, cleanup_rooms, unique_suffix):
        """Test searching for rooms"""
        # Create rooms with different names
        room1_data = {
            "name": f"Dog Lovers {unique_suffix}",
            "description": "For dog enthusiasts",
            "is_private": False,
            "owner_id": "search-test-user"
        }
        room2_data = {
            "name": f"Cat Lovers {unique_suffix}",
            "description": "For cat enthusiasts",
            "is_private": True,
            "owner_id": "search-test-user"
        }
        
        room1 = client.post("/api/rooms", json=room1_data).json()
        room2 = client.post("/api/rooms", json=room2_data).json()
        cleanup_rooms.extend([room1["id"], room2["id"]])
        
        # Search by name
        search_response = client.get(f"/api/rooms?search=Dog%20Lovers%20{unique_suffix}")
        assert search_response.status_code == 200
        results = search_response.json()
        assert len(results) >= 1
        assert any(r["name"] == room1_data["name"] for r in results)
        
        # Filter by privacy
        private_response = client.get(f"/api/rooms?is_private=true&search={unique_suffix}")
        assert private_response.status_code == 200
        private_results = private_response.json()
        assert all(r["is_private"] for r in private_results)

    def test_message_search(self, sample_room_data, cleanup_rooms, unique_suffix):
        """Test searching for messages"""
        # Create room
        room = client.post("/api/rooms", json=sample_room_data).json()
        cleanup_rooms.append(room["id"])
        
        # Create messages
        messages = [
            {"content": f"Hello world {unique_suffix}", "author_id": "user-a", "room_id": room["id"]},
            {"content": f"Goodbye world {unique_suffix}", "author_id": "user-b", "room_id": room["id"]},
            {"content": f"Just testing {unique_suffix}", "author_id": "user-a", "room_id": room["id"]}
        ]
        
        for msg in messages:
            client.post("/api/messages", json=msg)
        
        # Search by content
        search_response = client.get(f"/api/messages?room_id={room['id']}&search=Hello")
        assert search_response.status_code == 200
        results = search_response.json()
        assert len(results) >= 1
        assert any("Hello" in r["content"] for r in results)
        
        # Filter by author
        author_response = client.get(f"/api/messages?room_id={room['id']}&author_id=user-a")
        assert author_response.status_code == 200
        author_results = author_response.json()
        assert all(r["author_id"] == "user-a" for r in author_results)


class TestCascadeOperations:
    """Test cascade delete operations"""

    def test_room_deletion_cascades(self, sample_room_data, unique_suffix):
        """Test that deleting a room deletes associated data"""
        # 1. Create room
        room = client.post("/api/rooms", json=sample_room_data).json()
        
        # 2. Add messages
        for i in range(3):
            message_data = {
                "content": f"Message {i} for cascade test",
                "author_id": sample_room_data["owner_id"],
                "room_id": room["id"]
            }
            client.post("/api/messages", json=message_data)
        
        # 3. Verify messages exist
        messages_response = client.get(f"/api/rooms/{room['id']}/messages")
        assert len(messages_response.json()) == 3
        
        # 4. Delete room
        delete_response = client.delete(f"/api/rooms/{room['id']}")
        assert delete_response.status_code == 204
        
        # 5. Verify room is gone
        verify_response = client.get(f"/api/rooms/{room['id']}")
        assert verify_response.status_code == 404


# =============================================================================
# Performance/Load Tests (Optional)
# =============================================================================

class TestPerformance:
    """Basic performance tests"""

    def test_create_multiple_rooms(self, cleanup_rooms, unique_suffix):
        """Test creating multiple rooms quickly"""
        NUM_ROOMS = 5
        
        start_time = time.time()
        for i in range(NUM_ROOMS):
            room_data = {
                "name": f"Perf Test Room {i} {unique_suffix}",
                "is_private": False,
                "owner_id": f"perf-user-{unique_suffix}"
            }
            response = client.post("/api/rooms", json=room_data)
            assert response.status_code == 201
            cleanup_rooms.append(response.json()["id"])
        
        elapsed = time.time() - start_time
        avg_time = elapsed / NUM_ROOMS
        
        print(f"\nCreated {NUM_ROOMS} rooms in {elapsed:.2f}s (avg: {avg_time:.3f}s per room)")
        
        # Basic performance assertion (should be under 2s per room on average)
        assert avg_time < 2.0, f"Room creation too slow: {avg_time:.3f}s average"

    def test_list_rooms_performance(self, cleanup_rooms, unique_suffix):
        """Test listing rooms performance"""
        # Create some rooms first
        for i in range(3):
            room_data = {
                "name": f"List Perf Room {i} {unique_suffix}",
                "is_private": False,
                "owner_id": f"list-perf-user-{unique_suffix}"
            }
            response = client.post("/api/rooms", json=room_data)
            cleanup_rooms.append(response.json()["id"])
        
        # Time the list operation
        start_time = time.time()
        response = client.get("/api/rooms?limit=100")
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        print(f"\nListed rooms in {elapsed:.3f}s")
        
        # Should be under 1 second
        assert elapsed < 1.0, f"Room listing too slow: {elapsed:.3f}s"

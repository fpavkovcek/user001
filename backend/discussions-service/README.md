# Discussions Service

A FastAPI-based microservice for managing discussion rooms and messages between pet owners. Built with Azure CosmosDB as the backend database.

## Features

- **Discussion Rooms**: Create public or private discussion rooms
- **Messages**: Post messages with support for threads (replies) and attachments
- **Invitations**: Invite users to private rooms with accept/decline workflow
- **Membership Management**: Add/remove members from rooms
- **Attachments**: Support for file attachments on messages
- **Search & Filter**: Search rooms and messages with various filters

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Discussions Service                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │   FastAPI    │   │   Pydantic   │   │   Database   │        │
│  │   Routes     │──▶│   Models     │──▶│   Service    │        │
│  └──────────────┘   └──────────────┘   └──────────────┘        │
│                                               │                  │
│                                               ▼                  │
│                                  ┌────────────────────┐         │
│                                  │  MockDB / CosmosDB │         │
│                                  └────────────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: Azure CosmosDB (NoSQL)
- **Validation**: Pydantic v2
- **Testing**: pytest, httpx
- **Containerization**: Docker

## Data Models

### Room
```python
{
    "id": "uuid",
    "name": "Pet Lovers Chat",
    "description": "A room for pet enthusiasts",
    "is_private": false,
    "owner_id": "user-001",
    "members": ["user-001", "user-002"],
    "created_at": "2026-01-22T10:00:00Z",
    "updated_at": "2026-01-22T10:00:00Z"
}
```

### Message
```python
{
    "id": "uuid",
    "content": "Hello everyone!",
    "author_id": "user-001",
    "room_id": "room-uuid",
    "parent_message_id": null,  # For thread replies
    "attachments": [],
    "reply_count": 0,
    "is_edited": false,
    "created_at": "2026-01-22T10:00:00Z",
    "updated_at": "2026-01-22T10:00:00Z"
}
```

### Invitation
```python
{
    "id": "uuid",
    "room_id": "room-uuid",
    "invitee_id": "user-002",
    "inviter_id": "user-001",
    "message": "Join our exclusive pet club!",
    "status": "pending",  # pending, accepted, declined, expired
    "created_at": "2026-01-22T10:00:00Z",
    "responded_at": null
}
```

### Attachment
```python
{
    "id": "uuid",
    "message_id": "message-uuid",
    "filename": "my_pet.jpg",
    "content_type": "image/jpeg",
    "size_bytes": 102400,
    "url": "https://storage.example.com/attachments/my_pet.jpg",
    "uploaded_at": "2026-01-22T10:00:00Z"
}
```

## API Endpoints

### Health Check
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with service info |
| GET | `/health` | Health check with database status |

### Rooms
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/rooms` | Create a new room |
| GET | `/api/rooms` | List rooms with filters |
| GET | `/api/rooms/{room_id}` | Get room by ID |
| PATCH | `/api/rooms/{room_id}` | Update room |
| DELETE | `/api/rooms/{room_id}` | Delete room and all associated data |

### Room Membership
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/rooms/{room_id}/members` | Add a member to room |
| DELETE | `/api/rooms/{room_id}/members/{user_id}` | Remove member from room |

### Messages
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/messages` | Create a new message |
| GET | `/api/messages` | List messages with filters |
| GET | `/api/rooms/{room_id}/messages` | List messages in a room |
| GET | `/api/messages/{message_id}` | Get message by ID |
| GET | `/api/messages/{message_id}/replies` | Get replies to a message |
| PATCH | `/api/messages/{message_id}` | Update message |
| DELETE | `/api/messages/{message_id}` | Delete message |

### Invitations
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/invitations?inviter_id={id}` | Create invitation |
| GET | `/api/invitations` | List invitations with filters |
| GET | `/api/invitations/{invitation_id}` | Get invitation by ID |
| POST | `/api/invitations/{invitation_id}/respond` | Accept or decline |
| DELETE | `/api/invitations/{invitation_id}` | Delete invitation |

### Attachments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/messages/{message_id}/attachments` | Add attachment to message |
| GET | `/api/messages/{message_id}/attachments` | List message attachments |
| GET | `/api/attachments/{attachment_id}` | Get attachment by ID |
| DELETE | `/api/attachments/{attachment_id}` | Delete attachment |

## Quick Start

### Option 1: Development Mode (Mock Database)

1. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

2. Run with mock database (no CosmosDB required):
   ```bash
   # Using the start script
   chmod +x start.sh
   ./start.sh
   
   # Or manually
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8002 --reload
   ```

3. Access the API:
   - Swagger UI: http://localhost:8002/docs
   - ReDoc: http://localhost:8002/redoc

### Option 2: With Azure CosmosDB

1. Provision CosmosDB (using Azure CLI):
   ```bash
   chmod +x provision_cosmosdb.sh
   ./provision_cosmosdb.sh my-resource-group eastus my-cosmos-account
   ```

2. Update `.env` with the output values:
   ```env
   USE_MOCK_DB=false
   COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
   COSMOS_KEY=your-primary-key
   ```

3. Run the service:
   ```bash
   ./start.sh
   ```

### Option 3: Docker

```bash
# Build image
docker build -t discussions-service .

# Run with mock database
docker run -p 8002:8002 -e USE_MOCK_DB=true discussions-service

# Run with CosmosDB
docker run -p 8002:8002 \
  -e USE_MOCK_DB=false \
  -e COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/ \
  -e COSMOS_KEY=your-key \
  discussions-service
```

## Usage Examples

### Create a Public Room

```bash
curl -X POST http://localhost:8002/api/rooms \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dog Lovers Chat",
    "description": "For all dog enthusiasts!",
    "is_private": false,
    "owner_id": "user-001"
  }'
```

### Post a Message

```bash
curl -X POST http://localhost:8002/api/messages \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello everyone! My golden retriever just learned to fetch!",
    "author_id": "user-001",
    "room_id": "ROOM_ID_HERE"
  }'
```

### Post a Message with Attachment

```bash
curl -X POST http://localhost:8002/api/messages \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Check out my cute puppy!",
    "author_id": "user-001",
    "room_id": "ROOM_ID_HERE",
    "attachments": [{
      "filename": "puppy.jpg",
      "content_type": "image/jpeg",
      "size_bytes": 102400,
      "url": "https://storage.example.com/puppy.jpg"
    }]
  }'
```

### Reply to a Message (Thread)

```bash
curl -X POST http://localhost:8002/api/messages \
  -H "Content-Type: application/json" \
  -d '{
    "content": "That is so cute! How old is the puppy?",
    "author_id": "user-002",
    "room_id": "ROOM_ID_HERE",
    "parent_message_id": "MESSAGE_ID_HERE"
  }'
```

### Invite User to Private Room

```bash
# First create a private room
curl -X POST http://localhost:8002/api/rooms \
  -H "Content-Type: application/json" \
  -d '{
    "name": "VIP Pet Club",
    "is_private": true,
    "owner_id": "user-001"
  }'

# Then send invitation
curl -X POST "http://localhost:8002/api/invitations?inviter_id=user-001" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": "ROOM_ID_HERE",
    "invitee_id": "user-002",
    "message": "You are invited to our exclusive pet club!"
  }'
```

### Accept Invitation

```bash
curl -X POST http://localhost:8002/api/invitations/INVITATION_ID/respond \
  -H "Content-Type: application/json" \
  -d '{"action": "accept"}'
```

## Testing

### Run Unit Tests (Mock Database)

```bash
# All tests
python -m pytest test_main.py -v

# With coverage
python -m pytest test_main.py -v --cov=. --cov-report=html

# Specific test class
python -m pytest test_main.py::TestRoomCRUD -v
```

### Run Integration Tests (Real CosmosDB)

```bash
# Configure .env with real CosmosDB credentials first
# Then:
python -m pytest test_integration.py -v
```

### Test Coverage Summary

| Category | Tests |
|----------|-------|
| Health Endpoints | 2 |
| Room CRUD | 16 |
| Room Membership | 5 |
| Message CRUD | 16 |
| Invitations | 12 |
| Attachments | 7 |
| Integration Flows | 3 |
| **Total** | **61** |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `USE_MOCK_DB` | Use in-memory mock database | `true` |
| `COSMOS_ENDPOINT` | CosmosDB endpoint URL | - |
| `COSMOS_KEY` | CosmosDB primary key | - |
| `COSMOS_DATABASE_NAME` | Database name | `discussionsdb` |
| `COSMOS_ROOMS_CONTAINER` | Rooms container name | `rooms` |
| `COSMOS_MESSAGES_CONTAINER` | Messages container name | `messages` |
| `COSMOS_INVITATIONS_CONTAINER` | Invitations container name | `invitations` |
| `COSMOS_ATTACHMENTS_CONTAINER` | Attachments container name | `attachments` |
| `DEBUG` | Enable debug mode | `false` |
| `LOCAL_DEV` | Force local development mode | `false` |
| `COSMOS_EMULATOR_DISABLE_SSL_VERIFY` | Disable SSL for emulator | `false` |

### CosmosDB Container Configuration

| Container | Partition Key | Purpose |
|-----------|---------------|---------|
| `rooms` | `/id` | Discussion rooms |
| `messages` | `/room_id` | Messages (partitioned by room for efficient queries) |
| `invitations` | `/room_id` | Room invitations |
| `attachments` | `/message_id` | File attachments |

## Project Structure

```
backend/discussions-service/
├── main.py                 # FastAPI application and routes
├── models.py               # Pydantic data models
├── database.py             # Database service (Mock + CosmosDB)
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── test_main.py            # Unit tests (61 tests)
├── test_integration.py     # Integration tests for CosmosDB
├── provision_cosmosdb.sh   # Azure CLI script to provision CosmosDB
├── start.sh                # Development startup script
├── Dockerfile              # Container image definition
├── .env.example            # Environment template
└── README.md               # This file
```

## Security Notes

⚠️ **This service has no authentication** - it's simplified for demo purposes.

For production, you should:
1. Implement proper authentication (OAuth 2.0, Azure AD B2C, etc.)
2. Add authorization checks for room operations
3. Validate that users can only perform actions they're authorized for
4. Use HTTPS in production
5. Implement rate limiting
6. Secure CosmosDB with Entra ID (Managed Identity) instead of keys

## Contributing

1. Create a feature branch
2. Make changes
3. Run tests: `python -m pytest test_main.py -v`
4. Submit a pull request

## License

See the repository's LICENSE file.

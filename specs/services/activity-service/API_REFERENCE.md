# Service API Reference

Describe the HTTP/GraphQL endpoints, message topics, or scheduled jobs owned by this service.

## Quick Links
- Shared contracts: `../../platform/API_REFERENCE.md`
- ADRs impacting this service: N/A

## Endpoint Catalog

| Endpoint / Topic | Method / Verb | Description | Auth | Idempotency | Upstream Dependencies |
| --- | --- | --- | --- | --- | --- |
| `/` | GET | Root endpoint with service info | None | Yes | None |
| `/health` | GET | Health check | None | Yes | Cosmos DB |
| `/api/activities` | GET | List and search activities | None | Yes | Cosmos DB |
| `/api/activities` | POST | Create a new activity | None | No | Cosmos DB |
| `/api/activities/{activity_id}` | GET | Get a specific activity | None | Yes | Cosmos DB |
| `/api/activities/{activity_id}` | DELETE | Delete an activity | None | Yes | Cosmos DB |

## Detailed Contracts

### 1. List and Search Activities
**Purpose**: Retrieve activities, optionally filtered by pet, type, and date range.

**Request**:
- Query Parameters:
    - `petId` (optional): Filter by Pet ID.
    - `type` (optional): Filter by type (`feed`, `walk`, `play`, `vet`, `train`).
    - `from` (optional): Start timestamp (ISO).
    - `to` (optional): End timestamp (ISO).
    - `limit` (optional, default 100): Max results.
    - `offset` (optional, default 0): Skip results.

**Response**:
```json
[
  {
    "petId": "550e8400-e29b-41d4-a716-446655440000",
    "type": "walk",
    "timestamp": "2023-10-27T10:00:00Z",
    "notes": "Morning walk in the park",
    "id": "activity-uuid-123",
    "createdAt": "2023-10-27T10:00:00Z",
    "updatedAt": "2023-10-27T10:00:00Z"
  }
]
```

### 2. Create Activity
**Purpose**: Log a new activity for a pet.

**Request**:
```json
{
  "petId": "550e8400-e29b-41d4-a716-446655440000",
  "type": "walk",
  "timestamp": "2023-10-27T10:00:00Z",
  "notes": "Morning walk in the park"
}
```

**Response**: Returns the created activity object (201 Created).

### 3. Get Activity
**Purpose**: Retrieve details of a single activity.

**Response**: Returns the activity object or 404 Not Found.

### 4. Delete Activity
**Purpose**: Remove an activity log.

**Response**: 200 OK with message.

## Specification by Example

| Scenario | Given | When | Then |
| --- | --- | --- | --- |
| **Log Activity** | Valid activity payload | POST `/api/activities` | 201 Created, returns activity with ID. |
| **Invalid Type** | Payload with type "flying" | POST `/api/activities` | 422 Validation Error. |
| **Filter by Pet** | Existing activities for Pet A and Pet B | GET `/api/activities?petId=PetA` | Returns only activities for Pet A. |

## Error Catalog
- **404 Not Found**: Resource does not exist.
- **422 Unprocessable Entity**: Validation failure (e.g., invalid type).
- **500 Internal Server Error**: Database or server failure.
- **503 Service Unavailable**: Health check failure.

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
| `/clean` | GET | Maintenance: Clean database | None | Yes | Cosmos DB |
| `/api/pets` | GET | List and search pets | None | Yes | Cosmos DB |
| `/api/pets` | POST | Create a new pet | None | No | Cosmos DB |
| `/api/pets/{pet_id}` | GET | Get a specific pet | None | Yes | Cosmos DB |
| `/api/pets/{pet_id}` | PATCH | Update a pet | None | No | Cosmos DB |
| `/api/pets/{pet_id}` | DELETE | Delete a pet | None | Yes | Cosmos DB |

## Detailed Contracts

### 1. List and Search Pets
**Purpose**: Retrieve a list of pets with optional filtering by search term, species, and status. Supports pagination.

**Request**:
- Query Parameters:
    - `search` (optional): Search term for name or notes.
    - `species` (optional): Filter by species (`dog`, `cat`, `bird`, `other`).
    - `status` (optional): Filter by status.
    - `limit` (optional, default 100): Max results.
    - `offset` (optional, default 0): Skip results.

**Response**:
```json
[
  {
    "name": "Luna",
    "species": "dog",
    "ageYears": 3,
    "health": 90,
    "happiness": 85,
    "energy": 80,
    "avatarUrl": "https://example.com/luna.jpg",
    "notes": "Friendly golden retriever",
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "createdAt": "2023-10-27T10:00:00Z",
    "updatedAt": "2023-10-27T10:00:00Z"
  }
]
```

### 2. Create Pet
**Purpose**: Register a new pet in the system.

**Request**:
```json
{
  "name": "Luna",
  "species": "dog",
  "ageYears": 3,
  "health": 90,
  "happiness": 85,
  "energy": 80,
  "avatarUrl": "https://example.com/luna.jpg",
  "notes": "Friendly golden retriever"
}
```

**Response**: Returns the created pet object (201 Created).

### 3. Get Pet
**Purpose**: Retrieve details of a single pet.

**Response**: Returns the pet object or 404 Not Found.

### 4. Update Pet
**Purpose**: Partially update pet details.

**Request**:
```json
{
  "health": 95,
  "notes": "Recovered from cold"
}
```

**Response**: Returns the updated pet object.

### 5. Delete Pet
**Purpose**: Remove a pet from the system.

**Response**: 204 No Content.

## Specification by Example

| Scenario | Given | When | Then |
| --- | --- | --- | --- |
| **Create Valid Pet** | Valid pet JSON payload | POST `/api/pets` | 201 Created, returns pet with ID. |
| **Invalid Species** | Payload with species "dragon" | POST `/api/pets` | 422 Validation Error. |
| **Get Non-existent Pet** | Random UUID | GET `/api/pets/{id}` | 404 Not Found. |

## Error Catalog
- **400 Bad Request**: Invalid input parameters.
- **404 Not Found**: Resource does not exist.
- **422 Unprocessable Entity**: Validation failure (e.g., invalid species).
- **500 Internal Server Error**: Database or server failure.
- **503 Service Unavailable**: Health check failure.

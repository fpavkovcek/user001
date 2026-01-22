# Service API Reference

Describe the HTTP/GraphQL endpoints, message topics, or scheduled jobs owned by this service.

## Quick Links
- Shared contracts: `../../platform/API_REFERENCE.md`
- ADRs impacting this service: N/A

## Endpoint Catalog

| Endpoint / Topic        | Method / Verb | Description                                    | Auth | Idempotency | Upstream Dependencies |
| ----------------------- | ------------- | ---------------------------------------------- | ---- | ----------- | --------------------- |
| `/`                     | GET           | Root endpoint with service info                | None | Yes         | None                  |
| `/health`               | GET           | Health check with database connectivity        | None | Yes         | Cosmos DB             |
| `/api/accessories`      | GET           | List accessories with filtering and pagination | None | Yes         | Cosmos DB             |
| `/api/accessories`      | POST          | Create new accessory                           | None | No          | Cosmos DB             |
| `/api/accessories/{id}` | GET           | Get specific accessory                         | None | Yes         | Cosmos DB             |
| `/api/accessories/{id}` | PATCH         | Update accessory (partial)                     | None | No          | Cosmos DB             |
| `/api/accessories/{id}` | DELETE        | Delete accessory                               | None | Yes         | Cosmos DB             |

## Detailed Contracts

### 1. List Accessories
**Purpose**: Retrieve a list of accessories with optional filtering by search term, type, and stock status. Supports pagination.

**Request**:
- Query Parameters:
    - `search` (Optional[str]): Search in name or description.
    - `type` (Optional[str]): Filter by accessory type.
    - `lowStockOnly` (Optional[bool]): Show only items with stock < 10.
    - `limit` (int, default=100): Max results to return.
    - `offset` (int, default=0): Pagination offset.

**Response**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Squeaky Toy",
    "type": "toy",
    "price": 10.5,
    "stock": 50,
    "size": "M",
    "imageUrl": "http://example.com/toy.jpg",
    "description": "A fun toy",
    "createdAt": "2023-01-01T00:00:00Z",
    "updatedAt": "2023-01-01T00:00:00Z"
  }
]
```

### 2. Create Accessory
**Purpose**: Create a new accessory.

**Request**:
```json
{
  "name": "Squeaky Toy",
  "type": "toy",
  "price": 10.5,
  "stock": 50,
  "size": "M",
  "imageUrl": "http://example.com/toy.jpg",
  "description": "A fun toy"
}
```

**Response**:
Returns the created accessory object with generated ID and timestamps.

### 3. Get Accessory
**Purpose**: Get details of a specific accessory.

**Response**:
Returns the accessory object.

### 4. Update Accessory
**Purpose**: Update an existing accessory (partial update).

**Request**:
Fields to update (all optional).

**Response**:
Returns the updated accessory object.

### 5. Delete Accessory
**Purpose**: Delete an accessory.

**Response**:
204 No Content or 200 OK.

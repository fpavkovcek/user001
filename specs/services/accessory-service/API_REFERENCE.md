````markdown
# Service API Reference

Describe the HTTP/GraphQL endpoints, message topics, or scheduled jobs owned by this service.

## Quick Links
- Shared contracts: `../../platform/API_REFERENCE.md`
- ADRs impacting this service: N/A

## Endpoint Catalog

| Endpoint / Topic | Method / Verb | Description | Auth | Idempotency | Upstream Dependencies |
| --- | --- | --- | --- | --- | --- |
| `/` | GET | Root endpoint with service info | None | Yes | None |
| `/health` | GET | Health check with database connectivity | None | Yes | Cosmos DB |
| `/api/accessories` | GET | List accessories with filtering and pagination | None | Yes | Cosmos DB |
| `/api/accessories` | POST | Create a new accessory | None | No | Cosmos DB |
| `/api/accessories/{id}` | GET | Get a specific accessory | None | Yes | Cosmos DB |
| `/api/accessories/{id}` | PATCH | Partially update an accessory | None | No | Cosmos DB |
| `/api/accessories/{id}` | DELETE | Delete an accessory | None | Yes | Cosmos DB |

## Detailed Contracts

### 1. Root Endpoint
**Purpose**: Provides basic service information for discovery and verification.

**Request**: `GET /`

**Response**:
```json
{
  "service": "accessory-service",
  "version": "1.0.0",
  "status": "running"
}
```

---

### 2. Health Check
**Purpose**: Verifies service health and database connectivity. Automatically creates database/container and seeds sample data if they don't exist.

**Request**: `GET /health`

**Response** (Healthy):
```json
{
  "status": "healthy",
  "database": "connected",
  "container": "accessories"
}
```

**Response** (Unhealthy):
```json
{
  "status": "unhealthy",
  "error": "Failed to connect to database"
}
```

---

### 3. List and Search Accessories
**Purpose**: Retrieve a list of accessories with optional filtering by search term, type, and low stock status. Supports pagination.

**Request**: `GET /api/accessories`

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `search` | string | No | - | Search in name or description (uses `CONTAINS`) |
| `type` | string | No | - | Filter by accessory type (`toy`, `food`, `collar`, `bedding`, `grooming`, `other`) |
| `lowStockOnly` | boolean | No | `false` | Show only items with stock < 10 |
| `limit` | integer | No | `100` | Maximum number of results to return |
| `offset` | integer | No | `0` | Number of results to skip for pagination |

**Response**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Squeaky Ball",
    "type": "toy",
    "description": "A fun squeaky ball for dogs",
    "price": 12.99,
    "stock": 50,
    "size": "M",
    "imageUrl": "https://example.com/squeaky-ball.jpg",
    "createdAt": "2023-10-27T10:00:00Z",
    "updatedAt": "2023-10-27T10:00:00Z"
  },
  {
    "id": "661f8511-f30c-52e5-b827-557766551111",
    "name": "Premium Dog Food",
    "type": "food",
    "description": "Nutritious dry food for adult dogs",
    "price": 45.99,
    "stock": 8,
    "size": "L",
    "imageUrl": null,
    "createdAt": "2023-10-26T09:00:00Z",
    "updatedAt": "2023-10-26T09:00:00Z"
  }
]
```

---

### 4. Create Accessory
**Purpose**: Add a new accessory to the catalog.

**Request**: `POST /api/accessories`

**Request Body**:
```json
{
  "name": "Leather Collar",
  "type": "collar",
  "description": "Premium leather collar with brass buckle",
  "price": 29.99,
  "stock": 25,
  "size": "M",
  "imageUrl": "https://example.com/leather-collar.jpg"
}
```

**Required Fields**: `name`, `type`, `price`, `stock`, `size`

**Optional Fields**: `description`, `imageUrl`

**Response** (201 Created):
```json
{
  "id": "772f9622-g41d-63f6-c938-668877662222",
  "name": "Leather Collar",
  "type": "collar",
  "description": "Premium leather collar with brass buckle",
  "price": 29.99,
  "stock": 25,
  "size": "M",
  "imageUrl": "https://example.com/leather-collar.jpg",
  "createdAt": "2023-10-28T14:30:00Z",
  "updatedAt": "2023-10-28T14:30:00Z"
}
```

---

### 5. Get Accessory
**Purpose**: Retrieve details of a single accessory by ID.

**Request**: `GET /api/accessories/{id}`

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Squeaky Ball",
  "type": "toy",
  "description": "A fun squeaky ball for dogs",
  "price": 12.99,
  "stock": 50,
  "size": "M",
  "imageUrl": "https://example.com/squeaky-ball.jpg",
  "createdAt": "2023-10-27T10:00:00Z",
  "updatedAt": "2023-10-27T10:00:00Z"
}
```

**Response** (404 Not Found):
```json
{
  "detail": "Accessory not found"
}
```

---

### 6. Update Accessory (Partial)
**Purpose**: Partially update accessory details. Only provided fields are updated.

**Request**: `PATCH /api/accessories/{id}`

**Request Body** (all fields optional):
```json
{
  "stock": 30,
  "price": 27.99,
  "description": "Updated description"
}
```

**Response** (200 OK):
```json
{
  "id": "772f9622-g41d-63f6-c938-668877662222",
  "name": "Leather Collar",
  "type": "collar",
  "description": "Updated description",
  "price": 27.99,
  "stock": 30,
  "size": "M",
  "imageUrl": "https://example.com/leather-collar.jpg",
  "createdAt": "2023-10-28T14:30:00Z",
  "updatedAt": "2023-10-28T15:00:00Z"
}
```

---

### 7. Delete Accessory
**Purpose**: Remove an accessory from the catalog.

**Request**: `DELETE /api/accessories/{id}`

**Response** (204 No Content): Empty body.

**Response** (404 Not Found):
```json
{
  "detail": "Accessory not found"
}
```

---

## Specification by Example

| Scenario | Given | When | Then |
| --- | --- | --- | --- |
| **Create Valid Accessory** | Valid accessory JSON payload | POST `/api/accessories` | 201 Created, returns accessory with auto-generated ID and timestamps. |
| **Invalid Type** | Payload with type "furniture" | POST `/api/accessories` | 422 Validation Error (type must be one of: toy, food, collar, bedding, grooming, other). |
| **Negative Price** | Payload with price -5.00 | POST `/api/accessories` | 422 Validation Error (price must be >= 0). |
| **Get Non-existent Accessory** | Random UUID | GET `/api/accessories/{id}` | 404 Not Found. |
| **Filter by Type** | Accessories exist for toy and food types | GET `/api/accessories?type=toy` | Returns only accessories with type "toy". |
| **Search by Name** | Accessory named "Squeaky Ball" exists | GET `/api/accessories?search=squeaky` | Returns accessories with "squeaky" in name or description. |
| **Low Stock Filter** | Accessories exist with stock 5 and 50 | GET `/api/accessories?lowStockOnly=true` | Returns only accessory with stock 5 (< 10). |
| **Pagination** | 150 accessories exist | GET `/api/accessories?limit=50&offset=100` | Returns accessories 101-150. |
| **Partial Update** | Accessory exists | PATCH `/api/accessories/{id}` with `{"stock": 100}` | Updates only stock field, updatedAt is refreshed. |

---

## Error Catalog

| Status Code | Error | Description |
| --- | --- | --- |
| **400 Bad Request** | Invalid input parameters | Query parameter format invalid. |
| **404 Not Found** | Resource does not exist | Accessory with given ID not found. |
| **409 Conflict** | Duplicate resource | Accessory with given ID already exists. |
| **422 Unprocessable Entity** | Validation failure | Invalid type, negative price/stock, name too long, etc. |
| **500 Internal Server Error** | Database or server failure | Unexpected error during processing. |
| **503 Service Unavailable** | Health check failure | Database connectivity issue. |

---

## Query Parameter Details

### Search Behavior
- Case-insensitive search using Cosmos DB `CONTAINS()` function.
- Searches both `name` and `description` fields.
- Empty or null `search` parameter returns all accessories (subject to other filters).

### Low Stock Threshold
- Items with `stock < 10` are considered "low stock".
- When `lowStockOnly=true`, only items below this threshold are returned.

### Pagination
- Default `limit` is 100 items.
- `offset` allows skipping items for pagination.
- Results are ordered by `createdAt DESC` (newest first).

````

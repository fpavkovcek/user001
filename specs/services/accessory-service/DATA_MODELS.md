````markdown
# Service Data Models

Capture schemas owned by this service. Link to shared definitions from `../../platform/DATA_MODELS.md` when referencing canonical events or tables.

## Schema Inventory

| Name | Type | Owner | Source of Truth | Version |
| --- | --- | --- | --- | --- |
| **Accessory** | Entity | Accessory Service | Cosmos DB `accessories` container | v1 |
| **AccessoryBase** | Pydantic Model | Accessory Service | Code (models.py) | v1 |
| **AccessoryCreate** | Pydantic Model | Accessory Service | Code (models.py) | v1 |
| **AccessoryUpdate** | Pydantic Model | Accessory Service | Code (models.py) | v1 |
| **AccessorySearchFilters** | Pydantic Model | Accessory Service | Code (models.py) | v1 |

---

## Detailed Schemas

### Accessory (Full Entity)
**Purpose**: Represents a complete accessory record in the system, including auto-generated fields.

**Storage**: Azure Cosmos DB, Database: `accessoryservice`, Container: `accessories`.

**Partition Key**: `/id`

**Example Payload**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Squeaky Ball",
  "type": "toy",
  "description": "A fun squeaky ball for dogs of all sizes",
  "price": 12.99,
  "stock": 50,
  "size": "M",
  "imageUrl": "https://example.com/squeaky-ball.jpg",
  "createdAt": "2023-10-27T10:00:00Z",
  "updatedAt": "2023-10-27T10:00:00Z"
}
```

---

### Field Definitions

| Field | Type | Required | Constraints | Description |
| --- | --- | --- | --- | --- |
| `id` | string (UUID) | Auto-generated | UUID format | Unique identifier for the accessory. |
| `name` | string | Yes | 1-200 characters | Display name of the accessory. |
| `type` | string (enum) | Yes | See Accessory Types | Category of the accessory. |
| `description` | string | No | Max 2000 characters | Detailed description of the accessory. |
| `price` | float | Yes | >= 0 | Price in currency units. |
| `stock` | integer | Yes | >= 0 | Current inventory count. |
| `size` | string (enum) | Yes | S, M, L, XL | Size category of the accessory. |
| `imageUrl` | string | No | Valid URL format | URL to product image. |
| `createdAt` | datetime (ISO) | Auto-generated | ISO 8601 format | Timestamp when accessory was created. |
| `updatedAt` | datetime (ISO) | Auto-generated | ISO 8601 format | Timestamp when accessory was last updated. |

---

### Accessory Types (Enum)

| Value | Description |
| --- | --- |
| `toy` | Play items (balls, squeaky toys, puzzles) |
| `food` | Pet food and treats |
| `collar` | Collars, harnesses, and leashes |
| `bedding` | Beds, blankets, and crates |
| `grooming` | Brushes, shampoos, nail clippers |
| `other` | Miscellaneous accessories |

---

### Size Categories (Enum)

| Value | Description |
| --- | --- |
| `S` | Small - suitable for small pets |
| `M` | Medium - suitable for medium pets |
| `L` | Large - suitable for large pets |
| `XL` | Extra Large - suitable for very large pets |

---

## Pydantic Models

### AccessoryBase
**Purpose**: Base model with common fields shared across create/update operations.

```python
class AccessoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: Literal["toy", "food", "collar", "bedding", "grooming", "other"]
    price: float = Field(..., ge=0)
    stock: int = Field(..., ge=0)
    size: Literal["S", "M", "L", "XL"]
    imageUrl: Optional[str] = None
    description: Optional[str] = Field(None, max_length=2000)
```

---

### AccessoryCreate
**Purpose**: Model for POST requests to create a new accessory. Does not include `id` or timestamps.

```python
class AccessoryCreate(AccessoryBase):
    pass  # Inherits all fields from AccessoryBase
```

**Example Request**:
```json
{
  "name": "Leather Collar",
  "type": "collar",
  "price": 29.99,
  "stock": 25,
  "size": "M",
  "description": "Premium leather collar with brass buckle",
  "imageUrl": "https://example.com/leather-collar.jpg"
}
```

---

### AccessoryUpdate
**Purpose**: Model for PATCH requests. All fields are optional to support partial updates.

```python
class AccessoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[Literal["toy", "food", "collar", "bedding", "grooming", "other"]] = None
    price: Optional[float] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    size: Optional[Literal["S", "M", "L", "XL"]] = None
    imageUrl: Optional[str] = None
    description: Optional[str] = Field(None, max_length=2000)
```

**Example Request** (partial update):
```json
{
  "stock": 30,
  "price": 27.99
}
```

---

### Accessory (Response Model)
**Purpose**: Complete model returned in API responses. Includes auto-generated fields.

```python
class Accessory(AccessoryBase):
    id: str
    createdAt: datetime
    updatedAt: datetime
```

---

### AccessorySearchFilters
**Purpose**: Query parameter model for filtering and pagination on the list endpoint.

```python
class AccessorySearchFilters(BaseModel):
    search: Optional[str] = None          # Text search in name/description
    type: Optional[str] = None            # Filter by accessory type
    lowStockOnly: Optional[bool] = False  # Show only items with stock < 10
    limit: int = Field(100, ge=1)         # Max results to return
    offset: int = Field(0, ge=0)          # Pagination offset
```

---

## Validation Rules

| Rule | Field(s) | Error |
| --- | --- | --- |
| Name length | `name` | Must be 1-200 characters. |
| Valid type | `type` | Must be one of: toy, food, collar, bedding, grooming, other. |
| Non-negative price | `price` | Must be >= 0. |
| Non-negative stock | `stock` | Must be >= 0. |
| Valid size | `size` | Must be one of: S, M, L, XL. |
| Description length | `description` | Max 2000 characters if provided. |

---

## Low Stock Definition

An accessory is considered **low stock** when:
```
stock < 10
```

This threshold is used by:
- The `lowStockOnly` filter parameter.
- UI indicators for inventory management.
- Restocking alerts and workflows.

---

## Seed Data

When the database is auto-created during health check, two sample accessories are seeded:

**Sample 1 - Toy (Normal Stock)**:
```json
{
  "id": "seed-toy-001",
  "name": "Squeaky Ball",
  "type": "toy",
  "description": "A fun squeaky ball for dogs",
  "price": 12.99,
  "stock": 50,
  "size": "M",
  "imageUrl": null,
  "createdAt": "<auto>",
  "updatedAt": "<auto>"
}
```

**Sample 2 - Food (Low Stock)**:
```json
{
  "id": "seed-food-001",
  "name": "Premium Dog Food",
  "type": "food",
  "description": "Nutritious dry food for adult dogs",
  "price": 45.99,
  "stock": 5,
  "size": "L",
  "imageUrl": null,
  "createdAt": "<auto>",
  "updatedAt": "<auto>"
}
```

````

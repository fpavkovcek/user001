# Service Data Models

Capture schemas owned by this service. Link to shared definitions from `../../platform/DATA_MODELS.md` when referencing canonical events or tables.

## Schema Inventory

| Name          | Type   | Owner             | Source of Truth                   | Version |
| ------------- | ------ | ----------------- | --------------------------------- | ------- |
| **Accessory** | Entity | Accessory Service | Cosmos DB `accessories` container | v1      |

## Detailed Schemas

### Accessory Model
**Purpose**: Represents a pet accessory item.
**Storage**: Azure Cosmos DB, Database: `accessory-service`, Container: `accessories`.

**Example Payload**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Premium Collar",
  "type": "collar",
  "price": 25.99,
  "stock": 15,
  "size": "L",
  "imageUrl": "https://example.com/collar.jpg",
  "description": "High quality leather collar",
  "createdAt": "2023-10-27T10:00:00Z",
  "updatedAt": "2023-10-27T10:00:00Z"
}
```

**Validation Rules**:
- `name`: Required, 1-200 chars.
- `type`: Required, Literal["toy", "food", "collar", "bedding", "grooming", "other"].
- `price`: Required, float >= 0.
- `stock`: Required, int >= 0.
- `size`: Required, Literal["S", "M", "L", "XL"].
- `imageUrl`: Optional string.
- `description`: Optional string, max 2000 chars.

**Models to Implement**:
- **AccessoryBase**: Base model with common fields.
- **AccessoryCreate**: For POST requests (no id, timestamps).
- **AccessoryUpdate**: For PATCH requests (all fields optional).
- **Accessory**: Complete model with id and timestamps.
- **AccessorySearchFilters**: Query parameters for search/filter.

# Service Data Models

Capture schemas owned by this service. Link to shared definitions from `../../platform/DATA_MODELS.md` when referencing canonical events or tables.

## Schema Inventory

| Name | Type | Owner | Source of Truth | Version |
| --- | --- | --- | --- | --- |
| **Pet** | Entity | Pet Service | Cosmos DB `pets` container | v1 |

## Detailed Schemas

### Pet Model
**Purpose**: Represents a pet profile in the system.
**Storage**: Azure Cosmos DB, Database: `petservice`, Container: `pets`.

**Example Payload**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Luna",
  "species": "dog",
  "ageYears": 3,
  "health": 90,
  "happiness": 85,
  "energy": 80,
  "avatarUrl": "https://example.com/luna.jpg",
  "notes": "Friendly golden retriever",
  "createdAt": "2023-10-27T10:00:00Z",
  "updatedAt": "2023-10-27T10:00:00Z"
}
```

**Validation Rules**:
- `name`: Required, 1-100 chars.
- `species`: Required, Enum: `dog`, `cat`, `bird`, `other`.
- `ageYears`: Required, 0-50.
- `health`, `happiness`, `energy`: Required, 0-100.
- `notes`: Optional, max 1000 chars.

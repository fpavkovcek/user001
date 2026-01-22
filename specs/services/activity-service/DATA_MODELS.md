# Service Data Models

Capture schemas owned by this service. Link to shared definitions from `../../platform/DATA_MODELS.md` when referencing canonical events or tables.

## Schema Inventory

| Name | Type | Owner | Source of Truth | Version |
| --- | --- | --- | --- | --- |
| **Activity** | Entity | Activity Service | Cosmos DB `activities` container | v1 |

## Detailed Schemas

### Activity Model
**Purpose**: Represents a logged event/activity for a pet.
**Storage**: Azure Cosmos DB, Database: `activityservice`, Container: `activities`.

**Example Payload**:
```json
{
  "id": "activity-uuid-123",
  "petId": "550e8400-e29b-41d4-a716-446655440000",
  "type": "walk",
  "timestamp": "2023-10-27T10:00:00Z",
  "notes": "Morning walk in the park",
  "createdAt": "2023-10-27T10:00:00Z",
  "updatedAt": "2023-10-27T10:00:00Z"
}
```

**Validation Rules**:
- `petId`: Required, UUID string.
- `type`: Required, Enum: `feed`, `walk`, `play`, `vet`, `train`.
- `timestamp`: Required, ISO 8601 datetime.
- `notes`: Optional, max 1000 chars.

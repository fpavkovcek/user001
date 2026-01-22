# Accessory Service API Documentation

## Overview

The Accessory Service is a RESTful API built with FastAPI for managing pet accessories. It provides comprehensive CRUD operations, advanced search and filtering capabilities, and integrates with Azure CosmosDB for data persistence.

**Base URL**: `http://localhost:8030` (local development)

**API Version**: 1.0.0

## Table of Contents

- [Authentication](#authentication)
- [Configuration](#configuration)
- [Data Models](#data-models)
- [Endpoints](#endpoints)
  - [Health Check Endpoints](#health-check-endpoints)
  - [Accessory Management](#accessory-management)
- [Error Handling](#error-handling)
- [Sample Requests](#sample-requests)

## Authentication

### Current Implementation

The Accessory Service currently **does not require authentication** for API endpoints. All endpoints are publicly accessible.

### Azure CosmosDB Authentication

The service uses different authentication strategies based on the deployment environment:

#### Local Development (CosmosDB Emulator)

- **Method**: Key-based authentication
- **Required**: `COSMOS_KEY` environment variable
- **Default Key**: `C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==`

#### Azure Deployment

- **Method**: Entra ID (Managed Identity) authentication
- **Required**: `COSMOS_ENDPOINT` environment variable
- **Key Not Required**: Uses `DefaultAzureCredential` for automatic identity resolution

## Configuration

### Required Environment Variables

| Variable | Description | Required | Default | Example |
|----------|-------------|----------|---------|---------|
| `COSMOS_ENDPOINT` | Azure CosmosDB endpoint URL | Yes | - | `https://localhost:8081/` or `https://your-account.documents.azure.com:443/` |
| `COSMOS_KEY` | CosmosDB authentication key | Yes (local only) | - | `C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==` |
| `COSMOS_DATABASE_NAME` | Database name in CosmosDB | No | `accessoryservice` | `accessoryservice` |
| `COSMOS_CONTAINER_NAME` | Container name in CosmosDB | No | `accessories` | `accessories` |
| `DEBUG` | Enable debug mode | No | `false` | `true` or `false` |

### Environment Setup

Create a `.env` file in the service directory:

```bash
# Local Development with CosmosDB Emulator
COSMOS_ENDPOINT=https://localhost:8081/
COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
COSMOS_DATABASE_NAME=accessoryservice
COSMOS_CONTAINER_NAME=accessories
DEBUG=true

# Production with Azure CosmosDB
# COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
# COSMOS_KEY=<your-primary-or-secondary-key>
```

## Data Models

### Accessory (Complete Model)

The complete Accessory model includes all fields with system-generated metadata.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Interactive Ball",
  "type": "toy",
  "price": 15.99,
  "stock": 25,
  "size": "L",
  "imageUrl": "https://example.com/ball.jpg",
  "description": "LED light-up ball that keeps pets entertained for hours",
  "createdAt": "2025-11-24T10:00:00.000Z",
  "updatedAt": "2025-11-24T10:00:00.000Z"
}
```

### Field Definitions

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `id` | string | Auto-generated | UUID format | Unique accessory identifier |
| `name` | string | Yes | 1-200 characters | Accessory name |
| `type` | string | Yes | One of: `toy`, `food`, `collar`, `bedding`, `grooming`, `other` | Accessory category |
| `price` | number | Yes | >= 0 | Price in decimal format |
| `stock` | integer | Yes | >= 0 | Current stock quantity |
| `size` | string | Yes | One of: `S`, `M`, `L`, `XL` | Size category |
| `imageUrl` | string | No | Valid URL | URL to accessory image |
| `description` | string | No | Max 2000 characters | Detailed description |
| `createdAt` | string | Auto-generated | ISO 8601 timestamp | Creation timestamp |
| `updatedAt` | string | Auto-generated | ISO 8601 timestamp | Last update timestamp |

### AccessoryCreate (Request Model)

Used when creating a new accessory. Excludes system-generated fields.

```json
{
  "name": "Interactive Ball",
  "type": "toy",
  "price": 15.99,
  "stock": 25,
  "size": "L",
  "imageUrl": "https://example.com/ball.jpg",
  "description": "LED light-up ball that keeps pets entertained for hours"
}
```

### AccessoryUpdate (Request Model)

Used for partial updates. All fields are optional.

```json
{
  "name": "Updated Interactive Ball",
  "price": 18.99,
  "stock": 30,
  "description": "Updated: LED light-up ball with improved battery life"
}
```

### AccessorySearchFilters

Search and filter parameters for querying accessories.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `search` | string | No | - | Search term for name or description |
| `type` | string | No | - | Filter by type: `toy`, `food`, `collar`, `bedding`, `grooming`, `other` |
| `lowStockOnly` | boolean | No | - | Show only items with stock < 10 |
| `limit` | integer | No | 100 | Maximum results (1-1000) |
| `offset` | integer | No | 0 | Number of results to skip |

## Endpoints

### Health Check Endpoints

#### Get Root Information

**Endpoint**: `GET /`

**Description**: Returns basic service information and health status.

**Tags**: Health

**Authentication**: None required

**Request Headers**: None

**Response**: `200 OK`

```json
{
  "message": "Welcome to Accessory Service API",
  "version": "1.0.0",
  "status": "healthy"
}
```

#### Comprehensive Health Check

**Endpoint**: `GET /health`

**Description**: Comprehensive health check including database connectivity. Returns service health status and database connection status.

**Tags**: Health

**Authentication**: None required

**Request Headers**: None

**Response**: `200 OK` (Service Healthy)

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": {
    "status": "connected",
    "database": "accessoryservice",
    "container": "accessories"
  }
}
```

**Response**: `503 Service Unavailable` (Service Unhealthy)

```json
{
  "detail": "Service unhealthy"
}
```

### Accessory Management

#### List Accessories

**Endpoint**: `GET /api/accessories`

**Description**: Retrieve accessories with optional filtering and pagination. Supports searching by name/description, filtering by type, stock status, and pagination.

**Tags**: Accessories

**Authentication**: None required

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `search` | string | No | - | Search in name and description |
| `type` | string | No | - | Filter by type: `toy`, `food`, `collar`, `bedding`, `grooming`, `other` |
| `lowStockOnly` | boolean | No | - | Show only items with stock < 10 |
| `limit` | integer | No | 100 | Maximum results (1-1000) |
| `offset` | integer | No | 0 | Results to skip for pagination |

**Response**: `200 OK`

Returns an array of Accessory objects.

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Interactive Ball",
    "type": "toy",
    "price": 15.99,
    "stock": 25,
    "size": "L",
    "imageUrl": "https://example.com/ball.jpg",
    "description": "LED light-up ball that keeps pets entertained for hours",
    "createdAt": "2025-11-24T10:00:00.000Z",
    "updatedAt": "2025-11-24T10:00:00.000Z"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Premium Kibble",
    "type": "food",
    "price": 29.99,
    "stock": 8,
    "size": "M",
    "imageUrl": "https://example.com/kibble.jpg",
    "description": "High-quality dry food with natural ingredients",
    "createdAt": "2025-11-24T10:05:00.000Z",
    "updatedAt": "2025-11-24T10:05:00.000Z"
  }
]
```

**Error Responses**:

- `400 Bad Request`: Invalid type parameter

  ```json
  {
    "detail": "Invalid type. Must be one of: toy, food, collar, bedding, grooming, other"
  }
  ```

- `500 Internal Server Error`: Failed to retrieve accessories

  ```json
  {
    "detail": "Failed to retrieve accessories"
  }
  ```

#### Create Accessory

**Endpoint**: `POST /api/accessories`

**Description**: Create a new accessory with all required fields.

**Tags**: Accessories

**Authentication**: None required

**Request Headers**:

```text
Content-Type: application/json
```

**Request Body**: AccessoryCreate model

```json
{
  "name": "Interactive Ball",
  "type": "toy",
  "price": 15.99,
  "stock": 25,
  "size": "L",
  "imageUrl": "https://example.com/ball.jpg",
  "description": "LED light-up ball that keeps pets entertained for hours"
}
```

**Response**: `201 Created`

Returns the created Accessory object with generated `id`, `createdAt`, and `updatedAt`.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Interactive Ball",
  "type": "toy",
  "price": 15.99,
  "stock": 25,
  "size": "L",
  "imageUrl": "https://example.com/ball.jpg",
  "description": "LED light-up ball that keeps pets entertained for hours",
  "createdAt": "2025-11-24T10:00:00.000Z",
  "updatedAt": "2025-11-24T10:00:00.000Z"
}
```

**Error Responses**:

- `400 Bad Request`: Validation error

  ```json
  {
    "detail": "Validation error message"
  }
  ```

- `422 Unprocessable Entity`: Invalid field values (e.g., invalid type, negative price)

  ```json
  {
    "detail": [
      {
        "loc": ["body", "type"],
        "msg": "value is not a valid enumeration member; permitted: 'toy', 'food', 'collar', 'bedding', 'grooming', 'other'",
        "type": "type_error.enum"
      }
    ]
  }
  ```

- `500 Internal Server Error`: Failed to create accessory

  ```json
  {
    "detail": "Failed to create accessory"
  }
  ```

#### Get Accessory by ID

**Endpoint**: `GET /api/accessories/{accessory_id}`

**Description**: Retrieve a specific accessory by its unique identifier.

**Tags**: Accessories

**Authentication**: None required

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `accessory_id` | string | Yes | Unique accessory identifier (UUID) |

**Response**: `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Interactive Ball",
  "type": "toy",
  "price": 15.99,
  "stock": 25,
  "size": "L",
  "imageUrl": "https://example.com/ball.jpg",
  "description": "LED light-up ball that keeps pets entertained for hours",
  "createdAt": "2025-11-24T10:00:00.000Z",
  "updatedAt": "2025-11-24T10:00:00.000Z"
}
```

**Error Responses**:

- `404 Not Found`: Accessory not found

  ```json
  {
    "detail": "Accessory with ID 550e8400-e29b-41d4-a716-446655440000 not found"
  }
  ```

- `500 Internal Server Error`: Failed to retrieve accessory

  ```json
  {
    "detail": "Failed to retrieve accessory"
  }
  ```

#### Update Accessory

**Endpoint**: `PATCH /api/accessories/{accessory_id}`

**Description**: Partially update an accessory. Only provided fields will be updated.

**Tags**: Accessories

**Authentication**: None required

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `accessory_id` | string | Yes | Unique accessory identifier (UUID) |

**Request Headers**:

```text
Content-Type: application/json
```

**Request Body**: AccessoryUpdate model (all fields optional)

```json
{
  "price": 18.99,
  "stock": 30,
  "description": "Updated: LED light-up ball with improved battery life"
}
```

**Response**: `200 OK`

Returns the updated Accessory object with modified `updatedAt` timestamp.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Interactive Ball",
  "type": "toy",
  "price": 18.99,
  "stock": 30,
  "size": "L",
  "imageUrl": "https://example.com/ball.jpg",
  "description": "Updated: LED light-up ball with improved battery life",
  "createdAt": "2025-11-24T10:00:00.000Z",
  "updatedAt": "2025-11-24T12:00:00.000Z"
}
```

**Error Responses**:

- `404 Not Found`: Accessory not found

  ```json
  {
    "detail": "Accessory with ID 550e8400-e29b-41d4-a716-446655440000 not found"
  }
  ```

- `422 Unprocessable Entity`: Invalid field values

  ```json
  {
    "detail": [
      {
        "loc": ["body", "price"],
        "msg": "ensure this value is greater than or equal to 0",
        "type": "value_error.number.not_ge"
      }
    ]
  }
  ```

- `500 Internal Server Error`: Failed to update accessory

  ```json
  {
    "detail": "Failed to update accessory"
  }
  ```

#### Delete Accessory

**Endpoint**: `DELETE /api/accessories/{accessory_id}`

**Description**: Delete an accessory by its unique identifier.

**Tags**: Accessories

**Authentication**: None required

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `accessory_id` | string | Yes | Unique accessory identifier (UUID) |

**Response**: `204 No Content`

No response body.

**Error Responses**:

- `404 Not Found`: Accessory not found

  ```json
  {
    "detail": "Accessory with ID 550e8400-e29b-41d4-a716-446655440000 not found"
  }
  ```

- `500 Internal Server Error`: Failed to delete accessory

  ```json
  {
    "detail": "Failed to delete accessory"
  }
  ```

## Error Handling

The Accessory Service implements comprehensive error handling following HTTP standards and best practices.

### Error Response Format

All error responses follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

For validation errors (422), a more detailed format is used:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Detailed validation error message",
      "type": "error_type"
    }
  ]
}
```

### HTTP Status Codes

| Status Code | Meaning | When It Occurs |
|-------------|---------|----------------|
| `200 OK` | Success | Successful GET, PATCH requests |
| `201 Created` | Resource created | Successful POST requests |
| `204 No Content` | Success with no body | Successful DELETE requests |
| `400 Bad Request` | Invalid request | Invalid query parameters, validation errors |
| `404 Not Found` | Resource not found | Accessory ID does not exist |
| `422 Unprocessable Entity` | Validation failed | Invalid field values, type mismatches |
| `500 Internal Server Error` | Server error | Database errors, unexpected exceptions |
| `503 Service Unavailable` | Service unavailable | Health check failed, database unavailable |

### Common Error Scenarios

#### Invalid Accessory Type

**Request**: Create accessory with invalid type

```bash
curl -X POST "http://localhost:8030/api/accessories" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Invalid Item",
    "type": "invalid_type",
    "price": 10.00,
    "stock": 5,
    "size": "M"
  }'
```

**Response**: `422 Unprocessable Entity`

#### Missing Required Fields

**Request**: Create accessory without required fields

```bash
curl -X POST "http://localhost:8030/api/accessories" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Incomplete Item",
    "price": 15.99
  }'
```

**Response**: `422 Unprocessable Entity`

#### Negative Price

**Request**: Create accessory with negative price

```bash
curl -X POST "http://localhost:8030/api/accessories" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Negative Price Item",
    "type": "toy",
    "price": -5.00,
    "stock": 10,
    "size": "S"
  }'
```

**Response**: `422 Unprocessable Entity`

#### Accessory Not Found

**Request**: Get non-existent accessory

```bash
curl -X GET "http://localhost:8030/api/accessories/non-existent-id"
```

**Response**: `404 Not Found`

## Sample Requests

### Using curl

#### Health Check

```bash
# Check service health
curl -X GET "http://localhost:8030/health"

# Get root information
curl -X GET "http://localhost:8030/"
```

#### Create Accessories

```bash
# Create a toy accessory
curl -X POST "http://localhost:8030/api/accessories" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Interactive Ball",
    "type": "toy",
    "price": 15.99,
    "stock": 25,
    "size": "L",
    "imageUrl": "https://example.com/ball.jpg",
    "description": "LED light-up ball that keeps pets entertained for hours"
  }'

# Create a food accessory
curl -X POST "http://localhost:8030/api/accessories" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Kibble",
    "type": "food",
    "price": 29.99,
    "stock": 8,
    "size": "M",
    "imageUrl": "https://example.com/kibble.jpg",
    "description": "High-quality dry food with natural ingredients"
  }'

# Create a collar accessory
curl -X POST "http://localhost:8030/api/accessories" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "LED Safety Collar",
    "type": "collar",
    "price": 22.50,
    "stock": 15,
    "size": "M",
    "imageUrl": "https://example.com/collar.jpg",
    "description": "Rechargeable LED collar for nighttime visibility"
  }'

# Create a bedding accessory
curl -X POST "http://localhost:8030/api/accessories" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Memory Foam Bed",
    "type": "bedding",
    "price": 49.99,
    "stock": 5,
    "size": "XL",
    "imageUrl": "https://example.com/bed.jpg",
    "description": "Orthopedic memory foam bed for senior pets"
  }'

# Create a grooming accessory
curl -X POST "http://localhost:8030/api/accessories" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Slicker Brush",
    "type": "grooming",
    "price": 18.99,
    "stock": 12,
    "size": "M",
    "description": "Professional grooming brush for all coat types"
  }'
```

#### Get Accessories

```bash
# Get all accessories
curl -X GET "http://localhost:8030/api/accessories"

# Get accessories with pagination
curl -X GET "http://localhost:8030/api/accessories?limit=5&offset=0"

# Search accessories by name
curl -X GET "http://localhost:8030/api/accessories?search=ball"

# Filter by type
curl -X GET "http://localhost:8030/api/accessories?type=toy"

# Get low stock items only
curl -X GET "http://localhost:8030/api/accessories?lowStockOnly=true"

# Combined filters - food items with low stock
curl -X GET "http://localhost:8030/api/accessories?type=food&lowStockOnly=true"

# Search in descriptions
curl -X GET "http://localhost:8030/api/accessories?search=LED"

# Get specific accessory by ID
curl -X GET "http://localhost:8030/api/accessories/550e8400-e29b-41d4-a716-446655440000"
```

#### Update Accessories

```bash
# Update price and stock
curl -X PATCH "http://localhost:8030/api/accessories/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 18.99,
    "stock": 30,
    "description": "Updated: LED light-up ball with improved battery life"
  }'

# Update only stock
curl -X PATCH "http://localhost:8030/api/accessories/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "stock": 20
  }'

# Update multiple fields
curl -X PATCH "http://localhost:8030/api/accessories/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Interactive Ball",
    "price": 19.99,
    "stock": 35,
    "size": "XL"
  }'
```

#### Delete Accessories

```bash
# Delete an accessory
curl -X DELETE "http://localhost:8030/api/accessories/550e8400-e29b-41d4-a716-446655440000"
```

### Using HTTP File (REST Client)

The service includes an `accessory-service.http` file in the `backend/accessory-service` directory for use with the [REST Client VS Code extension](https://marketplace.visualstudio.com/items?itemName=humao.rest-client).

Example requests from the HTTP file:

```http
### Get Health Check
GET http://localhost:8030/health HTTP/1.1

### Create Accessory
POST http://localhost:8030/api/accessories HTTP/1.1
Content-Type: application/json

{
  "name": "Interactive Ball",
  "type": "toy",
  "price": 15.99,
  "stock": 25,
  "size": "L",
  "imageUrl": "https://example.com/ball.jpg",
  "description": "LED light-up ball that keeps pets entertained for hours"
}

### Get All Accessories
GET http://localhost:8030/api/accessories HTTP/1.1

### Get Low Stock Items
GET http://localhost:8030/api/accessories?lowStockOnly=true HTTP/1.1
```

## API Documentation (Interactive)

The Accessory Service provides interactive API documentation powered by OpenAPI/Swagger:

- **Swagger UI**: [http://localhost:8030/docs](http://localhost:8030/docs)
- **ReDoc**: [http://localhost:8030/redoc](http://localhost:8030/redoc)
- **OpenAPI Schema (JSON)**: [http://localhost:8030/openapi.json](http://localhost:8030/openapi.json)

The interactive documentation allows you to:

- Browse all available endpoints
- View request/response schemas
- Try out API calls directly from the browser
- See detailed validation rules and constraints

## Cross-Service References

### Shared Models and Patterns

The Accessory Service follows the same architectural patterns as other services in the PetPal application:

- **Pet Service** (`backend/pet-service`): Manages pet profiles
  - Similar CRUD patterns
  - Shared CosmosDB authentication strategy
  - Common health check implementation

- **Activity Service** (`backend/activity-service`): Tracks pet activities
  - Similar search and filter patterns
  - Shared timestamp formats (ISO 8601)
  - Common pagination approach

### Integration Considerations

When integrating with the Accessory Service:

1. **Pet References**: While accessories are standalone, they may be associated with pets via the Pet Service
2. **Activity Tracking**: Accessory purchases or usage could be tracked via the Activity Service
3. **Common Fields**: All services use UUID identifiers and ISO 8601 timestamps for consistency

## Assumptions and Notes

### Assumptions Made

1. **No Authentication Required**: The current implementation does not enforce authentication on endpoints. For production use, consider adding authentication middleware (e.g., JWT tokens, API keys).

2. **Single-Tenant**: The service assumes a single-tenant deployment. For multi-tenant scenarios, add tenant filtering and isolation.

3. **Mixed Async/Sync Operations**: The service uses a hybrid approach - the list/search endpoint (`GET /api/accessories`) uses async database operations for better performance with large result sets, while CRUD operations (create, get by ID, update, delete) use synchronous database calls for simplicity. This is based on the current implementation in `backend/accessory-service/database.py`.

4. **Manual Price Management**: Prices are stored as floats. For financial applications requiring exact precision, consider using Decimal types throughout.

5. **Basic Search**: The search functionality searches in name and description fields. For advanced full-text search, consider integrating Azure Cognitive Search.

6. **No Soft Deletes**: The DELETE operation permanently removes accessories. Consider implementing soft deletes for audit trails.

### Environment-Specific Notes

- **Local Development**: Uses CosmosDB Emulator with default credentials
- **Azure Production**: Uses Managed Identity for secure credential-less authentication
- **Port Configuration**: Default port is 8030 to avoid conflicts with Pet Service (8010) and Activity Service (8020)

### Known Limitations

1. **No Pagination Metadata**: The list endpoint supports offset/limit pagination parameters but returns raw arrays without pagination metadata in the response (e.g., no total count, has_next, page number). Clients must manage pagination state themselves.
2. **No Bulk Operations**: No endpoints for bulk create, update, or delete operations
3. **Limited Stock Management**: No automatic low-stock alerts or inventory management features
4. **No Image Upload**: The `imageUrl` field expects external URLs; no built-in image upload/storage

## Support and Troubleshooting

### Common Issues

**Issue**: CosmosDB connection fails

**Solution**: Verify `COSMOS_ENDPOINT` and `COSMOS_KEY` are set correctly. For local development, ensure CosmosDB Emulator is running.

**Issue**: Validation errors on create/update

**Solution**: Check that all required fields are present and valid. Use the interactive docs to see exact validation rules.

**Issue**: Empty results from search

**Solution**: Verify that accessories exist in the database. Use the health check endpoint to trigger auto-seeding of sample data.

### Logging

The service uses Python's logging module with INFO level by default. Logs include:

- Request processing information
- Database operation results
- Error details with stack traces

Check console output for detailed diagnostic information.

## License

This service is part of the MicroHack GitHub workshop and follows the repository's licensing terms.

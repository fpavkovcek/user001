# Accessory Service

Pet accessories management microservice for PetPal application.

## Overview

The Accessory Service manages pet accessories (toys, food, collars, bedding, grooming supplies) with full CRUD operations, search, filtering, and low-stock detection.

## Features

- **CRUD Operations**: Create, Read, Update, Delete accessories
- **Search**: Text search in name and description fields
- **Filtering**: Filter by accessory type and low-stock status
- **Pagination**: Offset/limit pagination for large datasets
- **Auto-setup**: Database and container are auto-created on first health check
- **Seed Data**: Sample accessories are seeded automatically

## Quick Start

### Prerequisites

- Python 3.11+
- Azure Cosmos DB Emulator (vNext) running on port 8081

### Running the Service

```bash
# From the backend/accessory-service directory
chmod +x start.sh
./start.sh
```

The service will be available at:
- **API**: http://localhost:8030
- **Docs**: http://localhost:8030/docs
- **Health**: http://localhost:8030/health

### Environment Variables

The service reads from `.env` file or environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `COSMOS_ENDPOINT` | (required) | CosmosDB endpoint URL |
| `COSMOS_KEY` | (required for local) | CosmosDB access key |
| `COSMOS_DATABASE_NAME` | `accessoryservice` | Database name |
| `COSMOS_CONTAINER_NAME` | `accessories` | Container name |
| `DEBUG` | `false` | Enable debug mode |

### Using Project Root .env

The service will automatically use `../../.env` if a local `.env` doesn't exist.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service info |
| GET | `/health` | Health check |
| GET | `/api/accessories` | List accessories (with filters) |
| POST | `/api/accessories` | Create accessory |
| GET | `/api/accessories/{id}` | Get accessory by ID |
| PATCH | `/api/accessories/{id}` | Update accessory |
| DELETE | `/api/accessories/{id}` | Delete accessory |

### Query Parameters (List Endpoint)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search` | string | - | Text search in name/description |
| `type` | string | - | Filter by type (toy, food, collar, bedding, grooming, other) |
| `lowStockOnly` | boolean | false | Show only items with stock < 10 |
| `limit` | integer | 100 | Max results (1-1000) |
| `offset` | integer | 0 | Skip results for pagination |

## Data Model

### Accessory

```json
{
  "id": "uuid",
  "name": "Squeaky Ball",
  "type": "toy",
  "description": "A fun toy for dogs",
  "price": 12.99,
  "stock": 50,
  "size": "M",
  "imageUrl": "https://example.com/image.jpg",
  "createdAt": "2023-10-27T10:00:00Z",
  "updatedAt": "2023-10-27T10:00:00Z"
}
```

### Accessory Types

- `toy` - Play items (balls, squeaky toys, puzzles)
- `food` - Pet food and treats
- `collar` - Collars, harnesses, leashes
- `bedding` - Beds, blankets, crates
- `grooming` - Brushes, shampoos, nail clippers
- `other` - Miscellaneous accessories

### Size Categories

- `S` - Small
- `M` - Medium
- `L` - Large
- `XL` - Extra Large

## Testing

### Using REST Client

Open `accessory-service.http` in VS Code with the REST Client extension.

### Using Test Script

```bash
# In a separate terminal, with the service running
python test_api.py
```

### Using curl

```bash
# Health check
curl http://localhost:8030/health

# List all accessories
curl http://localhost:8030/api/accessories

# Create accessory
curl -X POST http://localhost:8030/api/accessories \
  -H "Content-Type: application/json" \
  -d '{"name": "Ball", "type": "toy", "price": 9.99, "stock": 20, "size": "M"}'

# Filter by type
curl "http://localhost:8030/api/accessories?type=toy"

# Low stock only
curl "http://localhost:8030/api/accessories?lowStockOnly=true"
```

## Architecture

```
accessory-service/
├── config.py          # Configuration and settings
├── models.py          # Pydantic data models
├── database.py        # CosmosDB service layer
├── main.py            # FastAPI application
├── requirements.txt   # Python dependencies
├── start.sh           # Startup script
├── test_api.py        # API test script
├── accessory-service.http  # REST Client tests
└── README.md          # This file
```

## Low Stock Threshold

Items with `stock < 10` are considered "low stock" and can be filtered using `?lowStockOnly=true`.

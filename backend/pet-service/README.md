# Pet Service

A Python FastAPI REST API for pet management with Azure CosmosDB backend.

## Features

- **Full CRUD operations** for pet management
- **Azure CosmosDB** integration with key-based authentication
- **Search and filtering** capabilities (by name, species, notes)
- **Pagination** support for large datasets
- **Comprehensive error handling** and logging
- **OpenAPI/Swagger** documentation
- **Health check endpoints** for monitoring
- **CORS support** for web applications

## API Endpoints

### Base URL: `/api/pets`

- `GET /api/pets` - Get pets with optional filtering
  - Query parameters: `search`, `species`, `status`, `limit`, `offset`
- `POST /api/pets` - Create a new pet
- `GET /api/pets/{id}` - Get a specific pet by ID
- `PATCH /api/pets/{id}` - Update a pet (partial update)
- `DELETE /api/pets/{id}` - Delete a pet

### Health Endpoints

- `GET /` - Root endpoint with basic info
- `GET /health` - Comprehensive health check including database connectivity

## Pet Model

```json
{
  "id": "uuid",
  "name": "Luna",
  "species": "dog|cat|bird|other",
  "ageYears": 3,
  "health": 0-100,
  "happiness": 0-100,
  "energy": 0-100,
  "avatarUrl": "https://...",
  "notes": "string",
  "createdAt": "2025-01-01T00:00:00",
  "updatedAt": "2025-01-01T00:00:00"
}
```

## Setup

### Prerequisites

- Python 3.8+
- Azure CosmosDB account with NoSQL API
- Azure authentication (managed identity preferred, or service principal)

### Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Set required environment variables:
   - `COSMOS_ENDPOINT`: Your CosmosDB endpoint URL
   - `COSMOS_KEY`: Your CosmosDB primary or secondary key
   - `COSMOS_DATABASE_NAME`: Database name (default: "petservice")
   - `COSMOS_CONTAINER_NAME`: Container name (default: "pets")

### Authentication

The Pet Service uses **key-based authentication** for CosmosDB access:

#### For Production (Azure CosmosDB)
- Set `COSMOS_ENDPOINT` to your CosmosDB account endpoint (e.g., `https://your-account.documents.azure.com:443/`)
- Set `COSMOS_KEY` to your CosmosDB primary or secondary key (found in Azure Portal under Keys section)

#### For Local Development (CosmosDB Emulator)
- Set `COSMOS_ENDPOINT` to `https://localhost:8081/`
- Set `COSMOS_KEY` to the emulator's default key: `C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==`

### CosmosDB Setup

#### Option 1: Local Development with CosmosDB Emulator
1. [Download and install CosmosDB Emulator](https://docs.microsoft.com/en-us/azure/cosmos-db/local-emulator)
2. Start the emulator (usually available at `https://localhost:8081/`)
3. Use the default emulator settings in `.env`:
   ```bash
   COSMOS_ENDPOINT=https://localhost:8081/
   COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
   ```
4. The database and container will be created automatically when you first add a pet

#### Option 2: Production with Azure CosmosDB
1. Create a CosmosDB account with NoSQL API
2. Create a database named `petservice` (or your preferred name)
3. Create a container named `pets` with partition key `/id`
4. Get your CosmosDB access key:
   - In Azure Portal, navigate to your CosmosDB account
   - Go to "Keys" section
   - Copy the "Primary Key" or "Secondary Key"

## Running the Application

### Quick Start
```bash
# Use the provided startup script (recommended)
./start.sh
```

### Development
```bash
python main.py
```

### Production
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

> **Note**: The application uses lazy initialization for CosmosDB connections. The API will start successfully even if CosmosDB is not available. Database connections are established only when needed (e.g., when accessing pet data).

### Docker (Optional)
```bash
# Create Dockerfile if needed
docker build -t pet-service .
docker run -p 8000:8000 pet-service
```

## Startup Behavior

The Pet Service API uses **lazy initialization** for database connections:

- ✅ **API starts successfully** even if CosmosDB is not available
- ⚡ **Fast startup** - no database connection delays
- 🔄 **Automatic connection** when first database operation is needed
- 🏥 **Health endpoint** at `/health` shows database connectivity status
- 🛠️ **Auto-setup** - creates database/container and seeds sample data if they don't exist

### Auto Database Setup

When you first access the `/health` endpoint or make any API call:
- If database doesn't exist → automatically created
- If container doesn't exist → automatically created with proper partition key (`/id`)
- If container is empty → seeded with sample pets:
  - **Luna** (dog): "Loves fetch"
  - **Milo** (cat): "Window watcher"  
  - **Pico** (bird): "Chirpy"

This design allows for:
- **Zero-configuration development** - just start the emulator and go!
- Local development without manual database setup
- Graceful handling of temporary database outages
- Container orchestration scenarios where services start in any order

## API Documentation

Once running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health

## Usage Examples

### Create a Pet
```bash
curl -X POST "http://localhost:8000/api/pets" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Luna",
    "species": "dog",
    "ageYears": 3,
    "health": 85,
    "happiness": 90,
    "energy": 75,
    "avatarUrl": "https://example.com/luna.jpg",
    "notes": "Friendly golden retriever"
  }'
```

### Get All Pets
```bash
curl "http://localhost:8000/api/pets"
```

### Search Pets
```bash
curl "http://localhost:8000/api/pets?search=luna&species=dog&limit=10"
```

### Update a Pet
```bash
curl -X PATCH "http://localhost:8000/api/pets/{pet_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "health": 90,
    "happiness": 95
  }'
```

### Delete a Pet
```bash
curl -X DELETE "http://localhost:8000/api/pets/{pet_id}"
```

## Architecture

The application follows clean architecture principles:

- **`main.py`**: FastAPI application and route definitions
- **`models.py`**: Pydantic data models for validation
- **`database.py`**: CosmosDB service layer with Azure best practices
- **`config.py`**: Configuration management
- **`requirements.txt`**: Python dependencies

## Azure Best Practices Implemented

- **Authentication**: Uses secure key-based authentication for CosmosDB
- **Error Handling**: Comprehensive error handling with proper HTTP status codes
- **Logging**: Structured logging for monitoring and debugging
- **Security**: No hardcoded credentials, uses environment variables
- **Performance**: Connection pooling, retry logic, and pagination
- **Monitoring**: Health check endpoints for service monitoring
- **Documentation**: OpenAPI/Swagger for API documentation

## Troubleshooting

### Common Issues

1. **CosmosDB Emulator Not Running**: 
   - The API will start successfully but `/health` will show unhealthy status
   - Install and start [CosmosDB Emulator](https://docs.microsoft.com/en-us/azure/cosmos-db/local-emulator)
   - Or use a cloud CosmosDB instance with proper endpoint and key

2. **Authentication Error**: 
   - Verify your `COSMOS_KEY` is correct and has proper permissions
   - For emulator, use the default key provided in `.env.example`

3. **SSL/Certificate Error**: 
   - If using localhost emulator, ensure endpoint uses `https://localhost:8081/`
   - For production, ensure endpoint uses `https://`

4. **Import/Dependency Errors**: 
   - Run `pip install -r requirements.txt` to install dependencies
   - Or use `./start.sh` which handles installation automatically

### Logging

The application uses structured logging. Check logs for detailed error information:
- INFO level: Normal operations, requests, responses
- ERROR level: Errors and exceptions
- DEBUG level: Detailed query information (if enabled)

## License

MIT License - see LICENSE file for details.
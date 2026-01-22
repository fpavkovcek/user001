# Activity Service API

A RESTful API service for managing pet activities, built with FastAPI and Azure CosmosDB.

## Features

- **Complete CRUD Operations**: Create, read, and delete pet activities
- **Advanced Filtering**: Filter by pet ID, activity type, date ranges with pagination
- **Activity Types**: Support for feed, walk, play, vet, and train activities
- **Auto-Setup**: Automatically creates database/container with sample data
- **Azure CosmosDB**: Scalable NoSQL database backend with partition key optimization
- **FastAPI**: Modern, fast web framework with automatic API documentation
- **Type Safety**: Full Pydantic validation and type checking
- **Development Ready**: Docker support, REST Client tests, and comprehensive documentation

## Quick Start

### Prerequisites

- Python 3.9+
- Azure CosmosDB Emulator or Azure CosmosDB account
- Git

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd backend/activity-service
   ```

2. **Install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your CosmosDB settings
   ```

4. **Start the service:**
   ```bash
   ./start.sh
   # or
   uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   ```

## Configuration

The service uses environment variables for configuration. Copy `.env.example` to `.env` and update:

```bash
# Azure CosmosDB Configuration
COSMOS_ENDPOINT=https://localhost:8081/  # CosmosDB Emulator
COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==

# Application Configuration  
APP_NAME=Activity Service
APP_VERSION=1.0.0
DEBUG=True
LOG_LEVEL=INFO
```

### CosmosDB Setup

**Local Development (Recommended):**
- Install [Azure CosmosDB Emulator](https://docs.microsoft.com/en-us/azure/cosmos-db/local-emulator)
- Use the default configuration in `.env`

**Production:**
- Create an Azure CosmosDB account
- Update `COSMOS_ENDPOINT` and `COSMOS_KEY` in `.env`

## API Endpoints

### Health Check
- `GET /health` - Health check with auto-database setup

### Activities
- `GET /api/activities` - Get activities with optional filtering
  - Query parameters: `petId`, `type`, `from`, `to`, `limit`, `offset`
- `POST /api/activities` - Create a new activity
- `GET /api/activities/{id}` - Get a specific activity
- `DELETE /api/activities/{id}` - Delete an activity

### Documentation
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation
- `GET /openapi.json` - OpenAPI schema

## Activity Model

```json
{
  "id": "uuid",
  "petId": "uuid", 
  "type": "feed|walk|play|vet|train",
  "timestamp": "2025-10-06T19:00:00Z",
  "notes": "Optional notes about the activity",
  "createdAt": "2025-10-06T19:00:00Z",
  "updatedAt": "2025-10-06T19:00:00Z"
}
```

## Usage Examples

### Create an Activity
```bash
curl -X POST "http://localhost:8001/api/activities" \
  -H "Content-Type: application/json" \
  -d '{
    "petId": "p1",
    "type": "walk", 
    "timestamp": "2025-10-06T18:30:00Z",
    "notes": "30 minute park walk"
  }'
```

### Get Activities by Pet
```bash
curl "http://localhost:8001/api/activities?petId=p1"
```

### Get Activities by Type and Date Range
```bash
curl "http://localhost:8001/api/activities?type=feed&from=2025-10-06T00:00:00Z&to=2025-10-06T23:59:59Z"
```

### Delete an Activity
```bash
curl -X DELETE "http://localhost:8001/api/activities/{activity-id}"
```

## Testing

### REST Client (VS Code)
1. Install the [REST Client extension](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)
2. Open `activity-service.http`
3. Click "Send Request" for any request

### Sample Data
The health check automatically creates sample activities:
- Walk activity for pet p1: "Park loop" 
- Feed activity for pet p2: "Tuna pouch"
- Play activity for pet p1: "Frisbee"

## Development

### Project Structure
```
activity-service/
├── main.py              # FastAPI application and routes
├── models.py            # Pydantic data models
├── database.py          # CosmosDB service layer
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── .env.example        # Environment template
├── .env                # Environment configuration
├── start.sh            # Startup script
├── activity-service.http # REST Client tests
└── README.md           # This file
```

### Key Features

**Auto-Database Setup:**
- Database and container creation on first health check
- Automatic sample data seeding for immediate testing
- Partition key optimization for performance

**Advanced Filtering:**
- Filter by pet ID for pet-specific activities
- Filter by activity type (feed, walk, play, vet, train)
- Date range filtering with ISO timestamp support
- Pagination with offset and limit

**Error Handling:**
- Comprehensive validation with detailed error messages
- Proper HTTP status codes and responses
- Graceful handling of database connection issues

**Performance:**
- Lazy database initialization for fast startup
- Efficient CosmosDB queries with proper indexing
- Connection pooling and resource management

### Running in Production

1. **Environment Setup:**
   - Use a real Azure CosmosDB account
   - Set production-appropriate environment variables
   - Configure proper CORS settings

2. **Deployment Options:**
   - Azure Container Instances
   - Azure App Service
   - Docker containers
   - Kubernetes

3. **Security:**
   - Replace default CosmosDB keys with production keys
   - Configure HTTPS/TLS
   - Implement authentication if needed

## Architecture

The Activity Service follows a layered architecture:

- **API Layer** (`main.py`): FastAPI routes and HTTP handling
- **Service Layer** (`database.py`): Business logic and CosmosDB operations  
- **Model Layer** (`models.py`): Data validation and serialization
- **Configuration** (`config.py`): Environment and settings management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

This project is part of the MicroHack GitHub workshop.

## Support

For issues and questions:
- Check the health endpoint: `GET /health`
- Review logs for detailed error information
- Ensure CosmosDB emulator is running for local development
- Verify environment configuration in `.env`
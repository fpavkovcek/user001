# MicroHack Backend Services

Complete backend implementation for the Pet Management System with both Pet Service and Activity Service APIs.

## Quick Start

### 🚀 Start Both Services (Recommended)

```bash
# Start both Pet Service (port 8000) and Activity Service (port 8001)
./start.sh
```

This script will:
- ✅ Check port availability (8000, 8001)
- ✅ Set up virtual environments for both services
- ✅ Install all required dependencies
- ✅ Create .env files from examples if needed
- ✅ Start both services with auto-reload
- ✅ Monitor service health and provide detailed logs

### 🛑 Stop Services

Press `Ctrl+C` in the terminal running `./start.sh` to stop both services gracefully.

## Individual Service Setup

### Pet Service (Port 8000)

```bash
cd backend/pet-service
./start.sh
# or
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Activity Service (Port 8001)

```bash
cd backend/activity-service
./start.sh
# or
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## Service URLs

### 🐾 Pet Service
- **API Base:** http://localhost:8000
- **Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **OpenAPI Schema:** http://localhost:8000/openapi.json

### 📊 Activity Service
- **API Base:** http://localhost:8001
- **Documentation:** http://localhost:8001/docs
- **Health Check:** http://localhost:8001/health
- **OpenAPI Schema:** http://localhost:8001/openapi.json

## API Endpoints

### Pet Service (`/api/pets`)
- `GET /api/pets` - List pets with filtering and pagination
- `POST /api/pets` - Create a new pet
- `GET /api/pets/{id}` - Get specific pet
- `PATCH /api/pets/{id}` - Update pet
- `DELETE /api/pets/{id}` - Delete pet

### Activity Service (`/api/activities`)
- `GET /api/activities` - List activities with filtering and pagination
- `POST /api/activities` - Create a new activity
- `GET /api/activities/{id}` - Get specific activity
- `DELETE /api/activities/{id}` - Delete activity

## Testing

### REST Client (VS Code)

1. Install the [REST Client extension](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)
2. Open the test files:
   - `backend/pet-service/pet-service.http`
   - `backend/activity-service/activity-service.http`
3. Click "Send Request" above any request

### Sample Requests

**Create a Pet:**
```http
POST http://localhost:8000/api/pets
Content-Type: application/json

{
  "name": "Luna",
  "species": "dog",
  "ageYears": 3,
  "health": 85,
  "happiness": 90,
  "energy": 75,
  "notes": "Friendly golden retriever"
}
```

**Create an Activity:**
```http
POST http://localhost:8001/api/activities
Content-Type: application/json

{
  "petId": "p1",
  "type": "walk",
  "timestamp": "2025-10-06T18:30:00Z",
  "notes": "30 minute neighborhood walk"
}
```

## Prerequisites

### Azure CosmosDB

**Option 1: Local Development (Recommended)**
- Install [Azure CosmosDB Emulator](https://docs.microsoft.com/en-us/azure/cosmos-db/local-emulator)
- Default endpoint: `http://localhost:8081`
- Services will auto-create databases and sample data

**Option 2: Azure CosmosDB**
- Create an Azure CosmosDB account
- Update `.env` files with your credentials:
  ```bash
  COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
  COSMOS_KEY=your-primary-key-here
  ```

### Python Requirements
- Python 3.9+
- Virtual environment support
- All dependencies listed in `requirements.txt` files

## Project Structure

```
MicroHack-GitHub/
├── start.sh                     # Main startup script
├── README.md                    # This file
└── backend/
    ├── pet-service/             # Pet management API
    │   ├── main.py             # FastAPI application
    │   ├── models.py           # Pet data models
    │   ├── database.py         # CosmosDB service
    │   ├── config.py           # Configuration
    │   ├── pet-service.http    # REST Client tests
    │   └── requirements.txt    # Dependencies
    └── activity-service/        # Activity management API
        ├── main.py             # FastAPI application
        ├── models.py           # Activity data models
        ├── database.py         # CosmosDB service
        ├── config.py           # Configuration
        ├── activity-service.http # REST Client tests
        └── requirements.txt    # Dependencies
```

## Features

### 🏗️ Auto-Setup
- Databases and containers created automatically
- Sample data seeded on first run
- Zero-configuration development experience

### 🔍 Advanced Filtering
- **Pets:** Search by name/notes, filter by species, pagination
- **Activities:** Filter by pet ID, activity type, date ranges, pagination

### 🛡️ Production Ready
- Comprehensive error handling and validation
- Structured logging and monitoring
- Type safety with Pydantic models
- Azure best practices implementation

### 🚀 Developer Experience
- Hot reload during development
- Comprehensive API documentation
- REST Client test suites
- Detailed health checks and diagnostics

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the ports
lsof -i :8000
lsof -i :8001

# Kill processes if needed
kill -9 <PID>
```

### CosmosDB Connection Issues
- Ensure CosmosDB Emulator is running
- Check firewall settings for port 8081
- Verify `.env` configuration files

### Service Logs
- Pet Service: `backend/pet-service/pet-service.log`
- Activity Service: `backend/activity-service/activity-service.log`

## Development

### Adding New Features
1. Update models in `models.py`
2. Add database operations in `database.py`
3. Create API endpoints in `main.py`
4. Add tests to REST Client files

### Configuration
- Environment variables in `.env` files
- Settings management via `config.py`
- Database names configurable per service

## License

This project is part of the MicroHack GitHub workshop.

---

**Happy coding! 🚀**

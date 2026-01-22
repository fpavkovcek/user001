# Challenge 06: Design a new microservice with Copilot

## Overview
In this challenge we will prepare specifications for new service `accessory-service` which busines requirements we added to `PRD.md` in one of our previous challenges. Review specs templates in [constituion repo](https://github.com/CZSK-MicroHacks/MicroHack-GitHub-engineering-constitution/tree/main) and also check our platform specs and specs for our two services in `specs` folder.

## Create specifications for accessory service
We have our business requirements and we will now use Copilot to help us articulate our technical solution decissions (APIs, data models) into proper specs. Use following prompt:


```markdown
You task is to create technical specification for our new service accessory-service.

Business requirements are covered in #PRD.md

Here are templates - make sure you use each template and fill in details of our service as my definition bellow.

https://raw.githubusercontent.com/CZSK-MicroHacks/MicroHack-GitHub-engineering-constitution/refs/heads/main/specs-template/services/service-sample/API_REFERENCE.md
https://raw.githubusercontent.com/CZSK-MicroHacks/MicroHack-GitHub-engineering-constitution/refs/heads/main/specs-template/services/service-sample/DATA_MODELS.md
https://raw.githubusercontent.com/CZSK-MicroHacks/MicroHack-GitHub-engineering-constitution/refs/heads/main/specs-template/services/service-sample/DEPLOYMENT.md
https://raw.githubusercontent.com/CZSK-MicroHacks/MicroHack-GitHub-engineering-constitution/refs/heads/main/specs-template/services/service-sample/SECURITY.md
https://raw.githubusercontent.com/CZSK-MicroHacks/MicroHack-GitHub-engineering-constitution/refs/heads/main/specs-template/services/service-sample/ARCHITECTURE.md

Here are steps how to proceed:
1. Locate `specs/platform/ARCHITECTURE.md` and briefly modify it to inlcude our new accessory service
2. Read existing specifications in `specs/services` as some of parts, eg. configuration management as described in service ARCHITECTURE.md should be consistent and identical where possible.
3. Analyze our following technical details and incorporate them into specs files

### 3.1. Requirements
- **Core functionality**: Manage pet accessories with CRUD operations
- **Search & Filter**: Support filtering by type, low stock detection, text search
- **Pagination**: Handle large datasets with offset/limit pagination
- **Data types**: Support 6 accessory types (toy, food, collar, bedding, grooming, other)
- **Size categories**: S, M, L, XL
- **Stock management**: Track quantity and identify low stock items (< 10)

### 3.2. Database
Use **CosmosDB** for data persistency much like with other services.

**Lazy Initialization Pattern:**
   - Don't connect to Cosmos DB during `__init__()`
   - Connect only when first operation is attempted
   - Use `_ensure_initialized()` before each database operation

**Health Check with Auto-Setup:**
   - Try to query the container
   - If database/container doesn't exist, create it automatically
   - Seed with 2 sample accessories (one toy, one food item with low stock)

**Search Implementation:**
   - Build dynamic SQL query based on filters
   - Emulator do NOT support tautologies like `WHERE 1=1`, do not use it to simply concat filters, implement proper list-building patterns
   - Support text search in name and description (`CONTAINS`)
   - Support type filtering
   - Support low stock filtering (stock < 10)
   - Add pagination with `OFFSET` and `LIMIT`
   - Order results by `createdAt DESC`

**Error Handling:**
   - Catch `CosmosResourceNotFoundError` for 404 cases
   - Catch `CosmosResourceExistsError` for duplicate IDs
   - Log all operations and errors
   - Re-raise exceptions for FastAPI to handle

### 3.3 Data models
Base fields (required for all accessories):
- name: str (1-200 chars)
- type: Literal["toy", "food", "collar", "bedding", "grooming", "other"]
- price: float (>= 0)
- stock: int (>= 0)
- size: Literal["S", "M", "L", "XL"]

Optional fields:
- imageUrl: Optional[str]
- description: Optional[str] (max 2000 chars)

System fields (auto-generated):
- id: str (UUID, auto-generated)
- createdAt: datetime (auto-set on creation)
- updatedAt: datetime (auto-set on creation/update)

**Models to Implement:**
- **AccessoryBase** - Base model with common fields
- **AccessoryCreate** - For POST requests (no id, timestamps)
- **AccessoryUpdate** - For PATCH requests (all fields optional)
- **Accessory** - Complete model with id and timestamps
- **AccessorySearchFilters** - Query parameters for search/filter

**Validation Points:**
- Price must be non-negative
- Stock must be non-negative
- Type must be one of the 6 valid types
- Size must be S, M, L, or XL
- Name length between 1-200 characters

### 3.4 APIs
**API Endpoints** (to be implemented):
   - `GET /` - Root endpoint with service info
   - `GET /health` - Health check with database connectivity
   - `GET /api/accessories` - List accessories with filtering and pagination
   - `POST /api/accessories` - Create new accessory
   - `GET /api/accessories/{id}` - Get specific accessory
   - `PATCH /api/accessories/{id}` - Update accessory (partial)
   - `DELETE /api/accessories/{id}` - Delete accessory

**Query Parameters for List Endpoint:**
   - `search` (Optional[str]) - Search in name or description
   - `type` (Optional[str]) - Filter by accessory type
   - `lowStockOnly` (Optional[bool]) - Show only items with stock < 10
   - `limit` (int, default=100) - Max results to return
   - `offset` (int, default=0) - Pagination offset
```

Review results, modify if needed.

## Success criteria

- [ ] `specs/platform/ARCHITECTURE.md` is updated to include `accessory-service`
- [ ] `specs/services/accessory-service` folder is created and contains all required specification files (`API_REFERENCE.md`, `DATA_MODELS.md`, `DEPLOYMENT.md`, `SECURITY.md`, `ARCHITECTURE.md`)
- [ ] Specifications accurately reflect the technical requirements (CosmosDB, Data Models, API endpoints) and business rules defined in the challenge 




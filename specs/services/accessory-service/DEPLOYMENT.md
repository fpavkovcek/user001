```markdown
# Service Deployment Plan

Describe how this service moves from commit to production, referencing shared workflows in `../../platform/DEPLOYMENT.md`.

## Pipelines

### CI Stages
1. **Linting**: `flake8` / `pylint` for code quality.
2. **Unit Tests**: `pytest` for models and business logic.
3. **Integration Tests**: Tests against Cosmos DB Emulator.
4. **Build Docker Image**: `backend/accessory-service/Dockerfile`.

### CD Stages
1. **Push to ACR**: Azure Container Registry.
2. **Deploy to Azure Container Apps**: `accessory-service` container app.
3. **Verification**: `/health` endpoint check confirms database connectivity.

## Environments

| Environment | Branch/Artifact | Purpose | Approvals |
| --- | --- | --- | --- |
| **Local** | Feature Branch | Development and testing (Docker Compose with Cosmos DB Emulator) | None |
| **Production** | `main` | Live Traffic | PR Review |

## Release Steps

### 1. Preconditions
- Cosmos DB account must be provisioned.
- Database `accessoryservice` and container `accessories` will be auto-created on first health check if they don't exist.
- Environment variables configured:
  - `COSMOS_ENDPOINT` (required)
  - `COSMOS_KEY` (required for local/emulator; Managed Identity for production)

### 2. Deployment Procedure
1. **Merge to main**: GitHub Actions workflow triggers automatically.
2. **Infrastructure Update**: Bicep ensures infrastructure is up to date.
3. **Container Build**: Docker image built and pushed to ACR.
4. **Container App Revision**: New revision deployed to Azure Container Apps.
5. **Health Check**: Automated health check verifies database connectivity.

### 3. Verification
- **Automated**: Health endpoint returns `{"status": "healthy"}`.
- **Manual Smoke Test** (optional):
  - Create an accessory via POST `/api/accessories`.
  - Retrieve it via GET `/api/accessories/{id}`.
  - Verify filtering works via GET `/api/accessories?lowStockOnly=true`.

### 4. Rollback
- Azure Container Apps maintains previous revisions.
- Rollback by redirecting traffic to previous revision via Azure Portal or CLI.

## Infrastructure

### Compute
- **Azure Container App**: `accessory-service`
- **Scaling**: KEDA-based autoscaling (0-N replicas based on HTTP traffic).

### Database
- **Azure Cosmos DB Account**: Shared with other services.
- **Database**: `accessoryservice`
- **Container**: `accessories`
- **Partition Key**: `/id`
- **Throughput**: Serverless (auto-scale based on usage).

### IaC Definitions
| Resource | Bicep File |
| --- | --- |
| Container App | `infra/container-app.accessory-service.bicep` |
| Cosmos DB | `infra/cosmos.bicep` |
| ACR | `infra/acr.bicep` |
| Environment | `infra/container-app-environment.bicep` |

## Local Development

### Using Docker Compose
```bash
# Start all services including Cosmos DB Emulator
docker-compose up -d

# Or run accessory-service standalone
cd backend/accessory-service
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8003
```

### Environment Variables (Local)
```bash
COSMOS_ENDPOINT=https://localhost:8081
COSMOS_KEY=<emulator-key>
```

### Health Check Auto-Setup
On first health check, the service will:
1. Connect to Cosmos DB.
2. Create `accessoryservice` database if it doesn't exist.
3. Create `accessories` container if it doesn't exist.
4. Seed 2 sample accessories (toy and food with low stock).

## Monitoring

### Health Endpoint
- **URL**: `/health`
- **Expected Response**: `{"status": "healthy", "database": "connected", "container": "accessories"}`
- **Failure Indicator**: Status code 503, `{"status": "unhealthy", "error": "..."}`

### Logs
- Structured JSON logs with request ID and operation details.
- All database operations and errors are logged.
- Application Insights integration for production monitoring.

### Metrics
- HTTP request latency and status codes.
- Cosmos DB RU consumption.
- Container App scaling events.

```

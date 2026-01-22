# Service Deployment Plan

Describe how this service moves from commit to production, referencing shared workflows in `../../platform/DEPLOYMENT.md`.

## Pipelines
- **CI Stages**:
    - Linting.
    - Unit Tests.
    - Build Docker Image (`backend/activity-service/Dockerfile`).
- **CD Stages**:
    - Push to ACR.
    - Deploy to Azure Container Apps (`activity-service`).
    - Verification: `/health` endpoint check.

## Environments

| Environment | Branch/Artifact | Purpose | Approvals |
| --- | --- | --- | --- |
| **Local** | Feature Branch | Dev/Test (Docker Compose) | None |
| **Production** | `main` | Live Traffic | PR Review |

## Release Steps
1.  **Preconditions**: Cosmos DB `activityservice` database and `activities` container must exist.
2.  **Deployment**:
    -   GitHub Actions workflow triggers on push to `main`.
    -   Bicep ensures infrastructure is up to date.
    -   Container App revision is updated.
3.  **Verification**:
    -   Automated health check.

## Infrastructure
-   **Compute**: Azure Container App (`activity-service`).
-   **Database**: Azure Cosmos DB Account -> Database `activityservice` -> Container `activities`.
-   **IaC**: `infra/container-app.activity-service.bicep`, `infra/cosmos.bicep`.

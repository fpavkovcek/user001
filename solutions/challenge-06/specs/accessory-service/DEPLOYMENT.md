# Service Deployment Plan

Describe how this service moves from commit to production, referencing shared workflows in `../../platform/DEPLOYMENT.md`.

## Pipelines
- **CI Stages**:
    - Linting (`flake8` / `pylint`).
    - Unit Tests (`pytest`).
    - Build Docker Image (`backend/accessory-service/Dockerfile`).
- **CD Stages**:
    - Push to ACR.
    - Deploy to Azure Container Apps (`accessory-service`).
    - Verification: `/health` endpoint check.

## Environments

| Environment    | Branch/Artifact | Purpose                   | Approvals |
| -------------- | --------------- | ------------------------- | --------- |
| **Local**      | Feature Branch  | Dev/Test (Docker Compose) | None      |
| **Production** | `main`          | Live Traffic              | PR Review |

## Release Steps
1.  **Preconditions**: Cosmos DB `accessory-service` database and `accessories` container must exist.
2.  **Deployment**:
    -   GitHub Actions workflow triggers on push to `main`.
    -   Bicep ensures infrastructure is up to date.
    -   Container App revision is updated.
3.  **Verification**:
    -   Automated health check.
    -   Manual smoke test (optional).

## Infrastructure
-   **Compute**: Azure Container App (`accessory-service`).
-   **Database**: Azure Cosmos DB Account -> Database `accessory-service` -> Container `accessories`.
-   **IaC**: `infra/container-app.accessory-service.bicep`, `infra/cosmos.bicep`.

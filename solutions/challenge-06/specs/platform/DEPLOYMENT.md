# Shared Deployment Strategy

Capture the release workflow and infrastructure expectations that apply across all services in the monorepo.

## Environments

| Environment | Purpose | Source Branch / Tag | Promotion Criteria |
| --- | --- | --- | --- |
| **Local** | Development and functional testing. Uses Docker Compose and Cosmos DB Emulator. | Feature Branches | Developer verification (tests pass locally). |
| **Production** | Live user traffic. Uses Azure Container Apps and Cosmos DB Serverless. | `main` | Successful CI pipeline run, Code Review approval. |

## CI/CD Pipeline

### Strategy
We utilize **GitHub Actions** for continuous integration and deployment. The pipeline is triggered on push to `main` and Pull Requests.

### Stages
1.  **Build & Test**:
    -   Linting (code style checks).
    -   Unit Tests (pytest).
    -   Build Docker images.
2.  **Infrastructure as Code (IaC)**:
    -   Validate Bicep templates.
    -   Deploy/Update Azure resources (Cosmos DB, Container App Environment) using Bicep.
3.  **Deploy Services**:
    -   Push container images to Azure Container Registry (ACR).
    -   Update Container Apps with new image revisions.
4.  **Verification**:
    -   Health check endpoints (`/health`).

### Authentication
-   **GitHub to Azure**: Uses **Workload Identity Federation** (Managed Identity) to eliminate long-lived secrets.

## Release Patterns

-   **Rolling Updates**: Azure Container Apps default. New revisions are spun up, traffic is shifted, and old revisions are decommissioned.
-   **Manual Deployment (Initial)**: Initial setup involves running `start.sh` or `deploy.sh` scripts locally to bootstrap the environment.
-   **Automated Deployment (Target)**: Full automation via GitHub Actions.

## Approvals & Compliance

-   **Code Review**: All changes to `main` require a Pull Request with at least one peer review.
-   **Security**:
    -   Future: DevSecOps integration (SAST/DAST).
    -   Compliance: No PII/PHI in demo data.

## Specification by Example

| Scenario | Given | When | Then |
| --- | --- | --- | --- |
| **New Feature Deployment** | A developer merges a PR to `main` | The GitHub Actions workflow completes successfully | The new version is live in Production without downtime. |
| **Infrastructure Change** | A change is made to `infra/cosmos.bicep` | The pipeline runs | Bicep `what-if` is checked, and changes are applied incrementally to the Azure resource group. |

Services should reference this file in their local `DEPLOYMENT.md` and capture only the additional, service-specific steps (custom feature flags, data migrations, dependency sequencing).

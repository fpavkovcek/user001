# PetPal Infrastructure as Code (Bicep)

This directory contains the Infrastructure as Code (IaC) implementation for the PetPal microservices application using Azure Bicep.

## Architecture Overview

The infrastructure provisions the following Azure resources:

### Core Infrastructure
- **Azure Container Apps Environment**: Managed environment for hosting container apps
- **Log Analytics Workspace**: Centralized logging and monitoring
- **Azure Cosmos DB**: Serverless NoSQL database for all microservices
- **GitHub Deployment Identity**: User-assigned managed identity secured with federated credentials

### Application Services
- **Pet Service**: Container App using hello world container (port 80) - infrastructure provisioning phase
- **Activity Service**: Container App using hello world container (port 80) - infrastructure provisioning phase
- **Accessory Service**: Container App using hello world container (port 80) - infrastructure provisioning phase
- **Frontend**: Container App for the web UI (port 80)

> **Note**: Backend services currently use `mcr.microsoft.com/azuredocs/containerapps-helloworld:latest` as placeholder containers. This approach:
> - Validates the infrastructure setup works correctly
> - Provisions all necessary Azure resources
> - Configures environment variables and secrets for future service deployment
> - Allows testing networking, logging, and monitoring before deploying actual services
> 
> When actual service images are available, update the Bicep modules to replace the hello world image references.

## File Structure

```
infra/
├── main.bicep                           # Main orchestration template (includes GitHub managed identity)
├── main.parameters.json                 # Default parameter values
├── cosmos.bicep                         # Cosmos DB configuration
├── container-app-environment.bicep      # Container Apps environment
├── container-app.pet-service.bicep      # Pet service container app
├── container-app.activity-service.bicep # Activity service container app
├── container-app.accessory-service.bicep# Accessory service container app
├── container-app.frontend.bicep         # Frontend container app
└── README.md                            # This file
```

## Prerequisites

1. **Azure CLI** installed and configured
   ```bash
   az version
   az login
   ```

2. **Azure Subscription** with appropriate permissions
   ```bash
   az account show
   az account set --subscription <subscription-id>
   ```

3. **Resource Group** created
   ```bash
   az group create --name <resource-group-name> --location eastus
   ```

## Deployment

### Using Azure CLI

1. **Validate the deployment** (optional but recommended):
   ```bash
   az deployment group validate \
     --resource-group <resource-group-name> \
     --template-file main.bicep \
     --parameters main.parameters.json
   ```

2. **Deploy the infrastructure**:
   ```bash
   az deployment group create \
     --resource-group <resource-group-name> \
     --template-file main.bicep \
     --parameters main.parameters.json \
     --name petpal-infrastructure
   ```

3. **Monitor deployment progress**:
   ```bash
   az deployment group show \
     --resource-group <resource-group-name> \
     --name petpal-infrastructure
   ```

### Custom Parameters

You can override parameters at deployment time:

```bash
az deployment group create \
  --resource-group <resource-group-name> \
  --template-file main.bicep \
  --parameters \
    location=westus2 \
    environmentName=prod \
    frontendImage=ghcr.io/michalmar/petpal-ui:v1.0.0
```

## Parameters

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `location` | Azure region for resources | Resource group location | No |
| `environmentName` | Environment name (dev/staging/prod) | `dev` | No |
| `uniqueSuffix` | Unique suffix for resource names | Auto-generated | No |
| `frontendImage` | Frontend container image | `ghcr.io/michalmar/petpal-ui:latest` | No |
| `enableGitHubManagedIdentity` | Creates the user-assigned managed identity and RBAC role assignments | `true` | No |
| `githubRepository` | GitHub repository in `owner/name` format used when constructing subjects | `michalmar/MicroHack-GitHub` | No |
| `githubFederatedSubjects` | Array of GitHub OIDC subjects authorized to assume the identity | `['repo:${githubRepository}:ref:refs/heads/main']` | No |

> **Note**: Backend service image parameters have been removed as services use hello world containers during infrastructure provisioning phase.

## Outputs

After successful deployment, the following outputs are available:

```bash
az deployment group show \
  --resource-group <resource-group-name> \
  --name petpal-infrastructure \
  --query properties.outputs
```

| Output | Description |
|--------|-------------|
| `cosmosEndpoint` | Cosmos DB endpoint URL |
| `acrResourceId` | Azure Container Registry resource ID |
| `petServiceUrl` | Pet service FQDN (HTTPS) |
| `activityServiceUrl` | Activity service FQDN (HTTPS) |
| `accessoryServiceUrl` | Accessory service FQDN (HTTPS) |
| `frontendUrl` | Frontend application FQDN (HTTPS) |
| `githubManagedIdentityClientId` | Client ID for the federated managed identity |
| `githubManagedIdentityPrincipalId` | Object ID of the managed identity |
| `githubManagedIdentityResourceId` | Resource ID of the managed identity |

## Environment Variables

Each backend service (pets, activities, accessories) is configured with:

- `COSMOS_ENDPOINT`: Cosmos DB endpoint URL
- `COSMOS_KEY`: Cosmos DB primary key (stored as secret)
- `COSMOS_DATABASE_NAME`: Database name for the service
- `COSMOS_CONTAINER_NAME`: Container name for the service

The frontend is configured with:

- `VITE_API_PETS_URL`: Pet service API URL
- `VITE_API_ACTIVITIES_URL`: Activity service API URL
- `VITE_API_ACCESSORIES_URL`: Accessory service API URL

## Security Features

1. **Secrets Management**: Cosmos DB keys stored as Container App secrets
2. **HTTPS Only**: All ingress endpoints configured for HTTPS
3. **Serverless Cosmos DB**: Cost-effective, auto-scaling database
4. **Network Isolation**: Container Apps running in managed environment
5. **Minimal Privileges**: Each service only has access to required resources
6. **Federated CI/CD Identity**: GitHub deployments authenticate via workload identity federation—no stored client secrets

## Scaling Configuration

All services are configured with auto-scaling:

- **Backend Services**: 1-10 replicas based on HTTP concurrency (10 requests)
- **Frontend**: 1-5 replicas based on HTTP concurrency (50 requests)

## Cosmos DB Configuration

- **Capability Model**: Serverless (pay-per-request)
- **Consistency Level**: Session (default)
- **Locations**: Single region (same as deployment)
- **Free Tier**: Disabled

## Monitoring and Logging

All Container Apps send logs to the centralized Log Analytics workspace:

- **Retention**: 30 days
- **SKU**: Pay-as-you-go (PerGB2018)
- **Integration**: Automatic via Container Apps environment

## Managed Identity Federation for GitHub Actions

The deployment creates a user-assigned managed identity (`petpal-<env>-gha-mi-<suffix>`) that is bound to GitHub via workload identity federation. By default, it trusts `repo:michalmar/MicroHack-GitHub:ref:refs/heads/main`. Update the `githubFederatedSubjects` parameter to authorize additional branches, tags, or environments (for example `repo:owner/repo:environment:production`).

### Values required in GitHub

After provisioning, capture the following values:

| GitHub configuration | Value source |
|----------------------|--------------|
| `AZURE_CLIENT_ID` | `githubManagedIdentityClientId` output |
| `AZURE_TENANT_ID` | `az account show --query tenantId -o tsv` |
| `AZURE_SUBSCRIPTION_ID` | `az account show --query id -o tsv` |

Store them as repository or environment secrets before running workflows. The Azure Login action must request an ID token so that GitHub exchanges it for Azure access:

```yaml
- name: Azure login (workload identity)
  uses: azure/login@v2
  with:
    auth-type: ID_TOKEN
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

The template also creates a `federatedIdentityCredential` per entry in `githubFederatedSubjects`, so no manual setup is required unless you need to add more subjects later.

### Role assignments

To support container deployments, the identity receives:

- `Contributor` on the resource group (manage Container Apps, Cosmos connection strings, and logging)
- `AcrPush` on the Azure Container Registry (push images without admin credentials)

Tailor these assignments if you prefer more granular roles.

## Cost Optimization

1. **Serverless Cosmos DB**: Pay only for consumed RU/s
2. **Container Apps**: Pay per vCPU-second and GiB-second
3. **Auto-scaling**: Scale to zero (min 1 replica currently configured)
4. **Log Analytics**: 5GB free tier, then pay-per-GB

## Cleanup

To remove all deployed resources:

```bash
az deployment group delete \
  --resource-group <resource-group-name> \
  --name petpal-infrastructure
```

Or delete the entire resource group:

```bash
az group delete --name <resource-group-name> --yes --no-wait
```

## Troubleshooting

### View deployment errors
```bash
az deployment group show \
  --resource-group <resource-group-name> \
  --name petpal-infrastructure \
  --query properties.error
```

### View Container App logs
```bash
az containerapp logs show \
  --name <container-app-name> \
  --resource-group <resource-group-name> \
  --follow
```

### Test service endpoints
```bash
# Get service URLs
FRONTEND_URL=$(az deployment group show \
  --resource-group <resource-group-name> \
  --name petpal-infrastructure \
  --query properties.outputs.frontendUrl.value -o tsv)

# Test frontend
curl -I $FRONTEND_URL
```

## Next Steps

After infrastructure provisioning:

1. **Deploy Application Code**: Build and push container images to registry
2. **Update Container Apps**: Configure continuous deployment
3. **Configure Custom Domains**: Add custom DNS records
4. **Enable Monitoring**: Set up Application Insights
5. **Implement CI/CD**: Automate deployments with GitHub Actions

## References

- [Azure Container Apps Documentation](https://docs.microsoft.com/azure/container-apps/)
- [Azure Cosmos DB Documentation](https://docs.microsoft.com/azure/cosmos-db/)
- [Bicep Documentation](https://docs.microsoft.com/azure/azure-resource-manager/bicep/)
- [Challenge 08: Infrastructure as Code](/challenges/challenge-08/README.md)

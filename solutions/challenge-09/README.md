# Solution: Challenge 09 - Deployment Automation using GitHub Actions

This solution demonstrates implementing comprehensive CI/CD pipelines with GitHub Actions, including best practices for automated testing, building, and deployment.

## Overview

This challenge focuses on creating production-ready CI/CD pipelines that automate the entire software delivery process from code commit to production deployment.

## Solution Implementation

### Quick Start: Test Your Deployment

Setup all necessary environment variables as in section 1.2 of [Challenge 08](../../challenges/challenge-09/README.md#12-set-github-secrets-and-variables).
```bash
  REPO_FULL=$(gh repo view --json nameWithOwner -q .nameWithOwner)

  # Get resource group from azd environment
  RESOURCE_GROUP=$(azd env get-value AZURE_RESOURCE_GROUP)

  echo "Repository: $REPO_FULL"
  echo "RESOURCE_GROUP=$RESOURCE_GROUP"
  
  PET_SERVICE_CONTAINER_APP_NAME=$(azd env get-value petServiceName)
  PET_SERVICE_FQDN=$(azd env get-value petServiceUrl)
  
  ACTIVITY_SERVICE_CONTAINER_APP_NAME=$(azd env get-value activityServiceName)
  ACTIVITY_SERVICE_FQDN=$(azd env get-value activityServiceUrl)
  
  ACCESSORY_SERVICE_CONTAINER_APP_NAME=$(azd env get-value accessoryServiceName)
  ACCESSORY_SERVICE_FQDN=$(azd env get-value accessoryServiceUrl)
  
  
  echo "PET_SERVICE_CONTAINER_APP_NAME=$PET_SERVICE_CONTAINER_APP_NAME"
  echo "PET_SERVICE_FQDN=$PET_SERVICE_FQDN"
  echo "ACTIVITY_SERVICE_CONTAINER_APP_NAME=$ACTIVITY_SERVICE_CONTAINER_APP_NAME"
  echo "ACTIVITY_SERVICE_FQDN=$ACTIVITY_SERVICE_FQDN"
  echo "ACCESSORY_SERVICE_CONTAINER_APP_NAME=$ACCESSORY_SERVICE_CONTAINER_APP_NAME"
  echo "ACCESSORY_SERVICE_FQDN=$ACCESSORY_SERVICE_FQDN"
  ```


After deploying your services, validate the deployment health:

**Linux/macOS:**
```bash
./test-deployment-health.sh -r "rg-petpal-dev"
```

---

### Step 1: Basic CI/CD Pipelines

See all implemented GitHub Actions workflows in the `.github/workflows/` directory.


## Common Issues and Solutions

### Issue 1: Cosmos DB Authentication Failures

**Symptoms:**
- Health check returns 503 or authentication errors
- Logs show "Unauthorized" or "Forbidden" errors accessing Cosmos DB
- Error: "Unable to load the proper Managed Identity"

**Solutions:**
- **Verify AZURE_CLIENT_ID is set**: Check Container App environment variables include `AZURE_CLIENT_ID`
- **Verify RBAC role assignments exist**: 
  - Data plane: `az cosmosdb sql role assignment list`
  - ARM level: `az role assignment list --scope $COSMOS_ACCOUNT_ID`
- Wait 5-10 minutes for role propagation after infrastructure deployment
- Check Container App has user-assigned managed identity configured
- Verify backend code uses `DefaultAzureCredential()` when not on localhost
- Ensure workflows dynamically retrieve and set AZURE_CLIENT_ID during deployment
- Check Application Insights for detailed error messages

### Issue 2: Long Build Times
**Solutions**:
- Implement Docker layer caching
- Use parallel job execution
- Optimize Dockerfile with multi-stage builds
- Cache dependencies between runs


## Next Steps

- Proceed to [Challenge 10: DevSecOps and Governance](/challenges/challenge-10/README.md)
- Implement advanced monitoring and alerting
- Optimize pipeline performance and efficiency
- Create comprehensive deployment documentation

## Additional Resources

- [Azure Cosmos DB RBAC Documentation](https://learn.microsoft.com/azure/cosmos-db/how-to-setup-rbac)
- [Container Apps Managed Identity](https://learn.microsoft.com/azure/container-apps/managed-identity)
- [DefaultAzureCredential Best Practices](https://learn.microsoft.com/python/api/overview/azure/identity-readme)
- [Cosmos DB Authentication Migration Guide](/backend/COSMOS_AUTH_MIGRATION.md)
- [Infrastructure RBAC Migration Summary](/infra/RBAC_MIGRATION_COMPLETE.md)

---

**Key Takeaways**:
- **Managed Identity eliminates secret management** for Azure service-to-service authentication
- Automated pipelines reduce manual errors and increase deployment frequency
- **RBAC provides fine-grained access control** without exposing master keys
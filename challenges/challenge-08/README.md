# Challenge 08: Infrastructure as Code - Azure Deployment

## Overview

Deploy the PetPal microservices to Azure using Infrastructure as Code (IaC). This challenge focuses on provisioning the core infrastructure: Container Apps for backend services and frontend, and Cosmos DB for data storage.

## Learning Objectives

- Implement Infrastructure as Code (IaC) using Bicep
- Provision Azure Container Apps for microservices
- Provision and configure Azure Cosmos DB
- Understand basic Azure resource management and deployment
- Experience with Azure Developer CLI (azd) for simplified deployments

## Prerequisites

- Azure subscription with appropriate permissions
- Completed Challenge 07 (backend services running locally)
- Azure Developer CLI installed and configured
- Familiarity with Bicep or willingness to learn

## Tasks

### Task 1: Infrastructure Design and Planning

1. **Architecture Review**:
   - Review the PetPal microservices architecture (3 backend services + 1 frontend)
   - Identify Azure resources needed:
     - Azure Container Apps Environment
     - 4 Container Apps (pet-service, activity-service, accessory-service, frontend)
     - Azure Cosmos DB (serverless)
     - Azure Container Registry (ACR) for storing Docker images
     - Log Analytics Workspace (for Container Apps requirement)
   - Plan resource naming conventions and organization

2. **Choose IaC Approach**:
   - **Recommended**: Use Bicep for Azure-native IaC
   - Alternative: Terraform or ARM templates
   - Understand modular infrastructure design
   - Plan for environment-specific configurations (dev, staging, prod)

### Task 2: Review Up Bicep Infrastructure

1. **Review Bicep Project Structure**:
   - Create `infra/` directory in your project root
   - Organize Bicep files by resource type:
     - `main.bicep` - orchestration template
     - `cosmos.bicep` - Cosmos DB configuration
     - `acr.bicep` - Azure Container Registry configuration
     - `container-app-environment.bicep` - Container Apps environment
     - `container-app.*.bicep` - individual Container App modules
   - Create `main.parameters.json` for parameter values


### Task 3: Implement Container Infrastructure for Accessory Service

1. **Container Apps Environment**:
   - Review one of existing Bicep modules for Container Apps backend service
   - Use Copilot to help generate Bicep code if needed


### Task 5: Deployment and Testing

1. **Deploy Infrastructure**:

  > Important!: We will do only `provision` step here to set up infrastructure. Application code deployment will be done in Challenge 09 using GitHub Actions.

   - Use Azure Developer CLI (azd):
     ```bash
     azd init
     azd provision
     ```

2. **Verify Deployment**:
   - Check all Container Apps are running
   - Test backend service endpoints
   - Verify frontend loads
   - Confirm Cosmos DB databases and containers created
   - Verify ACR is created and accessible
   - Review deployment outputs (URLs, connection strings, managed identity information)

   Example of provisioned services in Azure Portal:
    ![Azure Portal Container Apps](../../solutions/challenge-08/docs/infra-provisioned.jpg)
 

## Success Criteria

- [ ] Infrastructure code organized in modular Bicep templates
- [ ] Four Container Apps deployed (pet, activity, accessory, frontend)
- [ ] Azure Cosmos DB provisioned with serverless capability
- [ ] Azure Container Registry (ACR) created and accessible
- [ ] User-assigned managed identities created for each backend service (3 total)
- [ ] Each service identity has `AcrPull` role assigned on ACR
- [ ] Each service identity has `Cosmos DB Data Contributor` + `DocumentDB Account Contributor` roles for Cosmos DB
- [ ] Services accessible via HTTPS endpoints

## Infrastructure as Code with Copilot - Exaamples

### Getting Started with Bicep
Use GitHub Copilot to generate Bicep templates:

```
"Create main.bicep orchestration template for PetPal microservices"

"Generate Bicep module for Azure Container App with parameters for image, environment variables, and ingress"

"Create Bicep template for Cosmos DB serverless with output for connection string"

"Generate parameters file for Bicep with location, environment name, and image tags"
```

### Copilot Tips
- Ask Copilot to explain Bicep syntax and best practices
- Use Copilot to generate module parameters and outputs
- Guide Copilot by referencing any specific files (#)
- Specify ACA images (hello world - mcr.microsoft.com/azuredocs/containerapps-helloworld:latest )
- Request Copilot to create deployment scripts
- Ask for troubleshooting help with deployment errors

## Azure Developer CLI (azd) - Recommended Approach

### Why Use azd?
- Simplified infrastructure provisioning and deployment
- Built-in support for Bicep templates
- Streamlined environment management
- Integrated CI/CD workflows
- Consistent deployment experience

### Getting Started with azd
```bash
# Initialize azd project
azd init

# Provision infrastructure and deploy
azd up

# Provision only (infrastructure as code)
azd provision

# Deploy code changes only
azd deploy

# Clean up all resources
azd down
```

### azd Project Structure
```
/
├── infra/                  # Bicep templates
│   ├── main.bicep
│   ├── main.parameters.json
│   └── modules/
├── azure.yaml             # azd configuration
└── .azure/                # azd environment files
```

## Resource Naming Conventions

Use consistent naming patterns for better organization:
- Resource Group: `rg-petpal-{env}`
- Container Apps Environment: `petpal-{env}-env`
- Container Apps: `petpal-{env}-{service-name}`
- Cosmos DB: `cosmos-petpal-{env}-{uniqueid}`
- Log Analytics: `logs-petpal-{env}`

## Troubleshooting Common Issues

### Deployment Failures
- Check resource naming conflicts (use unique suffixes)
- Verify subscription permissions
- Review Bicep validation warnings
- Check parameter values match expected types

### Container Apps Not Starting
- Verify container image exists and is accessible
- Check environment variables are set correctly
- Review Container Apps logs in Azure Portal
- Verify Log Analytics workspace connection

### Service Communication Issues
- Confirm all services have external ingress enabled
- Check environment variable URLs are correct
- Verify network connectivity between services
- Test endpoints individually before integration

### Cosmos DB Connection Issues
- Verify connection string format
- Check Cosmos DB key is correctly passed
- Confirm database and container names match
- Review firewall settings (allow Azure services)

## Cost Considerations

**Estimated monthly costs for development environment:**
- Container Apps (4 services): ~$30-60
- Cosmos DB (serverless): ~$5-15 (depends on usage)
- Log Analytics: ~$5 (5GB free tier)

**Total estimated cost: $40-80/month**

💡 **Tip**: Delete resources when not in use to minimize costs!

## Optional Extensions (Not Required for Challenge Completion)

The following topics are advanced features that can enhance your deployment but are **not required** to complete this challenge:

### Security Enhancements
- Implement managed identities for service authentication
- Use Azure Key Vault for secrets management
- Configure private endpoints for Cosmos DB
- Set up network security groups and access restrictions
- Implement Azure AD authentication

### Monitoring and Observability
- Configure Application Insights for distributed tracing
- Set up Azure Monitor dashboards
- Create alerts for service health and performance
- Implement custom metrics and logging
- Configure log aggregation and analysis

### Deployment Automation
- Create GitHub Actions workflows for CI/CD
- Implement automated testing before deployment
- Set up environment promotion pipelines
- Configure blue-green or canary deployments
- Implement rollback strategies

These optional extensions will be covered in future challenges focused on production readiness, security hardening, and operational excellence.

## Additional Resources

- [Azure Container Apps Documentation](https://docs.microsoft.com/azure/container-apps/)
- [Bicep Language Documentation](https://docs.microsoft.com/azure/azure-resource-manager/bicep/)
- [Azure Developer CLI (azd)](https://docs.microsoft.com/azure/developer/azure-developer-cli/)
- [Azure Cosmos DB Serverless](https://docs.microsoft.com/azure/cosmos-db/serverless)
- [Container Apps Pricing](https://azure.microsoft.com/pricing/details/container-apps/)

## Solution

Need help? Check the [Solution Guide](/solutions/challenge-08/README.md) for detailed implementation steps and reference code.

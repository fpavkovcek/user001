# Challenge 08 - Infrastructure Files Reference

This directory contains comprehensive documentation for Challenge 08's Infrastructure as Code solution.

## Main Solution Document

👉 **[README.md](README.md)** - Complete solution guide with:
- Architecture overview
- Step-by-step implementation
- Security best practices
- Deployment instructions
- Troubleshooting guide
- Cost estimates

## Infrastructure Code Location

All Bicep templates and deployment scripts are located in:

📁 **`/infra`** directory at repository root

### Quick Links

| File | Purpose |
|------|---------|
| [/infra/README.md](../../infra/README.md) | Infrastructure documentation |
| [/infra/QUICKSTART.md](../../infra/QUICKSTART.md) | Quick deployment guide |
| [/infra/main.bicep](../../infra/main.bicep) | Main orchestration template |
| [/infra/deploy.sh](../../infra/deploy.sh) | Automated deployment script |
| [/infra/validate.sh](../../infra/validate.sh) | Validation script |

## File Structure Overview

```
/infra/
├── main.bicep                           # Main template - orchestrates all modules
├── main.parameters.json                 # Parameter values
├── cosmos.bicep                         # Cosmos DB configuration
├── container-app-environment.bicep      # Container Apps environment + Log Analytics
├── container-app.pet-service.bicep      # Pet service container app
├── container-app.activity-service.bicep # Activity service container app
├── container-app.accessory-service.bicep# Accessory service container app
├── container-app.frontend.bicep         # Frontend container app
├── deploy.sh                            # Automated deployment script
├── validate.sh                          # Validation script
├── .bicepconfig.json                    # Bicep linting configuration
├── README.md                            # Full documentation
└── QUICKSTART.md                        # Quick start guide
```

## Quick Deployment

### Option 1: Automated Script (Recommended)
```bash
cd /workspaces/MicroHack-GitHub/infra
./deploy.sh
```

### Option 2: Azure CLI
```bash
cd /workspaces/MicroHack-GitHub/infra
az group create --name petpal-rg --location eastus
az deployment group create \
  --resource-group petpal-rg \
  --template-file main.bicep \
  --parameters main.parameters.json \
  --name petpal-infrastructure
```

## What Gets Deployed

✅ **7 Azure Resources**:
1. Container Apps Environment
2. Log Analytics Workspace
3. Cosmos DB Account (Serverless)
4. Pet Service Container App
5. Activity Service Container App
6. Accessory Service Container App
7. Frontend Container App

## Key Features

- **Serverless Cosmos DB**: Pay-per-request pricing
- **Auto-scaling**: All services scale 1-10 replicas
- **HTTPS Everywhere**: Automatic SSL/TLS
- **Secrets Management**: Cosmos keys stored securely
- **Centralized Logging**: Log Analytics integration
- **Modular Design**: Reusable Bicep modules

## Environment Variables Configured

### Backend Services (pets, activities, accessories)
- `COSMOS_ENDPOINT`: Database endpoint URL
- `COSMOS_KEY`: Primary key (secret)
- `COSMOS_DATABASE_NAME`: Service-specific database
- `COSMOS_CONTAINER_NAME`: Service-specific container

### Frontend
- `VITE_API_PETS_URL`: Pet service URL
- `VITE_API_ACTIVITIES_URL`: Activity service URL
- `VITE_API_ACCESSORIES_URL`: Accessory service URL

## Validation

After deployment, validate your infrastructure:

```bash
cd /workspaces/MicroHack-GitHub/infra
./validate.sh petpal-rg petpal-infrastructure
```

## Cost Estimate

💰 **Development Environment**: ~$30-60/month
- Container Apps: ~$20-40
- Cosmos DB Serverless: ~$5-15
- Log Analytics: ~$5 (5GB free)

## Next Steps

1. ✅ Deploy infrastructure (Challenge 08) - **YOU ARE HERE**
2. 🔄 Build and deploy applications (Challenge 09)
3. 🔐 Implement managed identities (Challenge 10)
4. 📊 Add monitoring and alerting (Challenge 11)
5. 🚀 Setup CI/CD pipeline (Challenge 12)

## Additional Resources

### Documentation
- [Azure Container Apps](https://docs.microsoft.com/azure/container-apps/)
- [Azure Cosmos DB](https://docs.microsoft.com/azure/cosmos-db/)
- [Bicep Language](https://docs.microsoft.com/azure/azure-resource-manager/bicep/)

### Related Challenges
- [Challenge 08 Instructions](../../challenges/challenge-08/README.md)
- [Challenge 09 (Deployment)](../../challenges/challenge-09/README.md)

## Support

For issues or questions:
1. Check [Troubleshooting section](README.md#troubleshooting-guide)
2. Review [Common Pitfalls](README.md#common-pitfalls-and-solutions)
3. Consult [Infrastructure README](../../infra/README.md)

---

**Ready to deploy?** Head to `/infra` and run `./deploy.sh`! 🚀

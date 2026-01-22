# Pet Service Deployment Guide

This guide covers different deployment scenarios for the Pet Service API.

## 🚀 Quick Start (Local Development)

1. **Clone and setup**:
   ```bash
   cd backend/pet-service
   ./start.sh
   ```

2. **Configure Azure CosmosDB**:
   - Edit `.env` file with your CosmosDB endpoint
   - Ensure you're authenticated with Azure (`az login`)

3. **Access the API**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

## 🐳 Docker Deployment

### Local Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t pet-service .
docker run -p 8000:8000 --env-file .env pet-service
```

### Azure Container Instances

```bash
# Login to Azure
az login

# Create resource group
az group create --name pet-service-rg --location eastus

# Create container instance
az container create \
  --resource-group pet-service-rg \
  --name pet-service-aci \
  --image your-registry/pet-service:latest \
  --dns-name-label pet-service-unique \
  --ports 8000 \
  --environment-variables \
    COSMOS_ENDPOINT="https://your-cosmos-account.documents.azure.com:443/" \
    COSMOS_DATABASE_NAME="petservice" \
    COSMOS_CONTAINER_NAME="pets" \
  --assign-identity \
  --cpu 1 \
  --memory 1
```

## ☁️ Azure App Service Deployment

### Option 1: Azure CLI

```bash
# Create App Service Plan
az appservice plan create \
  --name pet-service-plan \
  --resource-group pet-service-rg \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --resource-group pet-service-rg \
  --plan pet-service-plan \
  --name pet-service-app \
  --deployment-container-image-name your-registry/pet-service:latest

# Assign managed identity
az webapp identity assign \
  --resource-group pet-service-rg \
  --name pet-service-app

# Configure app settings
az webapp config appsettings set \
  --resource-group pet-service-rg \
  --name pet-service-app \
  --settings \
    COSMOS_ENDPOINT="https://your-cosmos-account.documents.azure.com:443/" \
    COSMOS_KEY="your-cosmos-primary-key" \
    COSMOS_DATABASE_NAME="petservice" \
    COSMOS_CONTAINER_NAME="pets" \
    WEBSITES_PORT="8000"
```

### Option 2: ARM Template

```bash
# Deploy using the provided ARM template
az deployment group create \
  --resource-group pet-service-rg \
  --template-file azure-deploy.json \
  --parameters \
    appName="pet-service" \
    cosmosAccountName="your-cosmos-account" \
    containerImage="your-registry/pet-service:latest"
```

## 🔐 Azure CosmosDB Setup

### 1. Create CosmosDB Account

```bash
# Create CosmosDB account
az cosmosdb create \
  --resource-group pet-service-rg \
  --name your-cosmos-account \
  --kind GlobalDocumentDB \
  --locations regionName="East US" failoverPriority=0 isZoneRedundant=False

# Create database
az cosmosdb sql database create \
  --account-name your-cosmos-account \
  --resource-group pet-service-rg \
  --name petservice

# Create container
az cosmosdb sql container create \
  --account-name your-cosmos-account \
  --resource-group pet-service-rg \
  --database-name petservice \
  --name pets \
  --partition-key-path "/id" \
  --throughput 400
```

### 2. Get CosmosDB Access Key

```bash
# Get the primary key for your CosmosDB account
COSMOS_KEY=$(az cosmosdb keys list \
  --resource-group pet-service-rg \
  --name your-cosmos-account \
  --query primaryMasterKey -o tsv)

echo "CosmosDB Key: $COSMOS_KEY"
# Use this key in your application settings
```

## 🏗️ Azure Kubernetes Service (AKS)

### 1. Create AKS Cluster

```bash
# Create AKS cluster
az aks create \
  --resource-group pet-service-rg \
  --name pet-service-aks \
  --node-count 1 \
  --enable-addons monitoring \
  --generate-ssh-keys \
  --enable-managed-identity

# Get credentials
az aks get-credentials \
  --resource-group pet-service-rg \
  --name pet-service-aks
```

### 2. Deploy to AKS

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pet-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: pet-service
  template:
    metadata:
      labels:
        app: pet-service
    spec:
      containers:
      - name: pet-service
        image: your-registry/pet-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: COSMOS_ENDPOINT
          value: "https://your-cosmos-account.documents.azure.com:443/"
        - name: COSMOS_KEY
          valueFrom:
            secretKeyRef:
              name: cosmos-secret
              key: cosmos-key
        - name: COSMOS_DATABASE_NAME
          value: "petservice"
        - name: COSMOS_CONTAINER_NAME
          value: "pets"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: pet-service-svc
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: pet-service
```

Create the secret and deploy:

```bash
# Create Kubernetes secret for CosmosDB key
kubectl create secret generic cosmos-secret \
  --from-literal=cosmos-key="your-cosmos-primary-key"

# Deploy the application
kubectl apply -f k8s-deployment.yaml
kubectl get services
```

## 📊 Monitoring & Observability

### Azure Application Insights

Add to your App Service:

```bash
# Create Application Insights
az monitor app-insights component create \
  --app pet-service-ai \
  --location eastus \
  --resource-group pet-service-rg

# Get instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app pet-service-ai \
  --resource-group pet-service-rg \
  --query instrumentationKey -o tsv)

# Add to app settings
az webapp config appsettings set \
  --resource-group pet-service-rg \
  --name pet-service-app \
  --settings APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=$INSTRUMENTATION_KEY"
```

### Log Analytics

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group pet-service-rg \
  --workspace-name pet-service-logs \
  --location eastus
```

## 🔧 CI/CD Pipeline

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Pet Service

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Login to Azure Container Registry
      uses: azure/docker-login@v1
      with:
        login-server: ${{ secrets.REGISTRY_LOGIN_SERVER }}
        username: ${{ secrets.REGISTRY_USERNAME }}
        password: ${{ secrets.REGISTRY_PASSWORD }}
    
    - name: Build and push Docker image
      run: |
        cd backend/pet-service
        docker build -t ${{ secrets.REGISTRY_LOGIN_SERVER }}/pet-service:${{ github.sha }} .
        docker push ${{ secrets.REGISTRY_LOGIN_SERVER }}/pet-service:${{ github.sha }}
    
    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: pet-service-app
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
        images: ${{ secrets.REGISTRY_LOGIN_SERVER }}/pet-service:${{ github.sha }}
```

## ✅ Testing Deployment

After deployment, test your API:

```bash
# Test with the provided test script
python test_api.py --base-url https://your-app.azurewebsites.net --verbose

# Or test manually
curl https://your-app.azurewebsites.net/health
curl https://your-app.azurewebsites.net/api/pets
```

## 🛡️ Security Best Practices

1. **Authentication**: Always use managed identity in Azure
2. **Network Security**: Use private endpoints for CosmosDB
3. **HTTPS**: Enable HTTPS-only in App Service
4. **Secrets**: Store secrets in Azure Key Vault
5. **Monitoring**: Enable security monitoring and alerts

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify CosmosDB access key is correct
   - Check key permissions (should be primary or secondary key)
   - Ensure key is not expired or regenerated

2. **Connection Errors**:
   - Verify CosmosDB endpoint URL
   - Check network connectivity
   - Review app logs: `az webapp log tail --name pet-service-app --resource-group pet-service-rg`

3. **Container Issues**:
   - Check container logs: `docker logs <container-id>`
   - Verify environment variables
   - Check health endpoint: `/health`

### Useful Commands

```bash
# Check app logs
az webapp log tail --name pet-service-app --resource-group pet-service-rg

# Stream logs in real-time
az webapp log config --name pet-service-app --resource-group pet-service-rg --docker-container-logging filesystem

# Check app settings
az webapp config appsettings list --name pet-service-app --resource-group pet-service-rg

# Restart app
az webapp restart --name pet-service-app --resource-group pet-service-rg
```

## 📈 Scaling Considerations

- **App Service**: Use autoscaling rules based on CPU/memory
- **CosmosDB**: Consider dedicated throughput for high-load scenarios
- **Caching**: Add Redis for frequently accessed data
- **CDN**: Use Azure CDN for static assets

## 💰 Cost Optimization

- **App Service**: Use appropriate SKU (B1 for development, P1V2+ for production)
- **CosmosDB**: Use serverless for variable workloads
- **Monitoring**: Set up cost alerts and budgets
- **Resources**: Use resource tagging for cost tracking
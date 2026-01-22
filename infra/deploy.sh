#!/bin/bash

# PetPal Infrastructure Deployment Script
# This script automates the deployment of PetPal microservices infrastructure to Azure

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_info "Checking prerequisites..."

if ! command_exists az; then
    print_error "Azure CLI is not installed. Please install it from https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi

print_success "Azure CLI is installed"

# Check if logged in to Azure
if ! az account show >/dev/null 2>&1; then
    print_error "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

print_success "Logged in to Azure"

# Get current subscription
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
print_info "Using subscription: ${SUBSCRIPTION_NAME} (${SUBSCRIPTION_ID})"

# Prompt for parameters or use defaults
read -p "Enter resource group name [petpal-rg]: " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-petpal-rg}

read -p "Enter location [eastus]: " LOCATION
LOCATION=${LOCATION:-eastus}

read -p "Enter environment name (dev/staging/prod) [dev]: " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-dev}

read -p "Enter frontend image [ghcr.io/michalmar/petpal-ui:latest]: " FRONTEND_IMAGE
FRONTEND_IMAGE=${FRONTEND_IMAGE:-ghcr.io/michalmar/petpal-ui:latest}

print_info "Deployment Configuration:"
echo "  Resource Group: ${RESOURCE_GROUP}"
echo "  Location: ${LOCATION}"
echo "  Environment: ${ENVIRONMENT}"
echo "  Frontend Image: ${FRONTEND_IMAGE}"
echo "  Backend Services: Using hello world containers for infrastructure provisioning"
echo ""

read -p "Proceed with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled."
    exit 0
fi

# Create resource group if it doesn't exist
print_info "Creating resource group '${RESOURCE_GROUP}'..."
az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}" --output none
print_success "Resource group ready"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Validate Bicep template
print_info "Validating Bicep template..."
VALIDATION_RESULT=$(az deployment group validate \
    --resource-group "${RESOURCE_GROUP}" \
    --template-file "${SCRIPT_DIR}/main.bicep" \
    --parameters \
        location="${LOCATION}" \
        environmentName="${ENVIRONMENT}" \
        frontendImage="${FRONTEND_IMAGE}" \
    --output json)

if [ $? -eq 0 ]; then
    print_success "Bicep template validation passed"
else
    print_error "Bicep template validation failed"
    echo "${VALIDATION_RESULT}" | jq .
    exit 1
fi

# Deploy infrastructure
DEPLOYMENT_NAME="petpal-infrastructure-$(date +%Y%m%d-%H%M%S)"
print_info "Starting deployment '${DEPLOYMENT_NAME}'..."
print_info "This may take 5-10 minutes..."

az deployment group create \
    --resource-group "${RESOURCE_GROUP}" \
    --template-file "${SCRIPT_DIR}/main.bicep" \
    --parameters \
        location="${LOCATION}" \
        environmentName="${ENVIRONMENT}" \
        frontendImage="${FRONTEND_IMAGE}" \
    --name "${DEPLOYMENT_NAME}" \
    --output json > /tmp/petpal-deployment-result.json

if [ $? -eq 0 ]; then
    print_success "Infrastructure deployment completed successfully!"
else
    print_error "Deployment failed. Check the error details above."
    exit 1
fi

# Extract and display outputs
print_info "Extracting deployment outputs..."

COSMOS_ENDPOINT=$(az deployment group show \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${DEPLOYMENT_NAME}" \
    --query properties.outputs.cosmosEndpoint.value -o tsv)

PET_SERVICE_URL=$(az deployment group show \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${DEPLOYMENT_NAME}" \
    --query properties.outputs.petServiceUrl.value -o tsv)

ACTIVITY_SERVICE_URL=$(az deployment group show \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${DEPLOYMENT_NAME}" \
    --query properties.outputs.activityServiceUrl.value -o tsv)

ACCESSORY_SERVICE_URL=$(az deployment group show \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${DEPLOYMENT_NAME}" \
    --query properties.outputs.accessoryServiceUrl.value -o tsv)

FRONTEND_URL=$(az deployment group show \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${DEPLOYMENT_NAME}" \
    --query properties.outputs.frontendUrl.value -o tsv)

# Display deployment summary
echo ""
print_success "========================================="
print_success "   DEPLOYMENT COMPLETED SUCCESSFULLY"
print_success "========================================="
echo ""
echo "📦 Resource Group: ${RESOURCE_GROUP}"
echo "🌍 Location: ${LOCATION}"
echo "🏷️  Environment: ${ENVIRONMENT}"
echo ""
echo "🔗 Deployment Outputs:"
echo "   Cosmos DB Endpoint: ${COSMOS_ENDPOINT}"
echo "   Pet Service URL: ${PET_SERVICE_URL}"
echo "   Activity Service URL: ${ACTIVITY_SERVICE_URL}"
echo "   Accessory Service URL: ${ACCESSORY_SERVICE_URL}"
echo "   Frontend URL: ${FRONTEND_URL}"
echo ""
print_info "Testing frontend availability..."
if curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}" | grep -q "200\|301\|302"; then
    print_success "Frontend is accessible!"
    echo ""
    echo "🎉 You can now access the PetPal application at:"
    echo "   ${FRONTEND_URL}"
else
    print_warning "Frontend may take a few minutes to become available."
    echo "   Check ${FRONTEND_URL} in a few minutes."
fi

echo ""
print_info "To view logs, run:"
echo "   az containerapp logs show --name <app-name> --resource-group ${RESOURCE_GROUP} --follow"
echo ""
print_info "To delete all resources, run:"
echo "   az group delete --name ${RESOURCE_GROUP} --yes --no-wait"
echo ""

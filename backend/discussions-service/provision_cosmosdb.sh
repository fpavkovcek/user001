#!/bin/bash
# Script to provision Azure CosmosDB for Discussions Service
#
# This script creates:
# - A CosmosDB account (NoSQL API)
# - A database for discussions
# - Containers for rooms, messages, invitations, and attachments
#
# Prerequisites:
# - Azure CLI installed and logged in (az login)
# - Subscription selected (az account set --subscription <id>)
#
# Usage:
#   ./provision_cosmosdb.sh [resource-group] [location] [account-name]
#
# Example:
#   ./provision_cosmosdb.sh my-rg eastus discussions-cosmos

set -e

# Default values
RESOURCE_GROUP="${1:-discussions-rg}"
LOCATION="${2:-eastus}"
ACCOUNT_NAME="${3:-discussions-cosmos-$(openssl rand -hex 4)}"
DATABASE_NAME="discussionsdb"

# Container configurations
ROOMS_CONTAINER="rooms"
MESSAGES_CONTAINER="messages"
INVITATIONS_CONTAINER="invitations"
ATTACHMENTS_CONTAINER="attachments"

echo "=========================================="
echo "Discussions Service CosmosDB Provisioning"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Account Name: $ACCOUNT_NAME"
echo "  Database Name: $DATABASE_NAME"
echo ""

# Check if logged in to Azure
echo "Checking Azure CLI login..."
if ! az account show > /dev/null 2>&1; then
    echo "Error: Not logged in to Azure CLI. Run 'az login' first."
    exit 1
fi

SUBSCRIPTION=$(az account show --query name -o tsv)
echo "Using subscription: $SUBSCRIPTION"
echo ""

# Create resource group if it doesn't exist
echo "Creating resource group (if needed)..."
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output none

# Create CosmosDB account
echo "Creating CosmosDB account (this may take several minutes)..."
az cosmosdb create \
    --name "$ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --kind GlobalDocumentDB \
    --default-consistency-level Session \
    --locations regionName="$LOCATION" failoverPriority=0 isZoneRedundant=false \
    --capabilities EnableServerless \
    --output none

echo "CosmosDB account created successfully!"

# Create database
echo "Creating database: $DATABASE_NAME..."
az cosmosdb sql database create \
    --account-name "$ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DATABASE_NAME" \
    --output none

# Create containers with appropriate partition keys
echo "Creating container: $ROOMS_CONTAINER..."
az cosmosdb sql container create \
    --account-name "$ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --database-name "$DATABASE_NAME" \
    --name "$ROOMS_CONTAINER" \
    --partition-key-path "/id" \
    --output none

echo "Creating container: $MESSAGES_CONTAINER..."
az cosmosdb sql container create \
    --account-name "$ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --database-name "$DATABASE_NAME" \
    --name "$MESSAGES_CONTAINER" \
    --partition-key-path "/room_id" \
    --output none

echo "Creating container: $INVITATIONS_CONTAINER..."
az cosmosdb sql container create \
    --account-name "$ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --database-name "$DATABASE_NAME" \
    --name "$INVITATIONS_CONTAINER" \
    --partition-key-path "/room_id" \
    --output none

echo "Creating container: $ATTACHMENTS_CONTAINER..."
az cosmosdb sql container create \
    --account-name "$ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --database-name "$DATABASE_NAME" \
    --name "$ATTACHMENTS_CONTAINER" \
    --partition-key-path "/message_id" \
    --output none

# Get connection details
echo ""
echo "Retrieving connection details..."
ENDPOINT=$(az cosmosdb show \
    --name "$ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query documentEndpoint \
    -o tsv)

PRIMARY_KEY=$(az cosmosdb keys list \
    --name "$ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query primaryMasterKey \
    -o tsv)

echo ""
echo "=========================================="
echo "CosmosDB Provisioning Complete!"
echo "=========================================="
echo ""
echo "Add these values to your .env file:"
echo ""
echo "USE_MOCK_DB=false"
echo "COSMOS_ENDPOINT=$ENDPOINT"
echo "COSMOS_KEY=$PRIMARY_KEY"
echo "COSMOS_DATABASE_NAME=$DATABASE_NAME"
echo "COSMOS_ROOMS_CONTAINER=$ROOMS_CONTAINER"
echo "COSMOS_MESSAGES_CONTAINER=$MESSAGES_CONTAINER"
echo "COSMOS_INVITATIONS_CONTAINER=$INVITATIONS_CONTAINER"
echo "COSMOS_ATTACHMENTS_CONTAINER=$ATTACHMENTS_CONTAINER"
echo ""
echo "To delete all resources:"
echo "  az group delete --name $RESOURCE_GROUP --yes --no-wait"

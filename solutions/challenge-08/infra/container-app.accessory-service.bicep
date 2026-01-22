// Container App for Accessory Service
// Provisions Azure Container App for the Accessory microservice with Entra ID authentication to Cosmos DB
// NOTE: Currently using hello world container for infrastructure provisioning
//       Replace with actual service image during application deployment phase

@description('Name of the Container App')
param name string

@description('Location for the Container App')
param location string = resourceGroup().location

@description('Container Apps Environment ID')
param containerAppEnvironmentId string

@description('Cosmos DB endpoint')
param cosmosEndpoint string

@description('Cosmos DB account resource ID for RBAC role assignment')
param cosmosAccountId string

@description('Optional Cosmos DB Data Contributor role definition ID to override the default built-in role')
param cosmosDataContributorRoleId string = ''

@description('Cosmos DB database name')
param cosmosDatabaseName string = 'accessoryservice'

@description('Cosmos DB container name')
param cosmosContainerName string = 'accessories'

@description('Whether to pre-provision the Cosmos SQL database and container (avoids needing sqlDatabases/write at runtime).')
param provisionCosmosResources bool = true

@description('Azure Container Registry name')
param acrName string = ''

@description('Azure Container Registry login server')
param acrLoginServer string = ''

// Managed Identity for ACR Pull - separate identity per microservice
resource accessoryServiceIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${name}-identity'
  location: location
}

// Reference to ACR for role assignment
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = if (acrName != '') {
  name: acrName
}

// Grant AcrPull role to the managed identity if ACR is specified
resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (acrName != '') {
  name: guid(acr.id, accessoryServiceIdentity.id, 'acrpull')
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '7f951dda-4ed3-4680-a7ca-43fe172d538d'
    ) // AcrPull role
    principalId: accessoryServiceIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Reference to Cosmos DB account for role assignment
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2025-04-15' existing = {
  name: split(cosmosAccountId, '/')[8] // Extract account name from resource ID
}

var cosmosDataPlaneRoleDefinitionId = empty(cosmosDataContributorRoleId)
  ? '${cosmosAccountId}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
  : '${cosmosAccountId}/sqlRoleDefinitions/${cosmosDataContributorRoleId}'

resource cosmosRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2025-04-15' = {
  name: guid(cosmosAccountId, accessoryServiceIdentity.id, 'cosmos-data-contributor')
  parent: cosmosAccount
  properties: {
    roleDefinitionId: cosmosDataPlaneRoleDefinitionId
    principalId: accessoryServiceIdentity.properties.principalId
    scope: cosmosAccountId
  }
}

// Grant control plane access so the identity can manage Cosmos DB account resources when required
resource cosmosControlPlaneRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(cosmosAccountId, accessoryServiceIdentity.id, 'cosmos-control-plane')
  scope: cosmosAccount
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '230815da-be43-4aae-9cb4-875f7bd000aa'
    )
    principalId: accessoryServiceIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Optional pre-provisioning of database & container (control plane creation happens at deploy time)
resource accessoryDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2025-04-15' = if (provisionCosmosResources) {
  name: cosmosDatabaseName
  parent: cosmosAccount
  properties: {
    resource: { id: cosmosDatabaseName }
    options: {}
  }
}

resource accessoryContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-04-15' = if (provisionCosmosResources) {
  name: cosmosContainerName
  parent: accessoryDatabase
  properties: {
    resource: {
      id: cosmosContainerName
      partitionKey: { paths: ['/id'], kind: 'Hash' }
    }
    options: {}
  }
}

resource accessoryServiceApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${accessoryServiceIdentity.id}': {}
    }
  }
  properties: {
    environmentId: containerAppEnvironmentId
    configuration: {
      ingress: {
        external: true
        targetPort: 8030
        transport: 'auto'
        allowInsecure: false
      }
      registries: (acrLoginServer != '')
        ? [
            {
              server: acrLoginServer
              identity: accessoryServiceIdentity.id
            }
          ]
        : []
      // No secrets needed - using Managed Identity for Cosmos DB auth
    }
    template: {
      containers: [
        {
          name: 'simple-hello'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'AZURE_CLIENT_ID'
              value: accessoryServiceIdentity.properties.clientId
            }
            {
              name: 'COSMOS_ENDPOINT'
              value: cosmosEndpoint
            }
            {
              name: 'COSMOS_DATABASE_NAME'
              value: cosmosDatabaseName
            }
            {
              name: 'COSMOS_CONTAINER_NAME'
              value: cosmosContainerName
            }
            // No COSMOS_KEY - using Managed Identity authentication
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-rule'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// Outputs
output fqdn string = 'https://${accessoryServiceApp.properties.configuration.ingress.fqdn}'
output name string = accessoryServiceApp.name
output id string = accessoryServiceApp.id
output identityPrincipalId string = accessoryServiceIdentity.properties.principalId
output identityClientId string = accessoryServiceIdentity.properties.clientId
output controlPlaneRoleDefinitionId string = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '230815da-be43-4aae-9cb4-875f7bd000aa'
)
output dataPlaneRoleDefinitionId string = cosmosDataPlaneRoleDefinitionId
output databaseProvisioned bool = provisionCosmosResources

// Container App for Pet Service
// Provisions Azure Container App for the Pet microservice with Entra ID authentication to Cosmos DB
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

@description('Cosmos DB database name')
param cosmosDatabaseName string = 'petservice'

@description('Cosmos DB container name')
param cosmosContainerName string = 'pets'

// NOTE: Using built-in Cosmos DB Operator for control plane. If you require broader permissions
// (e.g., role definition/assignment writes) consider supplying a different built-in role id or creating
// a custom role in a separate template. This template purposefully avoids custom role creation for simplicity.

// Granting data plane access relies on the built-in Cosmos DB Data Contributor role scoped at the account.

@description('Azure Container Registry name')
param acrName string = ''

@description('Azure Container Registry login server')
param acrLoginServer string = ''

// Managed Identity for ACR Pull - always create for future use
resource petServiceIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${name}-identity'
  location: location
}

// Reference to ACR for role assignment
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = if (acrName != '') {
  name: acrName
}

// Grant AcrPull role to the managed identity if ACR is specified
resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (acrName != '') {
  name: guid(acr.id, petServiceIdentity.id, 'acrpull')
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '7f951dda-4ed3-4680-a7ca-43fe172d538d'
    ) // AcrPull role
    principalId: petServiceIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Custom control plane role definition removed for simplicity (always using provided built-in id).

resource petServiceApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${petServiceIdentity.id}': {}
    }
  }
  properties: {
    environmentId: containerAppEnvironmentId
    configuration: {
      ingress: {
        external: true
        targetPort: 8010
        transport: 'auto'
        allowInsecure: false
      }
      registries: (acrLoginServer != '')
        ? [
            {
              server: acrLoginServer
              identity: petServiceIdentity.id
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
              value: petServiceIdentity.properties.clientId
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
output fqdn string = 'https://${petServiceApp.properties.configuration.ingress.fqdn}'
output name string = petServiceApp.name
output id string = petServiceApp.id
output identityPrincipalId string = petServiceIdentity.properties.principalId
output identityClientId string = petServiceIdentity.properties.clientId

// Main Bicep template for PetPal microservices infrastructure
// This template provisions:
// - Azure Container Registry (ACR) for Docker images
// - Azure Container Apps Environment
// - Azure Cosmos DB (serverless)
// - Container Apps for each microservice (pets, activities, accessories)
// - Container App for frontend
// NOTE: Backend services use hello world containers for infrastructure provisioning
//       Actual service images will be deployed in a separate application deployment phase

targetScope = 'resourceGroup'

// Parameters
@description('The location for all resources')
param location string = resourceGroup().location

@description('Environment name (e.g., dev, staging, prod)')
@minLength(3)
@maxLength(10)
param environmentName string = 'dev'

@description('Unique suffix for resource names to ensure global uniqueness')
param uniqueSuffix string = uniqueString(resourceGroup().id)

@description('Frontend container image')
param frontendImage string = 'ghcr.io/michalmar/petpal-ui:latest'

@description('Toggle creation of the user-assigned managed identity for GitHub Actions federation')
param enableGitHubManagedIdentity bool = true

// Variables
var resourcePrefix = 'petpal-${environmentName}'
var cosmosAccountName = '${resourcePrefix}-cosmos-${uniqueSuffix}'
var containerAppEnvName = '${resourcePrefix}-env-${uniqueSuffix}'
var logAnalyticsName = '${resourcePrefix}-logs-${uniqueSuffix}'
var acrName = replace('${resourcePrefix}acr${uniqueSuffix}', '-', '') // ACR names cannot contain hyphens
var githubIdentityName = '${resourcePrefix}-gha-mi-${uniqueSuffix}'
var cosmosControlPlaneRoleDefinitionId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '230815da-be43-4aae-9cb4-875f7bd000aa'
)
var cosmosAccountResourceId = resourceId('Microsoft.DocumentDB/databaseAccounts', cosmosAccountName)
var cosmosDataContributorRoleId = '00000000-0000-0000-0000-000000000002'

var petServiceCosmos = {
  databaseName: 'petservice'
  containerName: 'pets'
  partitionKeyPath: '/id'
}

var activityServiceCosmos = {
  databaseName: 'activityservice'
  containerName: 'activities'
  partitionKeyPath: '/id'
}

var accessoryServiceCosmos = {
  databaseName: 'accessoryservice'
  containerName: 'accessories'
  partitionKeyPath: '/id'
}

var cosmosDatabaseDefinitions = [
  {
    name: petServiceCosmos.databaseName
    containerName: petServiceCosmos.containerName
    partitionKeyPath: petServiceCosmos.partitionKeyPath
  }
  {
    name: activityServiceCosmos.databaseName
    containerName: activityServiceCosmos.containerName
    partitionKeyPath: activityServiceCosmos.partitionKeyPath
  }
  {
    name: accessoryServiceCosmos.databaseName
    containerName: accessoryServiceCosmos.containerName
    partitionKeyPath: accessoryServiceCosmos.partitionKeyPath
  }
]
var cosmosDataPlaneRoleDefinitionId = '${cosmosAccountResourceId}/sqlRoleDefinitions/${cosmosDataContributorRoleId}'

// Module imports
module containerRegistry 'acr.bicep' = {
  name: 'acr-deployment'
  params: {
    name: acrName
    location: location
    sku: 'Basic'
    adminUserEnabled: false
  }
}

resource containerRegistryResource 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = if (enableGitHubManagedIdentity) {
  name: acrName
}

module cosmosDb 'cosmos.bicep' = {
  name: 'cosmosdb-deployment'
  params: {
    accountName: cosmosAccountName
    location: location
    databaseDefinitions: cosmosDatabaseDefinitions
  }
}

module containerAppEnvironment 'container-app-environment.bicep' = {
  name: 'container-app-env-deployment'
  params: {
    environmentName: containerAppEnvName
    logAnalyticsName: logAnalyticsName
    location: location
  }
}

module petService 'container-app.pet-service.bicep' = {
  name: 'pet-service-deployment'
  params: {
    name: '${resourcePrefix}-pet-service'
    location: location
    containerAppEnvironmentId: containerAppEnvironment.outputs.environmentId
    cosmosEndpoint: cosmosDb.outputs.endpoint
    cosmosDatabaseName: petServiceCosmos.databaseName
    cosmosContainerName: petServiceCosmos.containerName
    acrName: acrName
    acrLoginServer: containerRegistry.outputs.loginServer
  }
}

module activityService 'container-app.activity-service.bicep' = {
  name: 'activity-service-deployment'
  params: {
    name: '${resourcePrefix}-activity-service'
    location: location
    containerAppEnvironmentId: containerAppEnvironment.outputs.environmentId
    cosmosEndpoint: cosmosDb.outputs.endpoint
    cosmosDatabaseName: activityServiceCosmos.databaseName
    cosmosContainerName: activityServiceCosmos.containerName
    acrName: acrName
    acrLoginServer: containerRegistry.outputs.loginServer
  }
}

module accessoryService 'container-app.accessory-service.bicep' = {
  name: 'accessory-service-deployment'
  params: {
    name: '${resourcePrefix}-accessory-service'
    location: location
    containerAppEnvironmentId: containerAppEnvironment.outputs.environmentId
    cosmosEndpoint: cosmosDb.outputs.endpoint
    cosmosDatabaseName: accessoryServiceCosmos.databaseName
    cosmosContainerName: accessoryServiceCosmos.containerName
    acrName: acrName
    acrLoginServer: containerRegistry.outputs.loginServer
  }
}

resource cosmosAccountExisting 'Microsoft.DocumentDB/databaseAccounts@2025-04-15' existing = {
  name: cosmosAccountName
}

resource petServiceCosmosDataRole 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2025-04-15' = {
  name: guid(resourceGroup().id, 'pet-service-cosmos-data')
  parent: cosmosAccountExisting
  properties: {
    roleDefinitionId: cosmosDataPlaneRoleDefinitionId
    principalId: petService.outputs.identityPrincipalId
    scope: cosmosAccountResourceId
  }
}

resource activityServiceCosmosDataRole 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2025-04-15' = {
  name: guid(resourceGroup().id, 'activity-service-cosmos-data')
  parent: cosmosAccountExisting
  properties: {
    roleDefinitionId: cosmosDataPlaneRoleDefinitionId
    principalId: activityService.outputs.identityPrincipalId
    scope: cosmosAccountResourceId
  }
}

resource accessoryServiceCosmosDataRole 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2025-04-15' = {
  name: guid(resourceGroup().id, 'accessory-service-cosmos-data')
  parent: cosmosAccountExisting
  properties: {
    roleDefinitionId: cosmosDataPlaneRoleDefinitionId
    principalId: accessoryService.outputs.identityPrincipalId
    scope: cosmosAccountResourceId
  }
}

resource petServiceCosmosControlRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, 'pet-service-cosmos-control')
  scope: cosmosAccountExisting
  properties: {
    roleDefinitionId: cosmosControlPlaneRoleDefinitionId
    principalId: petService.outputs.identityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource activityServiceCosmosControlRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, 'activity-service-cosmos-control')
  scope: cosmosAccountExisting
  properties: {
    roleDefinitionId: cosmosControlPlaneRoleDefinitionId
    principalId: activityService.outputs.identityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource accessoryServiceCosmosControlRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, 'accessory-service-cosmos-control')
  scope: cosmosAccountExisting
  properties: {
    roleDefinitionId: cosmosControlPlaneRoleDefinitionId
    principalId: accessoryService.outputs.identityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

module frontend 'container-app.frontend.bicep' = {
  name: 'frontend-deployment'
  params: {
    name: '${resourcePrefix}-frontend'
    location: location
    containerAppEnvironmentId: containerAppEnvironment.outputs.environmentId
    frontendImage: frontendImage
    petServiceUrl: petService.outputs.fqdn
    activityServiceUrl: activityService.outputs.fqdn
    accessoryServiceUrl: accessoryService.outputs.fqdn
  }
}

resource githubManagedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2025-01-31-preview' = if (enableGitHubManagedIdentity) {
  name: githubIdentityName
  location: location
}

var githubManagedIdentityPrincipalId = enableGitHubManagedIdentity
  ? githubManagedIdentity!.properties.principalId
  : null
var githubManagedIdentityClientId = enableGitHubManagedIdentity ? githubManagedIdentity!.properties.clientId : null
var githubManagedIdentityResourceId = enableGitHubManagedIdentity ? githubManagedIdentity!.id : null

// resource githubFederatedIdentityCredentials 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2025-01-31-preview' = [for subject in githubFederatedSubjects: if (enableGitHubManagedIdentity) {
//   name: guid(githubManagedIdentity.id, subject)
//   parent: githubManagedIdentity
//   properties: {
//     issuer: 'https://token.actions.githubusercontent.com'
//     subject: subject
//     audiences: [
//       'api://AzureADTokenExchange'
//     ]
//   }
// }]

resource githubIdentityContributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableGitHubManagedIdentity) {
  name: guid(subscription().subscriptionId, githubManagedIdentity.id, 'contributor')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'b24988ac-6180-42a0-ab88-20f7382dd24c'
    )
    principalId: githubManagedIdentityPrincipalId!
    principalType: 'ServicePrincipal'
  }
}

resource githubIdentityAcrPushRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableGitHubManagedIdentity) {
  name: guid(subscription().subscriptionId, githubManagedIdentity.id, 'acr-push')
  scope: containerRegistryResource
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '8311e382-0749-4cb8-b61a-304f252e45ec'
    )
    principalId: githubManagedIdentityPrincipalId!
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output cosmosEndpoint string = cosmosDb.outputs.endpoint
output acrLoginServer string = containerRegistry.outputs.loginServer
output acrName string = containerRegistry.outputs.name
output acrResourceId string = containerRegistry.outputs.id

output petServiceUrl string = petService.outputs.fqdn
output petServiceName string = petService.outputs.name
output petServiceManagedIdentityClientId string = petService.outputs.identityClientId

output activityServiceUrl string = activityService.outputs.fqdn
output activityServiceName string = activityService.outputs.name
output activityServiceManagedIdentityClientId string = activityService.outputs.identityClientId

output accessoryServiceUrl string = accessoryService.outputs.fqdn
output accessoryServiceName string = accessoryService.outputs.name
output accessoryServiceManagedIdentityClientId string = accessoryService.outputs.identityClientId

output frontendUrl string = frontend.outputs.fqdn
output githubManagedIdentityClientId string = githubManagedIdentityClientId == null
  ? ''
  : githubManagedIdentityClientId!
output githubManagedIdentityPrincipalId string = githubManagedIdentityPrincipalId == null
  ? ''
  : githubManagedIdentityPrincipalId!
output githubManagedIdentityResourceId string = githubManagedIdentityResourceId == null
  ? ''
  : githubManagedIdentityResourceId!

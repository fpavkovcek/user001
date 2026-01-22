// Container Apps Environment
// Provisions a managed environment for Azure Container Apps

@description('Name of the Container Apps Environment')
param environmentName string

@description('Name of the Log Analytics workspace')
param logAnalyticsName string

@description('Location for resources')
param location string = resourceGroup().location

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2021-06-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Container Apps Environment
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// Outputs
output environmentId string = containerAppEnvironment.id
output environmentName string = containerAppEnvironment.name
output defaultDomain string = containerAppEnvironment.properties.defaultDomain

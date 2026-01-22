// Cosmos DB Account - Serverless Configuration
// Provisions Azure Cosmos DB with serverless capability model

@description('Cosmos DB account name')
param accountName string

@description('Location for the Cosmos DB account')
param location string = resourceGroup().location

@description('The default consistency level of the Cosmos DB account')
@allowed([
  'Eventual'
  'ConsistentPrefix'
  'Session'
  'BoundedStaleness'
  'Strong'
])
param defaultConsistencyLevel string = 'Session'

@description('Collection of SQL databases and their primary containers to provision in this account')
param databaseDefinitions array = []

var databaseDefinitionsWithIndex = [for idx in range(0, length(databaseDefinitions)): {
  index: idx
  definition: databaseDefinitions[idx]
}]

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2025-04-15' = {
  name: accountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: defaultConsistencyLevel
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
    enableFreeTier: false
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    publicNetworkAccess: 'Enabled'
    disableKeyBasedMetadataWriteAccess: false
  }
}

resource sqlDatabases 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2025-04-15' = [for db in databaseDefinitionsWithIndex: {
  name: db.definition.name
  parent: cosmosAccount
  properties: {
    resource: {
      id: db.definition.name
    }
    options: {}
  }
}]

resource sqlContainers 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-04-15' = [
  for db in databaseDefinitionsWithIndex: {
    name: db.definition.containerName
    parent: sqlDatabases[db.index]
    properties: {
      resource: {
        id: db.definition.containerName
        partitionKey: {
          paths: [
            db.definition.partitionKeyPath
          ]
          kind: 'Hash'
        }
      }
      options: {}
    }
  }
]

// Built-in Cosmos DB Data Contributor role definition
// This is a built-in role, we just reference it for assignments
// Role ID: 00000000-0000-0000-0000-000000000002
var cosmosDataContributorRoleId = '00000000-0000-0000-0000-000000000002'

// Outputs
output endpoint string = cosmosAccount.properties.documentEndpoint
// output primaryKey string = cosmosAccount.listKeys().primaryMasterKey
output accountName string = cosmosAccount.name
output accountId string = cosmosAccount.id
output dataContributorRoleId string = cosmosDataContributorRoleId

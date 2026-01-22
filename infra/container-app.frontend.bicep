// Container App for Frontend
// Provisions Azure Container App for the PetPal frontend UI

@description('Name of the Container App')
param name string

@description('Location for the Container App')
param location string = resourceGroup().location

@description('Container Apps Environment ID')
param containerAppEnvironmentId string

@description('Frontend container image')
param frontendImage string

@description('Pet Service URL')
param petServiceUrl string

@description('Activity Service URL')
param activityServiceUrl string

@description('Accessory Service URL')
param accessoryServiceUrl string

resource frontendApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  properties: {
    environmentId: containerAppEnvironmentId
    configuration: {
      ingress: {
        external: true
        targetPort: 80
        transport: 'auto'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: frontendImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'VITE_API_PETS_URL'
              value: petServiceUrl
            }
            {
              name: 'VITE_API_ACTIVITIES_URL'
              value: activityServiceUrl
            }
            {
              name: 'VITE_API_ACCESSORIES_URL'
              value: accessoryServiceUrl
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'http-rule'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

// Outputs
output fqdn string = 'https://${frontendApp.properties.configuration.ingress.fqdn}'
output name string = frontendApp.name
output id string = frontendApp.id

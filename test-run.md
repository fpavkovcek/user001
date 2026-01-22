## remove running containers if exists
docker container rm -f cosmos-emulator petpal-ui 2>/dev/null || true

# pull docker image
docker pull ghcr.io/michalmar/petpal-ui:latest

# Run Cosmos DB Emulator in Docker (Linux)
docker run \
   --name cosmos-emulator \
   --detach \
   --publish 8081:8081 \
   --publish 1234:1234 \
   mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-preview



docker container rm -f petpal-ui 2>/dev/null || true
# run frontend
docker run -d \
   -p 3000:80 \
   -e VITE_API_PETS_URL=https://super-dollop-g46v49xq4xpf9xq5-8010.app.github.dev \
   -e VITE_API_ACTIVITIES_URL=https://super-dollop-g46v49xq4xpf9xq5-8020.app.github.dev \
   -e VITE_API_ACCESSORIES_URL=https://super-dollop-g46v49xq4xpf9xq5-8030.app.github.dev \
   -e VITE_API_GITHUB_TOKEN=$GITHUB_TOKEN \
   --name petpal-ui \
   ghcr.io/michalmar/petpal-ui:latest


#!/bin/bash

# MicroHack Backend Services Startup Script
# Configuration - Change these ports as needed
PET_SERVICE_PORT=8010
ACTIVITY_SERVICE_PORT=8020
ACCESSORY_SERVICE_PORT=8030
FRONTEND_PORT=3000
COSMOS_CONTAINER_NAME="cosmos-emulator"
FRONTEND_CONTAINER_NAME="petpal-ui"

# Check if Codespaces URL parameter is provided
if [ $# -ne 1 ]; then
    echo "❌ Error: Codespaces URL parameter is required"
    echo ""
    echo "Usage: $0 <codespaces-url>"
    echo "Example: $0 https://organic-journey-v6wj64pv64526wp4.github.dev/"
    echo ""
    exit 1
fi

CODESPACES_URL="$1"
# Remove trailing slash if present
CODESPACES_URL="${CODESPACES_URL%/}"

# Extract the codespace name from the URL (e.g., organic-journey-v6wj64pv64526wp4)
CODESPACE_NAME=$(echo "$CODESPACES_URL" | sed -E 's|https?://([^.]+)\.github\.dev/?|\1|')

if [ -z "$CODESPACE_NAME" ]; then
    echo "❌ Error: Invalid Codespaces URL format"
    echo "Expected format: https://<codespace-name>.github.dev/"
    exit 1
fi

# Construct the forwarded port URLs
PETS_URL="https://${CODESPACE_NAME}-${PET_SERVICE_PORT}.app.github.dev"
ACTIVITIES_URL="https://${CODESPACE_NAME}-${ACTIVITY_SERVICE_PORT}.app.github.dev"
ACCESSORIES_URL="https://${CODESPACE_NAME}-${ACCESSORY_SERVICE_PORT}.app.github.dev"

echo "🚀 Starting MicroHack Backend Services..."
echo "========================================"
echo "🌐 Codespaces URL: $CODESPACES_URL"
echo "🔗 Pet Service URL: $PETS_URL"
echo "🔗 Activity Service URL: $ACTIVITIES_URL"
echo "🔗 Accessory Service URL: $ACCESSORIES_URL"
echo ""

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # Port is in use
    else
        return 0  # Port is available
    fi
}

# Function to stop services on cleanup
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    
    # Kill background jobs
    for job in $(jobs -p); do
        echo "   Stopping process $job..."
        kill $job 2>/dev/null
    done

    if command -v docker >/dev/null 2>&1; then
        echo "   Removing Docker containers..."
        docker rm -f "$FRONTEND_CONTAINER_NAME" "$COSMOS_CONTAINER_NAME" >/dev/null 2>&1 || true
    fi
    
    echo "✅ All services stopped"
    exit 0
}

# Set up cleanup on script termination
trap cleanup SIGINT SIGTERM EXIT

# Navigate to project root
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

echo "📁 Project root: $PROJECT_ROOT"
echo ""

if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker is required to run the Cosmos DB emulator and frontend. Please install Docker and try again."
    exit 1
fi

echo "🐳 Preparing Docker prerequisites..."
docker container rm -f "$COSMOS_CONTAINER_NAME" "$FRONTEND_CONTAINER_NAME" >/dev/null 2>&1 || true

echo "   ⬇️  Pulling Cosmos DB emulator image..."
if ! docker pull mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest; then
    echo "❌ Failed to pull Cosmos DB emulator image."
    exit 1
fi

echo "   ⬇️  Pulling latest frontend image..."
if ! docker pull ghcr.io/michalmar/petpal-ui:latest; then
    echo "❌ Failed to pull frontend image."
    exit 1
fi

echo "   🚀 Starting Azure Cosmos DB Emulator..."
if ! docker run \
   --name "$COSMOS_CONTAINER_NAME" \
   --detach \
   --publish 8081:8081 \
   --publish 10250-10255:10250-10255 \
   mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest >/dev/null; then
    echo "❌ Failed to start Cosmos DB emulator container."
    exit 1
fi

# Wait briefly for the emulator to initialize
sleep 5

if [ -z "${GITHUB_TOKEN:-}" ]; then
    echo "   ⚠️  Environment variable GITHUB_TOKEN not set. Frontend will start without GitHub integration."
fi


echo "✅ Docker services ready"
echo ""

# Check if ports are available
echo "🔍 Checking port availability..."
if ! check_port $PET_SERVICE_PORT; then
    echo "❌ Port $PET_SERVICE_PORT is already in use. Please stop the service using this port."
    exit 1
fi

if ! check_port $ACTIVITY_SERVICE_PORT; then
    echo "❌ Port $ACTIVITY_SERVICE_PORT is already in use. Please stop the service using this port."
    exit 1
fi

if ! check_port $ACCESSORY_SERVICE_PORT; then
    echo "❌ Port $ACCESSORY_SERVICE_PORT is already in use. Please stop the service using this port."
    exit 1
fi

echo "✅ Ports $PET_SERVICE_PORT, $ACTIVITY_SERVICE_PORT, and $ACCESSORY_SERVICE_PORT are available"
echo ""

# Start Pet Service
echo "🐾 Starting Pet Service on port $PET_SERVICE_PORT..."
cd "$PROJECT_ROOT/backend/pet-service"

if [ ! -d "venv" ]; then
    echo "   📦 Creating virtual environment for Pet Service..."
    python3 -m venv venv
fi

echo "   🔧 Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1

if [ ! -f ".env" ]; then
    echo "   ⚙️ Creating .env file from .env.example..."
    cp .env.example .env
fi

echo "   🌟 Starting Pet Service..."
uvicorn main:app --host 0.0.0.0 --port $PET_SERVICE_PORT --reload > pet-service.log 2>&1 &
PET_SERVICE_PID=$!

# Wait a moment for the service to start
sleep 3

# Check if Pet Service started successfully
if kill -0 $PET_SERVICE_PID 2>/dev/null; then
    echo "   ✅ Pet Service started successfully (PID: $PET_SERVICE_PID)"
else
    echo "   ❌ Failed to start Pet Service"
    echo "   📋 Check pet-service.log for details"
    exit 1
fi

# Start Activity Service (port 8001)
echo ""
# Start Activity Service
echo "📊 Starting Activity Service on port $ACTIVITY_SERVICE_PORT..."
cd "$PROJECT_ROOT/backend/activity-service"

if [ ! -d "venv" ]; then
    echo "   📦 Creating virtual environment for Activity Service..."
    python3 -m venv venv
fi

echo "   🔧 Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1

if [ ! -f ".env" ]; then
    echo "   ⚙️ Creating .env file from .env.example..."
    cp .env.example .env
fi

echo "   🌟 Starting Activity Service..."
uvicorn main:app --host 0.0.0.0 --port $ACTIVITY_SERVICE_PORT --reload > activity-service.log 2>&1 &
ACTIVITY_SERVICE_PID=$!

# Wait a moment for the service to start
sleep 3

# Check if Activity Service started successfully
if kill -0 $ACTIVITY_SERVICE_PID 2>/dev/null; then
    echo "   ✅ Activity Service started successfully (PID: $ACTIVITY_SERVICE_PID)"
else
    echo "   ❌ Failed to start Activity Service"
    echo "   📋 Check activity-service.log for details"
    kill $PET_SERVICE_PID 2>/dev/null
    exit 1
fi

# Start Accessory Service (port 8002)
echo ""
echo "🛍️ Starting Accessory Service on port $ACCESSORY_SERVICE_PORT..."
cd "$PROJECT_ROOT/backend/accessory-service"

if [ ! -d "venv" ]; then
    echo "   📦 Creating virtual environment for Accessory Service..."
    python3 -m venv venv
fi

echo "   🔧 Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1

if [ ! -f ".env" ]; then
    echo "   ⚙️ Creating .env file from .env.example..."
    cp .env.example .env
fi

echo "   🌟 Starting Accessory Service..."
uvicorn main:app --host 0.0.0.0 --port $ACCESSORY_SERVICE_PORT --reload > accessory-service.log 2>&1 &
ACCESSORY_SERVICE_PID=$!

# Wait a moment for the service to start
sleep 3

# Check if Accessory Service started successfully
if kill -0 $ACCESSORY_SERVICE_PID 2>/dev/null; then
    echo "   ✅ Accessory Service started successfully (PID: $ACCESSORY_SERVICE_PID)"
else
    echo "   ❌ Failed to start Accessory Service"
    echo "   📋 Check accessory-service.log for details"
    kill $PET_SERVICE_PID 2>/dev/null
    kill $ACTIVITY_SERVICE_PID 2>/dev/null
    exit 1
fi

# Display service information
echo ""
echo "🎉 ALL SERVICES RUNNING SUCCESSFULLY!"
echo "====================================="
echo ""
echo "🐾 Pet Service:"
echo "   📡 API: http://localhost:$PET_SERVICE_PORT"
echo "   📚 Docs: http://localhost:$PET_SERVICE_PORT/docs"
echo "   🏥 Health: http://localhost:$PET_SERVICE_PORT/health"
echo "   📋 Log: $PROJECT_ROOT/backend/pet-service/pet-service.log"
echo ""
echo "📊 Activity Service:"
echo "   📡 API: http://localhost:$ACTIVITY_SERVICE_PORT"
echo "   📚 Docs: http://localhost:$ACTIVITY_SERVICE_PORT/docs"
echo "   🏥 Health: http://localhost:$ACTIVITY_SERVICE_PORT/health"
echo "   📋 Log: $PROJECT_ROOT/backend/activity-service/activity-service.log"
echo ""
echo "🛍️ Accessory Service:"
echo "   📡 API: http://localhost:$ACCESSORY_SERVICE_PORT"
echo "   📚 Docs: http://localhost:$ACCESSORY_SERVICE_PORT/docs"
echo "   🏥 Health: http://localhost:$ACCESSORY_SERVICE_PORT/health"
echo "   📋 Log: $PROJECT_ROOT/backend/accessory-service/accessory-service.log"
echo ""
echo "🧪 Testing:"
echo "   📖 Pet Service REST Client: backend/pet-service/pet-service.http"
echo "   📖 Activity Service REST Client: backend/activity-service/activity-service.http"
echo "   📖 Accessory Service REST Client: backend/accessory-service/accessory-service.http"
echo ""
echo "💡 Prerequisites:"
echo "   🗄️ Azure CosmosDB Emulator should be running on http://localhost:8081"
echo "   🔧 Or update .env files with your Azure CosmosDB credentials"
echo ""
echo "🏥 Running health checks..."
echo ""

# Health check for Pet Service
echo "   Checking Pet Service health..."
PET_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PET_SERVICE_PORT/health)
if [ "$PET_HEALTH" = "200" ]; then
    echo "   ✅ Pet Service health check passed (HTTP $PET_HEALTH)"
else
    echo "   ⚠️  Pet Service health check returned HTTP $PET_HEALTH"
fi

# Health check for Activity Service
echo "   Checking Activity Service health..."
ACTIVITY_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$ACTIVITY_SERVICE_PORT/health)
if [ "$ACTIVITY_HEALTH" = "200" ]; then
    echo "   ✅ Activity Service health check passed (HTTP $ACTIVITY_HEALTH)"
else
    echo "   ⚠️  Activity Service health check returned HTTP $ACTIVITY_HEALTH"
fi

# Health check for Accessory Service
echo "   Checking Accessory Service health..."
ACCESSORY_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$ACCESSORY_SERVICE_PORT/health)
if [ "$ACCESSORY_HEALTH" = "200" ]; then
    echo "   ✅ Accessory Service health check passed (HTTP $ACCESSORY_HEALTH)"
else
    echo "   ⚠️  Accessory Service health check returned HTTP $ACCESSORY_HEALTH"
fi

echo ""
echo "🎨 Starting Frontend UI..."
echo ""

# Start Frontend Docker Container
echo "   🚀 Starting Frontend UI container..."
if docker run -d \
   -p $FRONTEND_PORT:80 \
   -e VITE_API_PETS_URL="$PETS_URL" \
   -e VITE_API_ACTIVITIES_URL="$ACTIVITIES_URL" \
   -e VITE_API_ACCESSORIES_URL="$ACCESSORIES_URL" \
   -e VITE_API_GITHUB_TOKEN="$GITHUB_TOKEN" \
   --name "$FRONTEND_CONTAINER_NAME" \
   ghcr.io/michalmar/petpal-ui:latest >/dev/null 2>&1; then
    echo "   ✅ Frontend UI started successfully"
    echo "   🌐 Frontend URL: https://${CODESPACE_NAME}-${FRONTEND_PORT}.app.github.dev"
else
    echo "   ⚠️  Failed to start Frontend UI container (may already be running)"
fi

echo ""
echo "⚠️  Press Ctrl+C to stop all services"
echo ""

# Keep script running and monitor services
while true; do
    # Check if Pet Service is still running
    if ! kill -0 $PET_SERVICE_PID 2>/dev/null; then
        echo "❌ Pet Service stopped unexpectedly"
        break
    fi
    
    # Check if Activity Service is still running
    if ! kill -0 $ACTIVITY_SERVICE_PID 2>/dev/null; then
        echo "❌ Activity Service stopped unexpectedly"
        break
    fi
    
    # Check if Accessory Service is still running
    if ! kill -0 $ACCESSORY_SERVICE_PID 2>/dev/null; then
        echo "❌ Accessory Service stopped unexpectedly"
        break
    fi
    
    sleep 5
done

# Cleanup will be handled by the trap
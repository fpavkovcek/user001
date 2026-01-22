#!/bin/bash

# Accessory Service Startup Script
# This script helps set up and run the Accessory Service API

set -e  # Exit on any error

echo "🎒 Accessory Service Setup and Startup Script"
echo "=============================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python installation
if ! command_exists python3; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is available
if ! command_exists pip3; then
    echo "❌ Error: pip3 is not installed"
    exit 1
fi

echo "✅ pip3 found: $(pip3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists, try parent directory
if [ ! -f ".env" ]; then
    if [ -f "../../.env" ]; then
        echo "📋 Using .env file from project root..."
        export $(grep -v '^#' ../../.env | xargs)
    elif [ -f ".env.example" ]; then
        echo "⚙️  Creating .env file from .env.example..."
        cp .env.example .env
        echo "⚠️  Please edit .env file with your Azure CosmosDB configuration before running the service"
        echo "📝 Required variables:"
        echo "   - COSMOS_ENDPOINT: Your CosmosDB endpoint URL"
        echo "   - COSMOS_KEY: Your CosmosDB primary or secondary access key"
        echo "   - COSMOS_DATABASE_NAME: Database name (default: accessoryservice)"
        echo "   - COSMOS_CONTAINER_NAME: Container name (default: accessories)"
        echo ""
        echo "🔐 For local development with CosmosDB Emulator:"
        echo "   - COSMOS_ENDPOINT=http://localhost:8081"
        echo "   - COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
        echo ""
        read -p "Press Enter to continue after editing .env file..."
    else
        echo "⚠️  No .env file found, checking environment variables..."
    fi
else
    echo "📋 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Check if required environment variables are set
if [ -z "$COSMOS_ENDPOINT" ]; then
    echo "❌ Error: COSMOS_ENDPOINT environment variable is not set"
    echo "Please set COSMOS_ENDPOINT or create a .env file"
    exit 1
fi

if [ -z "$COSMOS_KEY" ]; then
    echo "❌ Error: COSMOS_KEY environment variable is not set"
    echo "Please set COSMOS_KEY or create a .env file"
    exit 1
fi

echo "✅ Configuration looks good!"

# Check CosmosDB configuration
echo "🔐 Checking CosmosDB configuration..."
echo "📡 Endpoint: $COSMOS_ENDPOINT"
echo "🗃️  Database: ${COSMOS_DATABASE_NAME:-accessoryservice}"
echo "📦 Container: ${COSMOS_CONTAINER_NAME:-accessories}"
if [[ "$COSMOS_ENDPOINT" == *"localhost"* ]]; then
    echo "🔧 Using CosmosDB Emulator (localhost)"
else
    echo "☁️  Using Azure CosmosDB"
fi

# Run tests (optional)
if [ "$1" = "--test" ]; then
    echo "🧪 Running tests..."
    python -m pytest test_main.py -v
    if [ $? -eq 0 ]; then
        echo "✅ All tests passed!"
    else
        echo "❌ Some tests failed"
        exit 1
    fi
fi

# Start the service
echo "🚀 Starting Accessory Service API..."
echo "📡 Server will be available at: http://localhost:8030"
echo "📚 API documentation: http://localhost:8030/docs"
echo "🔍 Health check: http://localhost:8030/health"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

# Run the FastAPI application
python main.py

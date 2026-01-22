#!/bin/bash
# Start script for Discussions Service

set -e

# Change to the script's directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your configuration."
fi

# Start the service
echo "Starting Discussions Service..."
uvicorn main:app --host 0.0.0.0 --port 8002 --reload

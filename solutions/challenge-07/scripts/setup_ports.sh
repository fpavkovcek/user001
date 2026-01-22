#!/bin/bash

# Script to set multiple port visibilities to public
# This runs after the devcontainer is created

echo "Setting up port visibility for Codespaces..."

# Check if we're in a Codespace
if [ -z "$CODESPACE_NAME" ]; then
  echo "Not running in a GitHub Codespace, skipping port visibility setup."
  exit 0
fi

# Function to change port visibility
change_port_visibility() {
  local port=$1
  local visibility=$2
  echo "Setting port $port to $visibility..."
  gh codespace ports visibility $port:$visibility -c $CODESPACE_NAME 2>&1 || echo "Warning: Could not set port $port visibility"
}

# Set backend service ports to public
change_port_visibility 8010 public  # backend-pets
change_port_visibility 8020 public  # backend-activities
change_port_visibility 8030 public  # backend-accessories

# Optionally set frontend to public as well
change_port_visibility 3000 public  # frontend

echo "Port visibility setup complete!"

#!/bin/bash
# cleanup_conductor_workspace.sh - Clean up resources when removing a Conductor workspace

# Check if Conductor environment variables are set
if [ -z "$CONDUCTOR_WORKSPACE_NAME" ]; then
    echo "Error: This script should be run within a Conductor workspace"
    echo "CONDUCTOR_WORKSPACE_NAME is not set"
    exit 1
fi

echo "Cleaning up Conductor workspace: $CONDUCTOR_WORKSPACE_NAME"

BASE_DIR="$CONDUCTOR_ROOT_PATH"
PORT_MANAGER="$BASE_DIR/manage_conductor_ports.py"

# Stop any running containers
if [ -f "docker-compose.yml" ]; then
    echo "Stopping Docker containers..."
    docker-compose down -v 2>/dev/null || true
fi

# Release reserved ports
if [ -f "$PORT_MANAGER" ]; then
    echo "Releasing reserved ports..."
    python3 "$PORT_MANAGER" release "$CONDUCTOR_WORKSPACE_NAME"
else
    echo "Port manager not found, skipping port release"
fi

echo "Cleanup complete for workspace: $CONDUCTOR_WORKSPACE_NAME"

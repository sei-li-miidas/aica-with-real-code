#!/bin/bash

echo "Stopping existing MCP server..."
docker stop mcp-server
docker rm mcp-server

echo "Starting the MCP server..."
START_SCRIPT=run.sh docker compose --env-file=.env.local -f docker/compose-mcp.yaml up -d mcp-server --force-recreate

echo "Waiting for server to start..."

while [ "$(docker inspect -f '{{.State.Status}}' mcp-server 2>/dev/null)" != "running" ]; do
    echo "Waiting for container to start..."
    sleep 1
done

TIMEOUT=120
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if docker logs mcp-server 2>&1 | grep -q "All setup success\. Start server\."; then
        echo "server is ready!"
        echo "MCP server started."
        exit 0
    fi
    echo "Still waiting for server... ($ELAPSED/$TIMEOUT seconds)"
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

echo "Timeout waiting for server to start"
exit 1

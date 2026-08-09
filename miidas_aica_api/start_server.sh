#!/bin/bash

if [ $# -gt 0 ]; then
    GO_BUILD_TAGS="$*"
fi
if [ -n "${GO_BUILD_TAGS:-}" ] && [[ "$GO_BUILD_TAGS" != -* ]]; then
    # Treat space-separated values as multiple tags and convert spaces to commas
    GO_BUILD_TAGS="-tags=$(echo "$GO_BUILD_TAGS" | tr ' ' ',')"
fi

echo "Stopping existing API server..."
docker stop api-server
docker rm api-server

echo "Starting the API server..."
if [ -n "${GO_BUILD_TAGS:-}" ]; then
    echo "Using Go build tags: $GO_BUILD_TAGS"
fi
GO_BUILD_TAGS="${GO_BUILD_TAGS:-}" START_SCRIPT=run.sh docker compose --env-file=.env.local -f docker/compose-api.yaml up -d api-server --force-recreate

echo "Waiting for server to start..."

while [ "$(docker inspect -f '{{.State.Status}}' api-server 2>/dev/null)" != "running" ]; do
    echo "Waiting for container to start..."
    sleep 1
done

TIMEOUT=120
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if docker logs api-server 2>&1 | grep -q "all setup success\. start server\."; then
        echo "server is ready!"
        echo "API server started."
        exit 0
    fi
    echo "Still waiting for server... ($ELAPSED/$TIMEOUT seconds)"
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

echo "Timeout waiting for server to start"
exit 1

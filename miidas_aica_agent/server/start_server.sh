#!/bin/bash

echo "Stopping existing Agent server..."
docker stop agent-server
docker rm agent-server

echo "Starting the Agent server..."
docker compose --env-file=.env.local -f docker/compose-agent.yaml up -d localstack agent-server redis --build --force-recreate

echo "Waiting for server to start..."

while [ "$(docker inspect -f '{{.State.Status}}' agent-server 2>/dev/null)" != "running" ]; do
    echo "Waiting for container to start..."
    sleep 1
done

TIMEOUT=120
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if docker logs agent-server 2>&1 | grep -q "Application startup complete\."; then
        echo "server is ready!"
        echo "Agent server started."
        exit 0
    fi
    echo "Still waiting for server... ($ELAPSED/$TIMEOUT seconds)"
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

echo "Timeout waiting for server to start"
exit 1

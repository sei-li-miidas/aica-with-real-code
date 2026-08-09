#!/bin/bash

echo "Stopping existing Frontend container..."
docker stop aica-frontend
docker rm aica-frontend
docker rmi ai-ca-frontend

echo "Starting the Frontend container..."
docker compose --env-file=.env.local -f docker/compose-frontend.yaml up -d --force-recreate

echo "Waiting for Frontend container to start..."

while [ "$(docker inspect -f '{{.State.Status}}' aica-frontend 2>/dev/null)" != "running" ]; do
    echo "Waiting for container to start..."
    sleep 1
done

TIMEOUT=120
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if docker logs aica-frontend 2>&1 | grep -q "Configuration complete; ready for start up"; then
        echo "Frontend is ready!"
        echo "Frontend container started."
        exit 0
    fi
    echo "Still waiting for Frontend container... ($ELAPSED/$TIMEOUT seconds)"
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

echo "Timeout waiting for Frontend container to start"
exit 1
#!/bin/bash

echo "Stopping existing Agent server..."
docker stop agent-server
docker rm agent-server

echo "Starting the Agent server..."
docker compose --env-file=.env.local -f docker/compose-agent.yaml up -d localstack agent-server-debug --build --force-recreate

echo "Waiting for debug server to start..."

TIMEOUT=120
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if [ "$(docker inspect -f '{{.State.Status}}' agent-server 2>/dev/null)" = "running" ]; then
        echo "Debug server is ready and listening on port 5678!"
        echo "Agent server started."
        echo "Wait a few seconds, otherwise debugger can't attach to it."
        sleep 5
        exit 0
    fi
    echo "Still waiting for debug server... ($ELAPSED/$TIMEOUT seconds)"
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

echo "Timeout waiting for debug server to start"
exit 1
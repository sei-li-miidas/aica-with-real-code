#!/bin/bash

set -x

update-ca-certificates

cd /go/src/aica

echo "Installing delve"
CGO_ENABLED=0 go install -ldflags "-s -w -extldflags '-static'" github.com/go-delve/delve/cmd/dlv@latest

echo "Building MCP Server for debugging"
go build -gcflags="all=-N -l" -o /go/bin/mcpserver main.go

echo "Starting Delve debugger on port 6000"
/go/bin/dlv --listen=:6000 --headless=true --api-version=2 --accept-multiclient exec /go/bin/mcpserver -- --debug=true

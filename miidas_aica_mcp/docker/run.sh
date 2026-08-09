#!/bin/bash

set -x

update-ca-certificates

cd /go/src/aica

echo "Building MCP Server"
go build -o /go/bin/mcpserver main.go

/go/bin/mcpserver --debug=true

tail -f /dev/null

#!/bin/bash

set -x

update-ca-certificates

cd /go/src/aica

echo "Installing delve"
CGO_ENABLED=0 go install -ldflags "-s -w -extldflags '-static'" github.com/go-delve/delve/cmd/dlv@latest

echo "Building API Server for debugging"
BUILD_ARGS=()
if [ -n "${GO_BUILD_TAGS:-}" ]; then
  # Intentional word-splitting so multiple flags can be passed in one env var.
  # shellcheck disable=SC2206
  BUILD_ARGS=(${GO_BUILD_TAGS})
fi
go build "${BUILD_ARGS[@]}" -gcflags="all=-N -l" -o /go/bin/apiserver ./api/mcptool/http

echo "Starting Delve debugger on port 4000"
/go/bin/dlv --listen=:4000 --headless=true --api-version=2 --accept-multiclient exec /go/bin/apiserver -- --debug=true --show-routes=true

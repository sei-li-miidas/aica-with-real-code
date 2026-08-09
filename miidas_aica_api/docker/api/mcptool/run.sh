#!/bin/bash

set -x

update-ca-certificates

cd /go/src/aica

echo "Building API Server"
BUILD_ARGS=()
if [ -n "${GO_BUILD_TAGS:-}" ]; then
  # Intentional word-splitting so multiple flags can be passed in one env var.
  # shellcheck disable=SC2206
  BUILD_ARGS=(${GO_BUILD_TAGS})
fi
go build "${BUILD_ARGS[@]}" -o /go/bin/apiserver ./api/mcptool/http

/go/bin/apiserver --debug=true --show-routes=true

tail -f /dev/null

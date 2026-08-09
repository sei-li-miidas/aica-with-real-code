#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env.local"

if [ -f "$ENV_FILE" ]; then
	set -a
	source "$ENV_FILE"
	set +a
else
	echo "Missing env file: ${ENV_FILE}" >&2
	exit 1
fi

PYTHON_BIN="${SCRIPT_DIR}/../.venv-e2e/bin/python"

if [ -x "$PYTHON_BIN" ]; then
	"$PYTHON_BIN" "${SCRIPT_DIR}/src/aica_client/main.py"
elif command -v python3 >/dev/null 2>&1; then
	python3 "${SCRIPT_DIR}/src/aica_client/main.py"
elif command -v python >/dev/null 2>&1; then
	python "${SCRIPT_DIR}/src/aica_client/main.py"
else
	echo "No Python interpreter found." >&2
	exit 1
fi

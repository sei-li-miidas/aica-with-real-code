#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

TEST_FILE_INPUT="${1:-}"
TEST_NODE_ID_INPUT="${2:-}"

resolve_test_file() {
  local input="$1"
  local resolved=""

  if [[ -z "$input" ]]; then
    echo ""
    return 0
  fi

  # If a path is provided, validate it directly.
  if [[ "$input" == *"/"* ]]; then
    if [[ ! -f "$input" ]]; then
      echo "Test file not found: $input" >&2
      return 2
    fi
    resolved="$input"
  else
    # If only a filename is provided, search under server/tests.
    matches=()
    while IFS= read -r match; do
      [[ -n "$match" ]] && matches+=("$match")
    done < <(find tests -type f -name "$input" 2>/dev/null || true)
    if [[ "${#matches[@]}" -eq 0 ]]; then
      echo "Test file not found under $SCRIPT_DIR/tests: $input" >&2
      echo "Example: ./run_tests.sh tests/unit/$input" >&2
      return 2
    fi
    if [[ "${#matches[@]}" -gt 1 ]]; then
      echo "Multiple test files matched '$input'. Please specify one of:" >&2
      printf '%s\n' "${matches[@]}" >&2
      return 2
    fi
    resolved="${matches[0]}"
  fi

  if command -v realpath >/dev/null 2>&1; then
    resolved="$(realpath "$resolved")"
  else
    resolved="$(
      python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$resolved"
    )"
  fi

  if [[ "$resolved" != "$SCRIPT_DIR/tests/"* ]]; then
    echo "Test file must be under $SCRIPT_DIR/tests: $resolved" >&2
    return 2
  fi

  echo "$resolved"
}

TEST_FILE_ABS="$(resolve_test_file "$TEST_FILE_INPUT")"

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  export OPENAI_API_KEY="test-key"
  echo "OPENAI_API_KEY is not set; using dummy value for tests."
fi

if [[ -n "$TEST_FILE_INPUT" && -z "$TEST_FILE_ABS" ]]; then
  exit 2
fi

echo "Starting docker containers via start_server.sh..."
./start_server.sh

PYTEST_ARGS=(
  -v
  --cov=application
  --cov=endpoints
  --cov=repositories
  --cov=services
  --cov=utils
  --cov=core
  --cov=domain
  --cov=security
  --cov-report=term-missing
  --cov-report=html
)

if [[ -n "$TEST_FILE_ABS" ]]; then
  TEST_FILE_REL="${TEST_FILE_ABS#"$SCRIPT_DIR/"}" # starts with tests/...
  CONTAINER_TEST_TARGET="/home/app/$TEST_FILE_REL"

  if [[ -n "$TEST_NODE_ID_INPUT" ]]; then
    # 2つ目の引数はpytestのnode id（例: test_func / ClassName::test_func）として扱う
    CONTAINER_TEST_TARGET="${CONTAINER_TEST_TARGET}::${TEST_NODE_ID_INPUT}"
  fi

  echo "Running single test file (with coverage): $TEST_FILE_REL"
  if [[ -n "$TEST_NODE_ID_INPUT" ]]; then
    echo "Test node id: $TEST_NODE_ID_INPUT"
  fi
  docker exec -i agent-server bash -lc "
    cd /home/app/tests/unit && \
    pytest \"${CONTAINER_TEST_TARGET}\" ${PYTEST_ARGS[*]}
  "
else
  echo "Running all unit tests (with coverage)..."
  docker exec -i agent-server bash -lc "
    cd /home/app/tests/unit && \
    pytest ${PYTEST_ARGS[*]}
  "
fi

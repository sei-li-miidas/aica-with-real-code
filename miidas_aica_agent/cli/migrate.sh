#!/bin/bash

# Flyway Migration Script
# Automates database migration execution using Flyway
# Reads database connection parameters from server/.env.local file and executes migrations

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERBOSE=false
CLEAN_MODE=false
POSITION_VECTORS_FILE=""

# Usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Flyway Migration Script - Automates database migration execution using Flyway

OPTIONS:
    -v, --verbose                    Enable verbose logging
    -h, --help                       Show this help message
    --clean                          Execute Flyway clean before migration (WARNING: deletes all data)
    --position-vectors=FILE          Path to SQL file containing position vector data to load after migration

DESCRIPTION:
    This script reads database connection parameters from a server/.env.local file in the server
    directory and executes Flyway migrations. The server/.env.local file must contain the
    required database connection parameters.

    The --clean option will delete ALL data from the database before running migrations.
    Use with extreme caution as this operation is irreversible.

    The --position-vectors option allows loading initial data after successful migrations.
    The specified file must be a valid SQL file that will be executed in the database container.

EXAMPLES:
    $0                               Run migrations with default settings
    $0 --verbose                     Run migrations with verbose logging
    $0 --clean                       Clean database and run migrations (WARNING: deletes data)
    $0 --position-vectors=data.sql   Run migrations and load position vector data
    $0 --clean --position-vectors=data.sql --verbose   Full database reset with data loading
    $0 --help                        Show this help message

EOF
}

# Enhanced logging functions with comprehensive timestamp support and context
log_message() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local pid=$$
    
    case "$level" in
        "INFO")
            echo "[$timestamp] [INFO] [PID:$pid] $message"
            ;;
        "ERROR")
            echo "[$timestamp] [ERROR] [PID:$pid] $message" >&2
            ;;
        "SUCCESS")
            echo "[$timestamp] [SUCCESS] [PID:$pid] $message"
            ;;
        "VERBOSE")
            if [[ "$VERBOSE" == "true" ]]; then
                echo "[$timestamp] [VERBOSE] [PID:$pid] $message"
            fi
            ;;
        "DEBUG")
            if [[ "$VERBOSE" == "true" ]]; then
                echo "[$timestamp] [DEBUG] [PID:$pid] $message"
            fi
            ;;
        "WARN")
            echo "[$timestamp] [WARN] [PID:$pid] $message" >&2
            ;;
        *)
            echo "[$timestamp] [LOG] [PID:$pid] $message"
            ;;
    esac
}

# Enhanced convenience logging functions with context support
log_info() {
    log_message "INFO" "$@"
}

log_error() {
    log_message "ERROR" "$@"
}

log_success() {
    log_message "SUCCESS" "$@"
}

log_verbose() {
    log_message "VERBOSE" "$@"
}

log_debug() {
    log_message "DEBUG" "$@"
}

log_warn() {
    log_message "WARN" "$@"
}

# Enhanced error logging with context information
log_error_with_context() {
    local error_message="$1"
    local context="$2"
    local function_name="${FUNCNAME[1]:-main}"
    local line_number="${BASH_LINENO[0]:-unknown}"
    
    log_error "$error_message"
    if [[ -n "$context" ]]; then
        log_error "Context: $context"
    fi
    log_verbose "Error occurred in function: $function_name at line: $line_number"
}

# Operation logging with timing
log_operation_start() {
    local operation="$1"
    log_info "Starting operation: $operation"
    log_verbose "Operation start time: $(date '+%Y-%m-%d %H:%M:%S.%3N')"
}

log_operation_end() {
    local operation="$1"
    local status="$2"  # "success" or "failed"
    
    if [[ "$status" == "success" ]]; then
        log_success "Completed operation: $operation"
    else
        log_error "Failed operation: $operation"
    fi
    log_verbose "Operation end time: $(date '+%Y-%m-%d %H:%M:%S.%3N')"
}

# Command line argument parsing
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--verbose)
                VERBOSE=true
                log_verbose "Verbose mode enabled"
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            --clean)
                CLEAN_MODE=true
                log_verbose "Clean mode enabled - database will be reset before migration"
                shift
                ;;
            --position-vectors=*)
                POSITION_VECTORS_FILE="${1#*=}"
                if [[ -z "$POSITION_VECTORS_FILE" ]]; then
                    log_error "Position vectors file path cannot be empty"
                    log_error "Usage: --position-vectors=path/to/file.sql"
                    exit 1
                fi
                log_verbose "Position vectors file specified: $POSITION_VECTORS_FILE"
                shift
                ;;
            --position-vectors)
                log_error "Position vectors option requires a file path"
                log_error "Usage: --position-vectors=path/to/file.sql"
                exit 1
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Load environment configuration from server/.env.local file
load_env_config() {
    local env_file="./server/.env.local"
    
    log_operation_start "Environment configuration loading"
    log_verbose "Loading environment configuration from: $env_file"
    
    # Check if server/.env.local file exists and is readable
    if [[ ! -f "$env_file" ]]; then
        log_error_with_context "Environment file not found: $env_file" "load_env_config function"
        log_error "Please create a server/.env.local file in the server directory with required database parameters"
        return 1
    fi
    
    if [[ ! -r "$env_file" ]]; then
        log_error_with_context "Environment file is not readable: $env_file" "load_env_config function"
        log_error "Please check file permissions for the server/.env.local file"
        return 1
    fi
    
    log_verbose "Environment file found and readable"
    
    # Parse key-value pairs from server/.env.local file
    # Skip empty lines and comments (lines starting with #)
    local line_number=0
    while IFS= read -r line || [[ -n "$line" ]]; do
        ((line_number++))
        
        # Skip empty lines
        [[ -z "$line" ]] && continue
        
        # Skip comments
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        
        # Check if line contains '=' character for key-value format
        if [[ ! "$line" =~ = ]]; then
            # Skip lines that are only whitespace
            if [[ "$line" =~ ^[[:space:]]*$ ]]; then
                continue
            fi
            log_error_with_context "Invalid server/.env.local file format at line $line_number: '$line'" "Parsing server/.env.local file"
            log_error "Expected format: KEY=VALUE"
            log_error "Lines must contain '=' character to separate key and value"
            return 1
        fi
        
        # Split on first '=' character
        key="${line%%=*}"
        value="${line#*=}"
        
        # Trim whitespace from key and value
        key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        
        # Validate key format (must not be empty and contain valid characters)
        if [[ -z "$key" ]]; then
            log_error_with_context "Invalid server/.env.local file format at line $line_number: empty key" "Parsing server/.env.local file"
            log_error "Keys cannot be empty"
            return 1
        fi
        
        # Check for valid key format (alphanumeric and underscore only)
        if [[ ! "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
            log_error_with_context "Invalid server/.env.local file format at line $line_number: invalid key '$key'" "Parsing server/.env.local file"
            log_error "Keys must start with a letter or underscore and contain only letters, numbers, and underscores"
            return 1
        fi
        
        # Remove quotes from value if present
        if [[ "$value" =~ ^\".*\"$ ]] || [[ "$value" =~ ^\'.*\'$ ]]; then
            value="${value:1:-1}"
        fi
        
        # Export the environment variable
        export "$key"="$value"
        log_verbose "Loaded environment variable: $key"
        
    done < "$env_file"
    
    log_info "Environment configuration loaded successfully"
    log_operation_end "Environment configuration loading" "success"
}

# Validate required parameters and construct derived configuration
validate_and_construct_config() {
    log_operation_start "Parameter validation and configuration construction"
    log_verbose "Validating required parameters and constructing configuration"
    
    # Define required parameters
    local required_params=("AICA_AGENT_DB_HOST" "AICA_AGENT_DB_PORT" "AICA_AGENT_DB_NAME" "AICA_AGENT_DB_USER" "AICA_AGENT_DB_PASSWORD" "AICA_MIGRATION_DIR")
    local missing_params=()
    
    # Check for missing required parameters
    for param in "${required_params[@]}"; do
        if [[ -z "${!param:-}" ]]; then
            missing_params+=("$param")
        fi
    done
    
    # If any parameters are missing, report and return error
    if [[ ${#missing_params[@]} -gt 0 ]]; then
        log_error_with_context "Missing required parameters in server/.env.local file" "validate_and_construct_config function"
        for param in "${missing_params[@]}"; do
            log_error "  - $param"
        done
        log_error "Please ensure all required parameters are defined in the server/.env.local file"
        return 1
    fi
    
    log_verbose "All required parameters found"
    
    # Validate port number format
    if ! [[ "$AICA_AGENT_DB_PORT" =~ ^[0-9]+$ ]] || [[ "$AICA_AGENT_DB_PORT" -lt 1 ]] || [[ "$AICA_AGENT_DB_PORT" -gt 65535 ]]; then
        log_error_with_context "Invalid database port: $AICA_AGENT_DB_PORT" "validate_and_construct_config function"
        log_error "Port must be a number between 1 and 65535"
        return 1
    fi
    
    log_verbose "Database port validation passed: $AICA_AGENT_DB_PORT"
    
    # Construct DB_CONNECTION_STRING from individual database parameters
    # If AICA_AGENT_DB_HOST is "pgvector", use "localhost" for Flyway connection
    local flyway_db_host="${AICA_AGENT_DB_HOST}"
    if [[ "${AICA_AGENT_DB_HOST}" == "pgvector" ]]; then
        flyway_db_host="localhost"
        log_verbose "Using 'localhost' instead of 'pgvector' for Flyway connection"
    fi
    
    DB_CONNECTION_STRING="jdbc:postgresql://${flyway_db_host}:${AICA_AGENT_DB_PORT}/${AICA_AGENT_DB_NAME}"
    export DB_CONNECTION_STRING
    log_verbose "Constructed DB_CONNECTION_STRING: $DB_CONNECTION_STRING"
    
    # Construct FLYWAY_LOCATIONS from AICA_MIGRATION_DIR parameter
    FLYWAY_LOCATIONS="filesystem:${AICA_MIGRATION_DIR}"
    export FLYWAY_LOCATIONS
    log_verbose "Constructed FLYWAY_LOCATIONS: $FLYWAY_LOCATIONS"
    
    # Export all environment variables for Flyway usage
    export AICA_AGENT_DB_HOST AICA_AGENT_DB_PORT AICA_AGENT_DB_NAME AICA_AGENT_DB_USER AICA_AGENT_DB_PASSWORD AICA_MIGRATION_DIR
    
    log_info "Parameter validation and configuration construction completed successfully"
    log_operation_end "Parameter validation and configuration construction" "success"
}

# Validate Docker container if using pgvector
validate_docker_container() {
    log_operation_start "Docker container validation"
    
    # Check if AICA_AGENT_DB_HOST is "pgvector" (containerized PostgreSQL)
    if [[ "${AICA_AGENT_DB_HOST:-}" == "pgvector" ]]; then
        log_info "Detected containerized PostgreSQL (AICA_AGENT_DB_HOST=pgvector)"
        log_verbose "Validating Docker container status"
        
        # Check if docker is available
        if ! command -v docker >/dev/null 2>&1; then
            log_error "Docker command is not available"
            log_error "AICA_AGENT_DB_HOST is set to 'pgvector' indicating containerized PostgreSQL"
            log_error "Docker is required to validate and connect to the PostgreSQL container"
            log_error ""
            log_error "Docker installation instructions:"
            log_error "  Visit: https://docs.docker.com/get-docker/"
            exit 2
        fi
        
        log_verbose "Docker command found, checking container status"
        
        # Check if container exists
        if ! docker ps -a --format '{{.Names}}' | grep -q "^pgvector$"; then
            log_error "PostgreSQL container 'pgvector' does not exist"
            log_error "AICA_AGENT_DB_HOST is set to 'pgvector' but the container was not found"
            log_error ""
            log_error "Please either:"
            log_error "  1. Create and start the PostgreSQL container named 'pgvector'"
            log_error "  2. Change AICA_AGENT_DB_HOST to the correct container name or hostname"
            log_error ""
            log_error "To list available containers: docker ps -a"
            exit 2
        fi
        
        log_verbose "Container 'pgvector' exists"
        
        # Check if container is running
        if ! docker ps --format '{{.Names}}' | grep -q "^pgvector$"; then
            log_error "PostgreSQL container 'pgvector' exists but is not running"
            log_error "The container must be running before executing migrations"
            log_error ""
            log_error "To start the container: docker start pgvector"
            log_error "To check container status: docker ps -a | grep pgvector"
            exit 2
        fi
        
        log_success "PostgreSQL container 'pgvector' is running and ready"
        log_info "Container validation completed successfully"
    else
        log_verbose "Using direct database connection (AICA_AGENT_DB_HOST=${AICA_AGENT_DB_HOST})"
        log_verbose "Skipping Docker container validation"
    fi
    
    log_operation_end "Docker container validation" "success"
}

# Validate database connection
validate_database_connection() {
    log_operation_start "Database connection validation"
    log_verbose "Validating database connection"
    
    # Validate database connection parameters before attempting connection
    if [[ -z "$AICA_AGENT_DB_HOST" ]] || [[ -z "$AICA_AGENT_DB_PORT" ]] || [[ -z "$AICA_AGENT_DB_NAME" ]] || [[ -z "$AICA_AGENT_DB_USER" ]] || [[ -z "$AICA_AGENT_DB_PASSWORD" ]]; then
        log_error "Database connection parameters are incomplete"
        log_error "All parameters (AICA_AGENT_DB_HOST, AICA_AGENT_DB_PORT, AICA_AGENT_DB_NAME, AICA_AGENT_DB_USER, AICA_AGENT_DB_PASSWORD) must be set"
        exit 2
    fi
    
    log_info "Testing database connectivity to ${AICA_AGENT_DB_HOST}:${AICA_AGENT_DB_PORT}/${AICA_AGENT_DB_NAME}"
    
    # Check if psql is available for PostgreSQL connections
    local use_docker=false
    local docker_container_name="${AICA_AGENT_DB_HOST}"
    
    if ! command -v psql >/dev/null 2>&1; then
        log_warn "PostgreSQL client (psql) is not installed or not in PATH"
        log_info "Checking if PostgreSQL is running in a Docker container..."
        
        # Check if docker is available
        if ! command -v docker >/dev/null 2>&1; then
            log_error "Neither psql nor docker command is available"
            log_error "Database connectivity validation requires either:"
            log_error "  1. PostgreSQL client tools (psql), OR"
            log_error "  2. Docker (if PostgreSQL is running in a container)"
            log_error ""
            log_error "PostgreSQL client installation instructions:"
            log_error "  On Ubuntu/Debian: sudo apt-get install postgresql-client"
            log_error "  On macOS: brew install postgresql"
            log_error "  On CentOS/RHEL: sudo yum install postgresql"
            log_error ""
            log_error "Docker installation instructions:"
            log_error "  Visit: https://docs.docker.com/get-docker/"
            exit 2
        fi
        
        log_verbose "Docker command found, checking for container: ${docker_container_name}"
        
        # Check if container exists
        if ! docker ps -a --format '{{.Names}}' | grep -q "^${docker_container_name}$"; then
            log_error "PostgreSQL container '${docker_container_name}' does not exist"
            log_error "Neither psql client nor PostgreSQL container found"
            log_error ""
            log_error "Please either:"
            log_error "  1. Install PostgreSQL client tools (psql)"
            log_error "  2. Ensure PostgreSQL container '${docker_container_name}' exists"
            log_error "  3. Verify AICA_AGENT_DB_HOST is set to the correct container name"
            log_error ""
            log_error "To list available containers: docker ps -a"
            exit 2
        fi
        
        log_verbose "Container '${docker_container_name}' exists"
        
        # Check if container is running
        if ! docker ps --format '{{.Names}}' | grep -q "^${docker_container_name}$"; then
            log_error "PostgreSQL container '${docker_container_name}' exists but is not running"
            log_error "Please start the container before running migrations"
            log_error ""
            log_error "To start the container: docker start ${docker_container_name}"
            log_error "To check container status: docker ps -a | grep ${docker_container_name}"
            exit 2
        fi
        
        log_info "PostgreSQL container '${docker_container_name}' is running"
        log_info "Will use Docker to execute database connectivity test"
        use_docker=true
    else
        log_verbose "PostgreSQL client (psql) found in PATH"
    fi
    
    # Set connection timeout (30 seconds)
    local connection_timeout=30
    
    # Test database connection using appropriate method
    local connection_result
    local connection_output
    
    log_verbose "Attempting database connection with timeout of ${connection_timeout} seconds"
    log_verbose "Connection parameters: ${AICA_AGENT_DB_USER}@${AICA_AGENT_DB_HOST}:${AICA_AGENT_DB_PORT}/${AICA_AGENT_DB_NAME}"
    
    if [[ "$use_docker" == "true" ]]; then
        # Use Docker to execute psql inside the container
        log_verbose "Using Docker container '${docker_container_name}' for database connectivity test"
        
        # Execute psql command inside the Docker container
        # Use environment variables for connection parameters
        if connection_output=$(docker exec "${docker_container_name}" psql \
            -h localhost \
            -p "${AICA_AGENT_DB_PORT}" \
            -U "${AICA_AGENT_DB_USER}" \
            -d "${AICA_AGENT_DB_NAME}" \
            -c "SELECT 1;" -t -A 2>&1); then
            connection_result=0
            log_verbose "Database connection test query executed successfully via Docker"
        else
            connection_result=$?
            log_verbose "Database connection test failed via Docker with exit code: $connection_result"
        fi
    else
        # Use direct psql connection
        log_verbose "Using direct psql connection"
        
        # Construct connection string for psql
        local psql_connection="postgresql://${AICA_AGENT_DB_USER}:${AICA_AGENT_DB_PASSWORD}@${AICA_AGENT_DB_HOST}:${AICA_AGENT_DB_PORT}/${AICA_AGENT_DB_NAME}"
        
        # Execute psql command directly
        if connection_output=$(psql "${psql_connection}" -c "SELECT 1;" -t -A 2>&1); then
            connection_result=0
            log_verbose "Database connection test query executed successfully via direct psql"
        else
            connection_result=$?
            log_verbose "Database connection test failed via direct psql with exit code: $connection_result"
        fi
    fi
    # Handle connection results
    if [[ "$connection_result" -eq 0 ]]; then
        log_verbose "Database connection test query executed successfully"
        log_success "Database connection validated successfully"
        if [[ "$use_docker" == "true" ]]; then
            log_info "Connection established to PostgreSQL container '${docker_container_name}' as user ${AICA_AGENT_DB_USER}"
        else
            log_info "Connection established to ${AICA_AGENT_DB_HOST}:${AICA_AGENT_DB_PORT}/${AICA_AGENT_DB_NAME} as user ${AICA_AGENT_DB_USER}"
        fi
    else
        # Log the connection failure with context
        log_error "Database connection validation failed"
        log_verbose "Connection attempt details:"
        log_verbose "  Host: ${AICA_AGENT_DB_HOST}"
        log_verbose "  Port: ${AICA_AGENT_DB_PORT}"
        log_verbose "  Database: ${AICA_AGENT_DB_NAME}"
        log_verbose "  User: ${AICA_AGENT_DB_USER}"
        log_verbose "  Method: $([ "$use_docker" == "true" ] && echo "Docker container" || echo "Direct psql")"
        log_verbose "  Timeout: ${connection_timeout} seconds"
        
        # Handle different types of connection failures with detailed error messages
        if echo "$connection_output" | grep -qi "timeout\|timed out"; then
            # Timeout occurred
            log_error "Database connection timeout"
            log_error "This indicates the database server is not responding within the expected time"
            log_error "Possible causes and solutions:"
            log_error "  1. Database server is not running - start the PostgreSQL service"
            log_error "  2. Network connectivity issues - check firewall and network settings"
            log_error "  3. Incorrect host/port - verify ${AICA_AGENT_DB_HOST}:${AICA_AGENT_DB_PORT} is correct"
            log_error "  4. Server overload - check database server performance"
            log_error "To troubleshoot:"
            if [[ "$use_docker" == "true" ]]; then
                log_error "  - Check container status: docker ps | grep ${docker_container_name}"
                log_error "  - Check container logs: docker logs ${docker_container_name}"
                log_error "  - Verify PostgreSQL is ready: docker exec ${docker_container_name} pg_isready"
                log_error "  - Check container resource usage: docker stats ${docker_container_name}"
            else
                log_error "  - Test network connectivity: ping ${AICA_AGENT_DB_HOST}"
                log_error "  - Test port accessibility: telnet ${AICA_AGENT_DB_HOST} ${AICA_AGENT_DB_PORT}"
                log_error "  - Check database server logs for errors"
            fi
            exit 2
        else
            # Other connection failures (authentication, network, etc.)
            log_error "Database connection failed with exit code: $connection_result"
            
            # Parse common error patterns and provide specific guidance
            if echo "$connection_output" | grep -qi "authentication failed\|password authentication failed"; then
                log_error "Authentication failed - credentials are incorrect"
                log_error "Please verify the following in your server/.env.local file:"
                log_error "  - AICA_AGENT_DB_USER: ${AICA_AGENT_DB_USER}"
                log_error "  - AICA_AGENT_DB_PASSWORD: [check if password is correct]"
                log_error "Troubleshooting steps:"
                log_error "  1. Verify the user exists in the database"
                log_error "  2. Check if the password is correct"
                log_error "  3. Ensure the user has login privileges"
                log_error "  4. Check pg_hba.conf for authentication method requirements"
            elif echo "$connection_output" | grep -qi "could not connect to server\|connection refused\|no route to host"; then
                log_error "Could not connect to database server"
                log_error "This indicates a network or server availability issue"
                log_error "Please verify:"
                log_error "  - Database server is running and accepting connections"
                log_error "  - Host is correct: ${AICA_AGENT_DB_HOST}"
                log_error "  - Port is correct: ${AICA_AGENT_DB_PORT}"
                log_error "  - Network connectivity is available"
                log_error "  - Firewall allows connections on port ${AICA_AGENT_DB_PORT}"
                
                if [[ "$use_docker" == "true" ]]; then
                    log_error "Docker container troubleshooting:"
                    log_error "  - Check container status: docker ps | grep ${docker_container_name}"
                    log_error "  - Check container logs: docker logs ${docker_container_name}"
                    log_error "  - Verify PostgreSQL is running inside container: docker exec ${docker_container_name} pg_isready"
                    log_error "  - Check container port mapping: docker port ${docker_container_name}"
                else
                    log_error "Troubleshooting commands:"
                    log_error "  - ping ${AICA_AGENT_DB_HOST}"
                    log_error "  - telnet ${AICA_AGENT_DB_HOST} ${AICA_AGENT_DB_PORT}"
                    log_error "  - sudo systemctl status postgresql (on Linux)"
                fi
            elif echo "$connection_output" | grep -qi "database.*does not exist"; then
                log_error "Database '${AICA_AGENT_DB_NAME}' does not exist on the server"
                log_error "Please either:"
                log_error "  1. Create the database: CREATE DATABASE ${AICA_AGENT_DB_NAME};"
                log_error "  2. Verify AICA_AGENT_DB_NAME is correct in server/.env.local file"
                log_error "  3. Check if you're connecting to the right server"
            elif echo "$connection_output" | grep -qi "role.*does not exist\|user.*does not exist"; then
                log_error "Database user '${AICA_AGENT_DB_USER}' does not exist"
                log_error "Please either:"
                log_error "  1. Create the user: CREATE USER ${AICA_AGENT_DB_USER} WITH PASSWORD 'your_password';"
                log_error "  2. Verify AICA_AGENT_DB_USER is correct in server/.env.local file"
                log_error "  3. Grant necessary privileges to the user"
            elif echo "$connection_output" | grep -qi "permission denied\|insufficient privilege"; then
                log_error "User '${AICA_AGENT_DB_USER}' lacks sufficient privileges"
                log_error "The user exists but cannot access the database '${AICA_AGENT_DB_NAME}'"
                log_error "Please grant access: GRANT CONNECT ON DATABASE ${AICA_AGENT_DB_NAME} TO ${AICA_AGENT_DB_USER};"
            elif echo "$connection_output" | grep -qi "ssl"; then
                log_error "SSL connection issue detected"
                log_error "The server may require SSL connections or have SSL configuration issues"
                log_error "Try adding SSL parameters to your connection or check server SSL settings"
            else
                log_error "Connection failed with unrecognized error"
                log_error "Raw error output:"
                # Split error output into lines for better readability
                while IFS= read -r error_line; do
                    [[ -n "$error_line" ]] && log_error "  $error_line"
                done <<< "$connection_output"
                log_error "General troubleshooting steps:"
                log_error "  1. Verify all connection parameters in server/.env.local file"
                if [[ "$use_docker" == "true" ]]; then
                    log_error "  2. Test connection via Docker: docker exec ${docker_container_name} psql -h localhost -p ${AICA_AGENT_DB_PORT} -U ${AICA_AGENT_DB_USER} -d ${AICA_AGENT_DB_NAME} -c 'SELECT 1;'"
                    log_error "  3. Check container logs: docker logs ${docker_container_name}"
                    log_error "  4. Verify PostgreSQL service in container: docker exec ${docker_container_name} pg_isready"
                else
                    log_error "  2. Test connection manually: psql -h ${AICA_AGENT_DB_HOST} -p ${AICA_AGENT_DB_PORT} -U ${AICA_AGENT_DB_USER} -d ${AICA_AGENT_DB_NAME}"
                    log_error "  3. Check database server logs for additional error details"
                    log_error "  4. Ensure PostgreSQL server is running and configured correctly"
                fi
            fi
            
            log_error "Connection validation failed - cannot proceed with migration"
            exit 2
        fi
    fi
    
    log_verbose "Database connection validation completed successfully"
    log_operation_end "Database connection validation" "success"
}

# Validate migration directory
validate_migration_directory() {
    log_operation_start "Migration directory validation"
    log_verbose "Validating migration directory"
    
    # Check if AICA_MIGRATION_DIR parameter is provided
    if [[ -z "${AICA_MIGRATION_DIR:-}" ]]; then
        log_error "Migration directory parameter is missing"
        log_error "AICA_MIGRATION_DIR must be specified in the server/.env.local file"
        log_error "Example: AICA_MIGRATION_DIR=./migrations"
        exit 1
    fi
    
    log_verbose "Migration directory parameter found: $AICA_MIGRATION_DIR"
    
    # Check if migration directory exists
    if [[ ! -d "$AICA_MIGRATION_DIR" ]]; then
        log_error "Migration directory does not exist: $AICA_MIGRATION_DIR"
        log_error "Please ensure the migration directory exists and contains migration files"
        log_error "Create the directory with: mkdir -p $AICA_MIGRATION_DIR"
        exit 1
    fi
    
    log_verbose "Migration directory exists: $AICA_MIGRATION_DIR"
    
    # Check if directory is accessible (readable)
    if [[ ! -r "$AICA_MIGRATION_DIR" ]]; then
        log_error "Migration directory is not accessible: $AICA_MIGRATION_DIR"
        log_error "Please check directory permissions"
        log_error "Fix permissions with: chmod 755 $AICA_MIGRATION_DIR"
        exit 1
    fi
    
    log_verbose "Migration directory is accessible"
    
    # Check if migration directory contains migration files
    # Look for SQL files that follow Flyway naming convention (V*.sql)
    local migration_files=()
    local sql_files=()
    
    # Find all .sql files in the directory
    while IFS= read -r -d '' file; do
        sql_files+=("$file")
    done < <(find "$AICA_MIGRATION_DIR" -maxdepth 1 -name "*.sql" -type f -print0 2>/dev/null)
    
    # Check if any SQL files were found
    if [[ ${#sql_files[@]} -eq 0 ]]; then
        log_error "Migration directory is empty: $AICA_MIGRATION_DIR"
        log_error "No SQL migration files found in the directory"
        log_error "Migration files should follow Flyway naming convention:"
        log_error "  - V1__Initial_migration.sql"
        log_error "  - V2__Add_users_table.sql"
        log_error "  - V3__Update_schema.sql"
        exit 1
    fi
    
    log_verbose "Found ${#sql_files[@]} SQL file(s) in migration directory"
    
    # Validate that at least some files follow Flyway naming convention
    for file in "${sql_files[@]}"; do
        local filename=$(basename "$file")
        # Check if filename follows Flyway versioned migration pattern (V*.sql)
        if [[ "$filename" =~ ^V[0-9]+.*\.sql$ ]]; then
            migration_files+=("$filename")
        fi
    done
    
    # Log all found SQL files for debugging
    log_verbose "SQL files found:"
    for file in "${sql_files[@]}"; do
        local filename=$(basename "$file")
        log_verbose "  - $filename"
    done
    
    # Check if any valid Flyway migration files were found
    if [[ ${#migration_files[@]} -eq 0 ]]; then
        log_error "No valid Flyway migration files found in: $AICA_MIGRATION_DIR"
        log_error "Found ${#sql_files[@]} SQL file(s), but none follow Flyway naming convention"
        log_error "Flyway migration files must start with 'V' followed by version number:"
        log_error "  Valid examples:"
        log_error "    - V1__Initial_migration.sql"
        log_error "    - V2__Add_users_table.sql"
        log_error "    - V10__Update_schema.sql"
        log_error "  Invalid examples:"
        log_error "    - migration.sql (missing version)"
        log_error "    - 1_migration.sql (missing 'V' prefix)"
        log_error "    - v1_migration.sql (lowercase 'v')"
        exit 1
    fi
    
    log_info "Migration directory validation successful"
    log_info "Found ${#migration_files[@]} valid Flyway migration file(s):"
    for file in "${migration_files[@]}"; do
        log_info "  - $file"
    done
    
    log_verbose "Migration directory validation completed successfully"
    log_operation_end "Migration directory validation" "success"
}

# Validate Flyway dependency
validate_flyway_dependency() {
    log_operation_start "Flyway dependency validation"
    log_verbose "Validating Flyway dependency"
    
    # Check if Flyway is installed and accessible in PATH
    if ! command -v flyway >/dev/null 2>&1; then
        log_error "Flyway is not installed or not accessible in PATH"
        log_error "Flyway CLI is required to execute database migrations"
        log_error ""
        log_error "Installation instructions:"
        log_error "  On macOS:"
        log_error "    brew install flyway"
        log_error ""
        log_error "  On Linux (Ubuntu/Debian):"
        log_error "    # Download and install Flyway"
        log_error "    wget -qO- https://repo1.maven.org/maven2/org/flywaydb/flyway-commandline/9.22.3/flyway-commandline-9.22.3-linux-x64.tar.gz | tar xvz"
        log_error "    sudo mv flyway-9.22.3 /opt/flyway"
        log_error "    sudo ln -s /opt/flyway/flyway /usr/local/bin/flyway"
        log_error ""
        log_error "  Manual installation:"
        log_error "    1. Download Flyway from https://flywaydb.org/download/"
        log_error "    2. Extract the archive"
        log_error "    3. Add the flyway/bin directory to your PATH"
        log_error ""
        log_error "After installation, verify with: flyway --version"
        exit 4
    fi
    
    log_verbose "Flyway command found in PATH"
    
    # Get Flyway version for logging and compatibility validation
    local flyway_version_output
    if flyway_version_output=$(flyway --version 2>&1); then
        log_verbose "Flyway version check successful"
        
        # Extract version number from output
        local flyway_version
        if flyway_version=$(echo "$flyway_version_output" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1); then
            log_info "Flyway version detected: $flyway_version"
            
            # Basic version compatibility check (require version 7.0.0 or higher)
            local major_version
            major_version=$(echo "$flyway_version" | cut -d. -f1)
            
            if [[ "$major_version" -lt 7 ]]; then
                log_error "Flyway version $flyway_version is not supported"
                log_error "This script requires Flyway version 7.0.0 or higher"
                log_error "Please upgrade Flyway to a supported version"
                log_error "Current version: $flyway_version"
                log_error "Minimum required: 7.0.0"
                exit 4
            fi
            
            log_verbose "Flyway version compatibility check passed"
        else
            log_verbose "Could not parse Flyway version from output: $flyway_version_output"
            log_info "Flyway is available but version could not be determined"
            log_verbose "Proceeding with migration execution"
        fi
    else
        log_error "Failed to get Flyway version information"
        log_error "Flyway command is available but may not be functioning correctly"
        log_error "Please verify Flyway installation with: flyway --version"
        exit 4
    fi
    
    log_success "Flyway dependency validation completed successfully"
    log_operation_end "Flyway dependency validation" "success"
}

# Ensure the vector extension exists directly in the database when --clean is requested
create_vector_extension_if_clean_mode() {
    if [[ "${CLEAN_MODE}" != "true" ]]; then
        log_verbose "Clean mode not enabled; skipping vector extension creation"
        return 0
    fi

    log_info "Ensuring vector extension exists before Flyway migrations"
    local sql_statement="CREATE EXTENSION IF NOT EXISTS vector;"
    local attempted_psql=false

    if command -v psql >/dev/null 2>&1; then
        attempted_psql=true
        log_verbose "Executing vector extension SQL via local psql"
        local psql_conn="postgresql://${AICA_AGENT_DB_USER}:${AICA_AGENT_DB_PASSWORD}@${AICA_AGENT_DB_HOST}:${AICA_AGENT_DB_PORT}/${AICA_AGENT_DB_NAME}"
        local output
        if output=$(PGPASSWORD="${AICA_AGENT_DB_PASSWORD}" psql "${psql_conn}" -c "${sql_statement}" 2>&1); then
            log_success "Vector extension ensured via psql"
            log_verbose "psql output:"
            while IFS= read -r line; do [[ -n "$line" ]] && log_verbose "  $line"; done <<< "$output"
            return 0
        else
            log_warn "psql failed to execute vector extension SQL; will try other available options"
            log_verbose "psql error output:"
            while IFS= read -r line; do [[ -n "$line" ]] && log_verbose "  $line"; done <<< "$output"
        fi
    fi

    if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -q "^${AICA_AGENT_DB_HOST}$"; then
        log_verbose "Executing vector extension SQL inside Docker container ${AICA_AGENT_DB_HOST}"
        local output
        if output=$(docker exec -i "${AICA_AGENT_DB_HOST}" psql -U "${AICA_AGENT_DB_USER}" -d "${AICA_AGENT_DB_NAME}" -p "${AICA_AGENT_DB_PORT}" -c "${sql_statement}" 2>&1); then
            log_success "Vector extension ensured via docker exec"
            log_verbose "docker exec output:"
            while IFS= read -r line; do [[ -n "$line" ]] && log_verbose "  $line"; done <<< "$output"
            return 0
        else
            log_warn "docker exec failed to execute vector extension SQL"
            log_verbose "docker exec error output:"
            while IFS= read -r line; do [[ -n "$line" ]] && log_verbose "  $line"; done <<< "$output"
        fi
    fi

    if [[ "${attempted_psql}" == "false" ]]; then
        log_error "Cannot create vector extension: neither psql nor docker + container ${AICA_AGENT_DB_HOST} is available"
    else
        log_error "Failed to ensure vector extension via the available client(s)"
    fi
    return 1
}

# If requested, perform Flyway clean before migrate
apply_clean_if_requested() {
    if [[ "${CLEAN_MODE}" != "true" ]]; then
        log_verbose "Clean mode not enabled; skipping Flyway clean"
        return 0
    fi

    log_warn "CLEAN MODE ENABLED: Flyway clean will delete all data in the target database"
    log_info "Executing Flyway clean"

    if [[ -z "${DB_CONNECTION_STRING:-}" ]] || [[ -z "${AICA_AGENT_DB_USER:-}" ]] || [[ -z "${AICA_AGENT_DB_PASSWORD:-}" ]] || [[ -z "${FLYWAY_LOCATIONS:-}" ]]; then
        log_error "Missing Flyway configuration required to run clean"
        return 1
    fi

    local clean_cmd=(
        "flyway"
        "-url=${DB_CONNECTION_STRING}"
        "-user=${AICA_AGENT_DB_USER}"
        "-password=${AICA_AGENT_DB_PASSWORD}"
        "-locations=${FLYWAY_LOCATIONS}"
        "-cleanDisabled=false"
        "clean"
    )

    log_verbose "Running: flyway clean (password redacted)"
    local out
    if out=$("${clean_cmd[@]}" 2>&1); then
        log_success "Flyway clean completed successfully"
        log_verbose "Flyway clean output:"
        while IFS= read -r line; do [[ -n "$line" ]] && log_verbose "  $line"; done <<< "$out"
        return 0
    else
        log_error "Flyway clean failed"
        log_error "Output:"
        while IFS= read -r line; do [[ -n "$line" ]] && log_error "  $line"; done <<< "$out"
        return 1
    fi
}

# Load position vectors SQL file into the database if requested
load_position_vectors() {
    if [[ -z "${POSITION_VECTORS_FILE:-}" ]]; then
        log_verbose "No position vectors file specified; skipping load step"
        return 0
    fi

    if [[ ! -f "${POSITION_VECTORS_FILE}" ]]; then
        log_error "Position vectors file not found: ${POSITION_VECTORS_FILE}"
        return 1
    fi

    log_info "Loading position vectors from: ${POSITION_VECTORS_FILE}"

    # Prefer local psql if available
    if command -v psql >/dev/null 2>&1; then
        log_verbose "Using local psql to load SQL file"
        local psql_conn="postgresql://${AICA_AGENT_DB_USER}:${AICA_AGENT_DB_PASSWORD}@${AICA_AGENT_DB_HOST}:${AICA_AGENT_DB_PORT}/${AICA_AGENT_DB_NAME}"
        if PGPASSWORD="${AICA_AGENT_DB_PASSWORD}" psql "${psql_conn}" -f "${POSITION_VECTORS_FILE}" 2>&1 | while IFS= read -r line; do [[ -n "$line" ]] && log_verbose "  $line"; done; then
            log_success "Position vectors loaded successfully via psql"
            return 0
        else
            log_error "Failed to load position vectors via psql"
            return 1
        fi
    fi

    # Fallback to docker exec if DB is containerized and docker available
    if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -q "^${AICA_AGENT_DB_HOST}$"; then
        log_verbose "Using docker exec to load SQL into container: ${AICA_AGENT_DB_HOST}"
        if docker exec -i "${AICA_AGENT_DB_HOST}" psql -U "${AICA_AGENT_DB_USER}" -d "${AICA_AGENT_DB_NAME}" -p "${AICA_AGENT_DB_PORT}" < "${POSITION_VECTORS_FILE}" 2>&1 | while IFS= read -r line; do [[ -n "$line" ]] && log_verbose "  $line"; done; then
            log_success "Position vectors loaded successfully into container ${AICA_AGENT_DB_HOST}"
            return 0
        else
            log_error "Failed to load position vectors into container ${AICA_AGENT_DB_HOST}"
            return 1
        fi
    fi

    log_error "Cannot load position vectors: neither psql nor docker (with running container ${AICA_AGENT_DB_HOST}) available"
    return 1
}

# Execute Flyway migration
execute_flyway_migration() {
    log_operation_start "Flyway migration execution"
    log_verbose "Preparing Flyway migration execution"
    
    # Validate that all required configuration is available
    if [[ -z "${DB_CONNECTION_STRING:-}" ]] || [[ -z "${FLYWAY_LOCATIONS:-}" ]] || [[ -z "${AICA_AGENT_DB_USER:-}" ]] || [[ -z "${AICA_AGENT_DB_PASSWORD:-}" ]]; then
        log_error "Required configuration missing for Flyway execution"
        log_error "Ensure database connection and migration directory validation completed successfully"
        exit 3
    fi
    
    log_info "Executing Flyway migration"
    log_info "Database: ${AICA_AGENT_DB_HOST}:${AICA_AGENT_DB_PORT}/${AICA_AGENT_DB_NAME}"
    log_info "Migration directory: ${AICA_MIGRATION_DIR}"
    log_info "User: ${AICA_AGENT_DB_USER}"
    
    # Construct Flyway command with database parameters and migration directory
    local flyway_cmd=(
        "flyway"
        "-url=${DB_CONNECTION_STRING}"
        "-user=${AICA_AGENT_DB_USER}"
        "-password=${AICA_AGENT_DB_PASSWORD}"
        "-locations=${FLYWAY_LOCATIONS}"
        "migrate"
    )
    
    log_verbose "Flyway command constructed:"
    log_verbose "  flyway \\"
    log_verbose "    -url=${DB_CONNECTION_STRING} \\"
    log_verbose "    -user=${AICA_AGENT_DB_USER} \\"
    log_verbose "    -password=[REDACTED] \\"
    log_verbose "    -locations=${FLYWAY_LOCATIONS} \\"
    log_verbose "    migrate"
    
    # Execute Flyway migrate command and capture output
    local flyway_output
    local flyway_exit_code
    local retry_with_baseline=false
    
    log_verbose "Starting Flyway migration execution"
    
    # Execute Flyway command and capture both stdout and stderr
    if flyway_output=$("${flyway_cmd[@]}" 2>&1); then
        flyway_exit_code=0
        log_verbose "Flyway command executed successfully"
    else
        flyway_exit_code=$?
        log_verbose "Flyway command failed with exit code: $flyway_exit_code"
        
        # Check if the error is due to non-empty schema without history table
        if echo "$flyway_output" | grep -qi "Found non-empty schema" && echo "$flyway_output" | grep -qi "no schema history table" && echo "$flyway_output" | grep -qi "baselineOnMigrate"; then
            log_warn "Detected non-empty schema without Flyway history table"
            log_info "This occurs when the database schema exists but Flyway hasn't been used before"
            log_info "Retrying migration with baselineOnMigrate=true to initialize schema history"
            retry_with_baseline=true
        fi
    fi
    
    # Retry with baselineOnMigrate if needed
    if [[ "$retry_with_baseline" == "true" ]]; then
        log_verbose "Constructing Flyway command with baselineOnMigrate=true"
        
        # Construct Flyway command with baselineOnMigrate option
        local flyway_baseline_cmd=(
            "flyway"
            "-url=${DB_CONNECTION_STRING}"
            "-user=${AICA_AGENT_DB_USER}"
            "-password=${AICA_AGENT_DB_PASSWORD}"
            "-locations=${FLYWAY_LOCATIONS}"
            "-baselineOnMigrate=true"
            "migrate"
        )
        
        log_verbose "Flyway baseline command constructed:"
        log_verbose "  flyway \\"
        log_verbose "    -url=${DB_CONNECTION_STRING} \\"
        log_verbose "    -user=${AICA_AGENT_DB_USER} \\"
        log_verbose "    -password=[REDACTED] \\"
        log_verbose "    -locations=${FLYWAY_LOCATIONS} \\"
        log_verbose "    -baselineOnMigrate=true \\"
        log_verbose "    migrate"
        
        log_info "Executing Flyway migration with baseline initialization"
        
        # Execute Flyway command with baseline and capture both stdout and stderr
        if flyway_output=$("${flyway_baseline_cmd[@]}" 2>&1); then
            flyway_exit_code=0
            log_verbose "Flyway baseline command executed successfully"
            log_success "Migration completed successfully with schema history initialization"
        else
            flyway_exit_code=$?
            log_verbose "Flyway baseline command failed with exit code: $flyway_exit_code"
        fi
    fi
    
    # Store output and exit code for result handling
    FLYWAY_OUTPUT="$flyway_output"
    FLYWAY_EXIT_CODE="$flyway_exit_code"
    
    log_verbose "Flyway execution completed with exit code: $flyway_exit_code"
    log_verbose "Captured output length: ${#flyway_output} characters"
    
    if [[ "$flyway_exit_code" -eq 0 ]]; then
        log_operation_end "Flyway migration execution" "success"
    else
        log_operation_end "Flyway migration execution" "failed"
    fi
    
    return "$flyway_exit_code"
}

# Handle migration results
handle_migration_results() {
    log_verbose "Processing migration results"
    
    # Check if Flyway execution variables are available
    if [[ -z "${FLYWAY_OUTPUT:-}" ]] || [[ -z "${FLYWAY_EXIT_CODE:-}" ]]; then
        log_error "Migration result data is not available"
        log_error "Flyway execution may not have been performed"
        exit 3
    fi
    
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    if [[ "$FLYWAY_EXIT_CODE" -eq 0 ]]; then
        # Handle successful migration
        log_success "Database migration completed successfully"
        log_info "Migration execution finished at: $timestamp"
        
        # Parse and log migration summary from Flyway output
        log_verbose "Parsing Flyway output for migration summary"
        
        # Extract migration information from Flyway output
        local migrations_applied=0
        local migration_details=()
        
        # Look for migration success patterns in output
        while IFS= read -r line; do
            # Count successful migrations (lines containing "Migrating schema" or "Successfully applied")
            if echo "$line" | grep -qi "migrating.*to version\|successfully applied.*migration"; then
                ((migrations_applied++))
                # Extract migration details for summary
                if echo "$line" | grep -qi "migrating.*to version"; then
                    local migration_info=$(echo "$line" | sed 's/.*Migrating.*to version \([^:]*\): \(.*\)/Version \1: \2/')
                    migration_details+=("$migration_info")
                fi
            fi
        done <<< "$FLYWAY_OUTPUT"
        
        # Provide summary of migration actions performed
        if [[ $migrations_applied -gt 0 ]]; then
            log_info "Migration summary:"
            log_info "  - Applied $migrations_applied migration(s)"
            
            # Log individual migration details if available
            if [[ ${#migration_details[@]} -gt 0 ]]; then
                log_info "  - Migration details:"
                for detail in "${migration_details[@]}"; do
                    log_info "    * $detail"
                done
            fi
        else
            # Check if schema is already up to date
            if echo "$FLYWAY_OUTPUT" | grep -qi "schema.*is up to date\|no migration necessary"; then
                log_info "Database schema is already up to date"
                log_info "No migrations were necessary"
            else
                log_info "Migration completed but no new migrations were applied"
            fi
        fi
        
        # Log additional Flyway output in verbose mode
        if [[ "$VERBOSE" == "true" ]]; then
            log_verbose "Complete Flyway output:"
            while IFS= read -r line; do
                [[ -n "$line" ]] && log_verbose "  $line"
            done <<< "$FLYWAY_OUTPUT"
        fi
        
        log_success "Migration process completed successfully"

        # If a position vectors SQL file was specified, attempt to load it now
        if [[ -n "${POSITION_VECTORS_FILE:-}" ]]; then
            log_info "Position vectors file specified; attempting to load data: ${POSITION_VECTORS_FILE}"
            if ! load_position_vectors; then
                log_error "Failed to load position vectors file: ${POSITION_VECTORS_FILE}"
                exit 3
            fi
        fi

        exit 0
        
    else
        # Handle failed migration
        log_error "Database migration failed"
        log_error "Migration execution failed at: $timestamp"
        log_error "Flyway exit code: $FLYWAY_EXIT_CODE"
        
        # Parse error details from Flyway output
        log_verbose "Parsing Flyway output for error details"
        
        # Extract error information
        local error_lines=()
        local in_error_section=false
        
        while IFS= read -r line; do
            # Look for error indicators
            if echo "$line" | grep -qi "error\|exception\|failed\|unable to\|could not"; then
                in_error_section=true
                error_lines+=("$line")
            elif [[ "$in_error_section" == "true" ]] && [[ -n "$line" ]]; then
                # Continue collecting error context
                error_lines+=("$line")
            elif [[ "$in_error_section" == "true" ]] && [[ -z "$line" ]]; then
                # Empty line might indicate end of error section
                in_error_section=false
            fi
        done <<< "$FLYWAY_OUTPUT"
        
        # Display error details
        if [[ ${#error_lines[@]} -gt 0 ]]; then
            log_error "Migration error details:"
            for error_line in "${error_lines[@]}"; do
                log_error "  $error_line"
            done
        else
            log_error "No specific error details found in Flyway output"
        fi
        
        # Provide common troubleshooting guidance
        log_error ""
        log_error "Common migration failure causes and solutions:"
        log_error "  1. SQL syntax errors in migration files"
        log_error "     - Review migration files for syntax issues"
        log_error "     - Test SQL statements manually in database client"
        log_error "  2. Database permission issues"
        log_error "     - Ensure user has CREATE, ALTER, DROP privileges"
        log_error "     - Check database user permissions"
        log_error "  3. Migration conflicts or version issues"
        log_error "     - Check if migrations are out of order"
        log_error "     - Verify migration file naming convention"
        log_error "  4. Database connectivity issues during migration"
        log_error "     - Check database server stability"
        log_error "     - Verify network connectivity"
        
        # Log complete Flyway output for debugging
        log_error ""
        log_error "Complete Flyway output for debugging:"
        while IFS= read -r line; do
            log_error "  $line"
        done <<< "$FLYWAY_OUTPUT"
        
        log_error "Migration process failed - check error details above"
        exit 3
    fi
}

# Main execution function with comprehensive error handling and cleanup
main() {
    local script_start_time=$(date '+%Y-%m-%d %H:%M:%S.%3N')
    local script_exit_code=0
    
    # Set up error handling and cleanup
    trap 'handle_interrupt' INT TERM
    
    log_info "Starting Flyway Migration Script"
    log_info "Script version: 1.0.0"
    log_info "Execution started at: $script_start_time"
    log_verbose "Script directory: $SCRIPT_DIR"
    log_verbose "Process ID: $$"
    log_verbose "User: $(whoami)"
    log_verbose "Working directory: $(pwd)"
    
    # Validate script prerequisites
    log_operation_start "Script prerequisites validation"
    validate_script_prerequisites
    log_operation_end "Script prerequisites validation" "success"
    
    # Execute main workflow with error handling
    execute_migration_workflow || script_exit_code=$?
    
    # Generate final summary
    generate_execution_summary "$script_start_time" "$script_exit_code"
    
    return "$script_exit_code"
}

# Execute the main migration workflow
execute_migration_workflow() {
    local workflow_exit_code=0
    
    log_info "Executing migration workflow"
    
    # Load environment configuration
    load_env_config || return 1
    
    # Validate parameters and construct configuration
    validate_and_construct_config || return 1
    
    # Validate Docker container if using pgvector
    validate_docker_container || return 2
    
    # Validate database connection
    validate_database_connection || return 2
    
    # Validate migration directory
    validate_migration_directory || return 1
    
    # Validate Flyway dependency
    validate_flyway_dependency || return 4

    # If requested, perform Flyway clean before migrate
    apply_clean_if_requested || return 3

    # If clean mode is enabled, create temporary migration file for vector extension
    create_vector_extension_if_clean_mode || return 1

    # Execute Flyway migration
    execute_flyway_migration || workflow_exit_code=$?
    
    # Handle migration results
    handle_migration_results || return 3
    
    return "$workflow_exit_code"
}

# Validate script prerequisites
validate_script_prerequisites() {
    log_verbose "Validating script prerequisites"
    
    # Check bash version (recommend 4.0+, but allow 3.2+ with warning)
    local bash_major_version="${BASH_VERSION%%.*}"
    if [[ "$bash_major_version" -lt 3 ]]; then
        log_error "Bash version 3.2 or higher is required"
        log_error "Current version: $BASH_VERSION"
        log_error "Please upgrade bash to continue"
        exit 1
    elif [[ "$bash_major_version" -eq 3 ]]; then
        local bash_minor_version="${BASH_VERSION#*.}"
        bash_minor_version="${bash_minor_version%%.*}"
        if [[ "$bash_minor_version" -lt 2 ]]; then
            log_error "Bash version 3.2 or higher is required"
            log_error "Current version: $BASH_VERSION"
            log_error "Please upgrade bash to continue"
            exit 1
        fi
        log_warn "Using bash version $BASH_VERSION (older than recommended 4.0+)"
        log_warn "Some advanced features may not be available"
    fi
    log_verbose "Bash version check passed: $BASH_VERSION"
    
    # Check required commands
    local required_commands=("date" "grep" "awk" "sed" "find" "dirname" "basename")
    local missing_commands=()
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_commands+=("$cmd")
        fi
    done
    
    if [[ ${#missing_commands[@]} -gt 0 ]]; then
        log_error "Required commands are missing:"
        for cmd in "${missing_commands[@]}"; do
            log_error "  - $cmd"
        done
        log_error "Please install missing commands to continue"
        exit 1
    fi
    log_verbose "All required commands are available"
    
    # Check script permissions
    if [[ ! -r "$0" ]]; then
        log_error "Script is not readable: $0"
        log_error "Please check script permissions"
        exit 1
    fi
    log_verbose "Script permissions check passed"
    
    log_verbose "Script prerequisites validation completed"
}

# Handle script interruption (Ctrl+C, SIGTERM)
handle_interrupt() {
    local signal_name="$1"
    log_warn "Script interrupted by signal: ${signal_name:-UNKNOWN}"
    log_info "Performing cleanup before exit"
    cleanup_and_exit 130  # Standard exit code for script interrupted by Ctrl+C
}

# Cleanup and exit with proper status
cleanup_and_exit() {
    local exit_code="${1:-0}"
    
    log_verbose "Performing cleanup operations"
    
    # Clear sensitive environment variables
    unset AICA_AGENT_DB_PASSWORD 2>/dev/null || true
    log_verbose "Sensitive environment variables cleared"
    
    # Log final exit status
    if [[ "$exit_code" -eq 0 ]]; then
        log_success "Script completed successfully"
    else
        log_error "Script completed with errors (exit code: $exit_code)"
    fi
    
    log_verbose "Cleanup completed"
    exit "$exit_code"
}

# Generate comprehensive execution summary
generate_execution_summary() {
    local start_time="$1"
    local exit_code="$2"
    local end_time=$(date '+%Y-%m-%d %H:%M:%S.%3N')
    
    log_info "=== EXECUTION SUMMARY ==="
    log_info "Script: Flyway Migration Script v1.0.0"
    log_info "Start time: $start_time"
    log_info "End time: $end_time"
    
    # Calculate execution duration
    if command -v python3 >/dev/null 2>&1; then
        local duration=$(python3 -c "
from datetime import datetime
start = datetime.strptime('$start_time', '%Y-%m-%d %H:%M:%S.%f')
end = datetime.strptime('$end_time', '%Y-%m-%d %H:%M:%S.%f')
duration = end - start
print(f'{duration.total_seconds():.3f}')
" 2>/dev/null || echo "unknown")
        log_info "Duration: ${duration} seconds"
    else
        log_info "Duration: calculation unavailable"
    fi
    
    # Summary based on exit code
    case "$exit_code" in
        0)
            log_success "Status: SUCCESS - Migration completed successfully"
            log_info "All database migrations have been applied"
            ;;
        1)
            log_error "Status: CONFIGURATION ERROR - Check server/.env.local file and parameters"
            log_error "Review configuration and try again"
            ;;
        2)
            log_error "Status: DATABASE CONNECTION ERROR - Cannot connect to database"
            log_error "Verify database server is running and credentials are correct"
            ;;
        3)
            log_error "Status: MIGRATION ERROR - Flyway execution failed"
            log_error "Check migration files and database state"
            ;;
        4)
            log_error "Status: DEPENDENCY ERROR - Flyway not available"
            log_error "Install Flyway and ensure it's in PATH"
            ;;
        130)
            log_warn "Status: INTERRUPTED - Script was interrupted by user"
            ;;
        *)
            log_error "Status: UNKNOWN ERROR - Unexpected exit code: $exit_code"
            ;;
    esac
    
    log_info "=========================="
}

# Script entry point with comprehensive error handling
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Parse command line arguments
    parse_arguments "$@"
    
    # Execute main function and capture exit code
    main
    script_exit_code=$?
    
    # Exit with the proper code
    exit "$script_exit_code"
fi

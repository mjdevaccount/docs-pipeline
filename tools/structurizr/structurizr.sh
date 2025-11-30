#!/bin/bash
# Structurizr CLI Wrapper for Linux/macOS
# Provides easy access to Structurizr CLI via Docker

set -e

# Configuration
DOCKER_IMAGE="structurizr/cli:latest"
WORKSPACE_DIR="$(pwd)"

# Colors (optional)
if command -v tput >/dev/null 2>&1; then
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4)
    RESET=$(tput sgr0)
else
    RED=""
    GREEN=""
    YELLOW=""
    BLUE=""
    RESET=""
fi

# Check if Docker is available
if ! command -v docker >/dev/null 2>&1; then
    echo "${RED}[ERROR]${RESET} Docker is not installed or not in PATH"
    echo "Please install Docker: https://www.docker.com/get-started"
    exit 1
fi

# Check if Docker is running
if ! docker ps >/dev/null 2>&1; then
    echo "${RED}[ERROR]${RESET} Docker is not running"
    echo "Please start Docker"
    exit 1
fi

# Parse command
COMMAND="${1:-}"

if [ -z "$COMMAND" ]; then
    echo "Structurizr CLI Wrapper"
    echo ""
    echo "Usage:"
    echo "  $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  export      Export diagrams from DSL workspace"
    echo "  validate    Validate DSL workspace syntax"
    echo "  serve       Start Structurizr Lite server"
    echo "  check       Check Docker and Structurizr CLI availability"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 export --workspace docs/Architecture.dsl --format mermaid --output docs/"
    echo "  $0 validate --workspace docs/Architecture.dsl"
    echo "  $0 serve --workspace docs/Architecture.dsl"
    echo "  $0 check"
    echo ""
    exit 0
fi

# Handle check command
if [ "$COMMAND" = "check" ]; then
    echo "${BLUE}[INFO]${RESET} Checking Docker..."
    docker --version
    
    echo "${BLUE}[INFO]${RESET} Checking Docker is running..."
    if ! docker ps >/dev/null 2>&1; then
        echo "${RED}[ERROR]${RESET} Docker is not running"
        exit 1
    fi
    
    echo "${BLUE}[INFO]${RESET} Checking Structurizr CLI image..."
    if ! docker images structurizr/cli >/dev/null 2>&1; then
        echo "${YELLOW}[WARN]${RESET} Structurizr CLI image not found, pulling..."
        docker pull "$DOCKER_IMAGE"
    fi
    
    echo "${GREEN}[OK]${RESET} All dependencies available"
    exit 0
fi

# Handle help command
if [ "$COMMAND" = "help" ]; then
    cat <<EOF
Structurizr CLI Wrapper - Help

This wrapper provides easy access to Structurizr CLI via Docker.

Commands:

  EXPORT
  -----
  Export diagrams from DSL workspace to various formats

  Usage:
    $0 export --workspace <file.dsl> --format <format> --output <dir>

  Formats: mermaid, plantuml, png, svg, html, json

  Example:
    $0 export --workspace docs/Architecture.dsl --format mermaid --output docs/

  VALIDATE
  -------
  Validate DSL workspace syntax

  Usage:
    $0 validate --workspace <file.dsl>

  Example:
    $0 validate --workspace docs/Architecture.dsl

  SERVE
  -----
  Start Structurizr Lite interactive server

  Usage:
    $0 serve --workspace <file.dsl>

  Example:
    $0 serve --workspace docs/Architecture.dsl

  Access at http://localhost:8080

  CHECK
  -----
  Check Docker and Structurizr CLI availability

  Usage:
    $0 check
EOF
    exit 0
fi

# Pull image if not present (for export/validate/serve)
if [ "$COMMAND" = "export" ] || [ "$COMMAND" = "validate" ] || [ "$COMMAND" = "serve" ]; then
    if ! docker images structurizr/cli >/dev/null 2>&1; then
        echo "${BLUE}[INFO]${RESET} Pulling Structurizr CLI image..."
        docker pull "$DOCKER_IMAGE"
    fi
fi

# Handle serve command (needs port mapping and Lite image)
if [ "$COMMAND" = "serve" ]; then
    DOCKER_CMD="docker run --rm -it -p 8080:8080"
    DOCKER_CMD="$DOCKER_CMD -v \"$WORKSPACE_DIR\":/usr/local/structurizr/workspace"
    DOCKER_CMD="$DOCKER_CMD -w /usr/local/structurizr/workspace"
    DOCKER_CMD="$DOCKER_CMD structurizr/lite"
    
    # Remove --workspace from arguments (Lite uses workspace directory)
    shift
    ARGS="$*"
    ARGS="${ARGS//--workspace /}"
    
    eval "$DOCKER_CMD $ARGS"
    exit $?
fi

# For export and validate, build Docker command
DOCKER_CMD="docker run --rm"
DOCKER_CMD="$DOCKER_CMD -v \"$WORKSPACE_DIR\":/workspace"
DOCKER_CMD="$DOCKER_CMD -w /workspace"
DOCKER_CMD="$DOCKER_CMD $DOCKER_IMAGE"

# Pass all remaining arguments
shift
ARGS="$*"

eval "$DOCKER_CMD $COMMAND $ARGS"
exit $?


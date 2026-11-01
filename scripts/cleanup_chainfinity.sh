#!/bin/bash
# ChainFinity Cleanup Script
# This script removes generated files, logs, and temporary directories to clean the project environment.

# --- Configuration ---
# Exit immediately if a command exits with a non-zero status, treat unset variables as an error, and fail if any command in a pipeline fails
set -euo pipefail

# Color definitions
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default Configuration
PROJECT_DIR="$(pwd)"

# --- Utility Functions ---

# Logging function
log() {
  local level="$1"
  local message="$2"
  local timestamp
  timestamp=$(date +"%Y-%m-%d %H:%M:%S")

  case $level in
    "INFO")
      echo -e "${BLUE}[${timestamp}] [${level}] ${message}${NC}"
      ;;
    "WARNING")
      echo -e "${YELLOW}[${timestamp}] [${level}] ${message}${NC}"
      ;;
    "ERROR")
      echo -e "${RED}[${timestamp}] [${level}] ${message}${NC}"
      ;;
    "SUCCESS")
      echo -e "${GREEN}[${timestamp}] [${level}] ${message}${NC}"
      ;;
  esac
}

# Function to remove files/directories safely
safe_remove() {
  local target="$1"
  if [ -e "$target" ]; then
    log "INFO" "Removing $target..."
    rm -rf "$target"
    log "SUCCESS" "Removed $target"
  else
    log "WARNING" "$target not found. Skipping removal."
  fi
}

# --- Main Execution ---

main() {
  log "INFO" "Starting ChainFinity environment cleanup..."

  # Change to project directory
  cd "$PROJECT_DIR" || { log "ERROR" "Failed to change to project directory: $PROJECT_DIR"; exit 1; }

  # 1. Stop and remove Docker containers
  log "INFO" "Stopping and removing Docker containers..."
  # Resolve the Compose command (v2 plugin preferred, v1 fallback).
  COMPOSE=""
  if docker compose version &> /dev/null; then
    COMPOSE="docker compose"
  elif command -v docker-compose &> /dev/null; then
    COMPOSE="docker-compose"
  fi
  if [ -n "$COMPOSE" ]; then
    if [ -f "infrastructure/docker-compose.yml" ]; then
      $COMPOSE -f infrastructure/docker-compose.yml down -v --remove-orphans \
        || log "WARNING" "Failed to stop containers."
    fi
    log "SUCCESS" "Docker containers stopped and removed."
  else
    log "WARNING" "Docker Compose not found. Skipping container cleanup."
  fi

  # 2. Remove generated directories and files
  log "INFO" "Removing generated files and directories..."

  # Logs, reports, backups
  safe_remove "logs"
  safe_remove "test-reports"
  safe_remove "backups"
  safe_remove "deployments"

  # Python virtual environment
  safe_remove "venv"
  safe_remove ".coverage"
  safe_remove "htmlcov"

  # Node.js dependencies and build artifacts
  safe_remove "code/blockchain/node_modules"
  safe_remove "web-frontend/node_modules"
  safe_remove "mobile-frontend/node_modules"
  safe_remove "web-frontend/build"
  safe_remove "web-frontend/dist"
  safe_remove "mobile-frontend/build"
  safe_remove "mobile-frontend/dist"
  safe_remove "node_modules" # Root node_modules

  # Configuration files created by scripts
  safe_remove ".env"
  safe_remove "monitor_config.json"
  safe_remove "activate_env.sh"

  # Remove backup files
  find . -type f -name "*.bak.*" -delete
  log "SUCCESS" "Removed backup files."

  log "$SUCCESS" "ChainFinity environment cleanup completed successfully!"
  log "$INFO" "The project directory remains, but generated files have been removed."
}

# Run main function
main

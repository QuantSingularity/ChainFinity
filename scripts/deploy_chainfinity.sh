#!/bin/bash
# ChainFinity Deployment Automation Script
# This script automates the deployment process for all components of the ChainFinity platform

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
LOG_DIR="$PROJECT_DIR/logs"
ENV_FILE="$PROJECT_DIR/.env"
ENVIRONMENT="development"
BACKUP_DIR="$PROJECT_DIR/backups/$(date +%Y%m%d_%H%M%S)"
DRY_RUN=false
DEPLOY_COMPONENT="all"

# --- Utility Functions ---

# Function to log messages
log() {
  local level="$1"
  local message="$2"
  local timestamp=$(date +"%Y-%m-%d %H:%M:%S")

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

  echo "[${timestamp}] [${level}] ${message}" >> "$LOG_FILE"
}

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Maps ENVIRONMENT to the Hardhat network name defined in
# code/blockchain/hardhat.config.js. Shared by deploy_blockchain() (to
# deploy to the right network) and deploy_backend() (to point the backend
# at that network's deployment manifest) so the two can't drift apart.
network_for_environment() {
  case "$1" in
    "development")
      echo "localhost"
      ;;
    "staging")
      echo "testnet"
      ;;
    "production")
      echo "mainnet"
      ;;
    *)
      return 1
      ;;
  esac
}

# Function to load environment variables
load_env() {
  if [ -f "$ENV_FILE" ]; then
    log "INFO" "Loading environment variables from $ENV_FILE"
    # Use 'set -a' to export all variables, but ensure it's turned off after sourcing
    set -a
    # Use 'source' to load variables into the current shell
    # This is safer than 'set -a; . "$ENV_FILE"; set +a' as it handles errors better
    if ! source "$ENV_FILE"; then
        log "ERROR" "Failed to source environment file: $ENV_FILE"
        exit 1
    fi
    set +a
  else
    log "WARNING" "Environment file not found: $ENV_FILE. Proceeding without explicit environment variables."
  fi
}

# Function to create backup
create_backup() {
  local component="$1"
  local source_dir="$2"

  if [ ! -d "$source_dir" ]; then
    log "WARNING" "Source directory not found for backup: $source_dir"
    return 0 # Not a critical error, just skip backup
  fi

  local backup_path="$BACKUP_DIR/$component"
  mkdir -p "$backup_path"

  log "INFO" "Creating backup of $component at $backup_path"

  if [ "$DRY_RUN" = true ]; then
    log "INFO" "[DRY RUN] Would backup $source_dir to $backup_path"
  else
    # Use rsync for safer and more efficient copying
    rsync -a --exclude='node_modules' --exclude='venv' --exclude='__pycache__' "$source_dir/" "$backup_path/"
    log "SUCCESS" "Backup created at $backup_path"
  fi
}

# --- Deployment Functions ---

# Function to deploy blockchain contracts
deploy_blockchain() {
  log "INFO" "Deploying blockchain contracts for $ENVIRONMENT environment..."

  local blockchain_dir="$PROJECT_DIR/code/blockchain"
  if [ ! -d "$blockchain_dir" ]; then
    log "ERROR" "Blockchain directory not found: $blockchain_dir"
    return 1
  fi

  create_backup "blockchain" "$blockchain_dir"

  (
    cd "$blockchain_dir"
    log "INFO" "Installing blockchain dependencies..."
    if [ "$DRY_RUN" = false ]; then
      npm install --silent
    fi

    local network
    network="$(network_for_environment "$ENVIRONMENT")" || {
      log "ERROR" "Unknown environment: $ENVIRONMENT"
      return 1
    }

    log "INFO" "Deploying contracts to $network network..."

    if [ "$DRY_RUN" = true ]; then
      log "INFO" "[DRY RUN] Would run: npx hardhat run scripts/deploy.js --network $network"
    else
      npx hardhat run scripts/deploy.js --network "$network"
      if [ $? -ne 0 ]; then
        log "ERROR" "Contract deployment failed"
        return 1
      fi

      # Store deployment artifacts
      local deploy_target="$PROJECT_DIR/deployments/$ENVIRONMENT/blockchain"
      mkdir -p "$deploy_target"
      cp -r artifacts "$deploy_target/"
      cp -r deployments "$deploy_target/"

      log "SUCCESS" "Blockchain contracts deployed to $network"
    fi
  ) || return 1
  return 0
}

# Function to deploy backend
deploy_backend() {
  log "INFO" "Deploying backend for $ENVIRONMENT environment..."

  local backend_dir="$PROJECT_DIR/code/backend"
  if [ ! -d "$backend_dir" ]; then
    log "ERROR" "Backend directory not found: $backend_dir"
    return 1
  fi

  create_backup "backend" "$backend_dir"

  (
    cd "$backend_dir"
    # Activate virtual environment if it exists
    if [ -d "$PROJECT_DIR/venv" ]; then
      source "$PROJECT_DIR/venv/bin/activate"
    fi

    log "INFO" "Installing backend dependencies..."
    if [ -f "requirements.txt" ] && [ "$DRY_RUN" = false ]; then
      pip install -r requirements.txt --quiet
    fi

    # Create environment-specific configuration.
    #
    # config/settings.py (a pydantic-settings BaseSettings) reads from a
    # .env file plus real process environment variables - it does NOT
    # import config/<environment>.py. A previous version of this script
    # only wrote the latter, so DATABASE_URL/REDIS_URL/blockchain settings
    # generated here were silently never read by the running app. Both are
    # written now: .env because it's what the app actually reads, and
    # config/<environment>.py kept alongside it purely as a
    # human-readable record of what was generated for this deploy.
    local config_dir="$backend_dir/config"
    mkdir -p "$config_dir"
    local config_file="$config_dir/$ENVIRONMENT.py"
    local env_file="$backend_dir/.env"

    if [ "$DRY_RUN" = false ]; then
      # Securely generate a secret key if not set in .env
      local secret_key="${SECRET_KEY:-$(openssl rand -hex 32)}"
      local encryption_key="${ENCRYPTION_KEY:-$(openssl rand -hex 32)}"

      # Resolve the same Hardhat network deploy_blockchain() just deployed
      # to (or will deploy to, if run in the same invocation), so the
      # backend points at the manifest deploy.js wrote for THAT network
      # rather than guessing.
      local network
      network="$(network_for_environment "$ENVIRONMENT")" || {
        log "ERROR" "Unknown environment: $ENVIRONMENT"
        return 1
      }
      local eth_rpc_url eth_chain_id
      case "$network" in
        "localhost")
          eth_rpc_url="http://127.0.0.1:8545"
          eth_chain_id="31337"
          ;;
        "testnet")
          eth_rpc_url="${TESTNET_RPC_URL:-}"
          eth_chain_id="${TESTNET_CHAIN_ID:-11155111}"
          ;;
        "mainnet")
          eth_rpc_url="${MAINNET_RPC_URL:-}"
          eth_chain_id="1"
          ;;
      esac
      local deployment_file="$PROJECT_DIR/code/blockchain/deployments/contracts.$network.json"

      cat > "$env_file" << EOF
# ChainFinity Backend Configuration
# Environment: $ENVIRONMENT
# Generated on: $(date)
# Written by scripts/deploy_chainfinity.sh:deploy_backend - do not edit by
# hand, it will be overwritten on the next deploy.

ENVIRONMENT=$ENVIRONMENT
DEBUG=$([ "$ENVIRONMENT" = "development" ] && echo "true" || echo "false")

# Database
DATABASE_URL=${DATABASE_URL:-postgresql+asyncpg://postgres:postgres@localhost:5432/chainfinity}

# Redis
REDIS_URL=${REDIS_URL:-redis://localhost:6379/0}

# Blockchain - see code/backend/config/settings.py's blockchain property
# and code/backend/services/blockchain/web3_client.py. ETH_RPC_URL/
# ETH_CHAIN_ID point at the network deploy_blockchain() deployed to, and
# BLOCKCHAIN_DEPLOYMENT_FILE is the address+ABI manifest scripts/deploy.js
# wrote there - both env vars are picked up with no other config needed.
ETH_RPC_URL=$eth_rpc_url
ETH_CHAIN_ID=$eth_chain_id
BLOCKCHAIN_DEPLOYMENT_FILE=$deployment_file
ETHERSCAN_API_KEY=${ETHERSCAN_API_KEY:-}

# Security
SECRET_KEY=$secret_key
ENCRYPTION_KEY=$encryption_key
EOF
      chmod 600 "$env_file"
      log "INFO" "Created backend environment file: $env_file"

      cat > "$config_file" << EOF
# ChainFinity Backend Configuration (reference copy - see $env_file for the
# file the application actually loads)
# Environment: $ENVIRONMENT
# Generated on: $(date)

DEBUG = $([ "$ENVIRONMENT" = "development" ] && echo "True" || echo "False")
TESTING = $([ "$ENVIRONMENT" = "development" ] && echo "True" || echo "False")

# Database
DATABASE_URL = "${DATABASE_URL:-postgresql+asyncpg://postgres:postgres@localhost:5432/chainfinity}"

# Redis
REDIS_URL = "${REDIS_URL:-redis://localhost:6379/0}"

# Blockchain
BLOCKCHAIN_NETWORK = "$network"
ETH_RPC_URL = "$eth_rpc_url"
ETH_CHAIN_ID = $eth_chain_id
BLOCKCHAIN_DEPLOYMENT_FILE = "$deployment_file"
ETHERSCAN_API_KEY = "${ETHERSCAN_API_KEY:-your_etherscan_api_key}"

# Security
SECRET_KEY = "$secret_key"
ALLOWED_HOSTS = ["*"]  # Restrict in production
EOF
      log "INFO" "Created environment config: $config_file"
    fi

    # Build and package the application
    log "INFO" "Building backend application..."
    if [ "$DRY_RUN" = false ]; then
      local deploy_dir="$PROJECT_DIR/deployments/$ENVIRONMENT/backend"
      mkdir -p "$deploy_dir"

      # Copy application files
      rsync -av --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' \
        --exclude='tests' --exclude='venv' --exclude='*.egg-info' \
        "$backend_dir/" "$deploy_dir/"

      # Create deployment script
      cat > "$deploy_dir/deploy.sh" << EOF
#!/bin/bash
# ChainFinity Backend Deployment Script
# Environment: $ENVIRONMENT
# Generated on: $(date)

# Set environment variables
export ENVIRONMENT="$ENVIRONMENT"
export PYTHONPATH="$deploy_dir"

# Start the application
if command -v uvicorn &> /dev/null; then
  # Use gunicorn for production-ready deployment
  if [ "$ENVIRONMENT" = "production" ]; then
    exec gunicorn -w \${WORKERS:-4} -b 0.0.0.0:\${PORT:-8000} app.main:app -k uvicorn.workers.UvicornWorker
  else
    exec uvicorn app.main:app --host 0.0.0.0 --port \${PORT:-8000} --reload
  fi
else
  echo "Error: uvicorn/gunicorn not found. Please install them."
  exit 1
fi
EOF
      chmod +x "$deploy_dir/deploy.sh"
      log "SUCCESS" "Backend deployed to $deploy_dir"
    fi
  ) || return 1
  return 0
}

# Function to deploy frontend
deploy_frontend() {
  log "INFO" "Deploying frontend for $ENVIRONMENT environment..."

  local frontend_dir="$PROJECT_DIR/web-frontend"
  if [ ! -d "$frontend_dir" ]; then
    log "ERROR" "Frontend directory not found: $frontend_dir"
    return 1
  fi

  create_backup "frontend" "$frontend_dir"

  (
    cd "$frontend_dir"
    log "INFO" "Installing frontend dependencies..."
    if [ "$DRY_RUN" = false ]; then
      npm install --silent
    fi

    # Create environment-specific configuration
    local env_config_file="$frontend_dir/.env.$ENVIRONMENT"
    if [ "$DRY_RUN" = false ]; then
      cat > "$env_config_file" << EOF
# ChainFinity Frontend Configuration
# Environment: $ENVIRONMENT
# Generated on: $(date)

REACT_APP_ENV=$ENVIRONMENT
REACT_APP_API_URL=${API_URL:-http://localhost:8080}
REACT_APP_BLOCKCHAIN_NETWORK=${BLOCKCHAIN_NETWORK:-$ENVIRONMENT}
REACT_APP_INFURA_KEY=${INFURA_API_KEY:-your_infura_api_key}
EOF
      log "INFO" "Created environment config: $env_config_file"
    fi

    # Build the frontend
    log "INFO" "Building frontend application..."
    if [ "$DRY_RUN" = false ]; then
      REACT_APP_ENV="$ENVIRONMENT" npm run build
      if [ $? -ne 0 ]; then
        log "ERROR" "Frontend build failed"
        return 1
      fi

      local deploy_dir="$PROJECT_DIR/deployments/$ENVIRONMENT/frontend"
      mkdir -p "$deploy_dir"

      # Copy build files
      rsync -av "$frontend_dir/build/" "$deploy_dir/"

      # Create deployment info file
      local version=$(jq -r '.version' package.json 2>/dev/null || echo "unknown")
      cat > "$deploy_dir/deployment-info.json" << EOF
{
  "environment": "$ENVIRONMENT",
  "buildTime": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "version": "$version"
}
EOF
      log "SUCCESS" "Frontend deployed to $deploy_dir"
    fi
  ) || return 1
  return 0
}

# Function to deploy mobile frontend
deploy_mobile_frontend() {
  log "INFO" "Deploying mobile frontend for $ENVIRONMENT environment..."

  local mobile_dir="$PROJECT_DIR/mobile-frontend"
  if [ ! -d "$mobile_dir" ]; then
    log "WARNING" "Mobile frontend directory not found: $mobile_dir. Skipping deployment."
    return 0
  fi

  create_backup "mobile-frontend" "$mobile_dir"

  (
    cd "$mobile_dir"
    log "INFO" "Installing mobile frontend dependencies..."
    if [ "$DRY_RUN" = false ]; then
      npm install --silent
    fi

    # Create environment-specific configuration
    local env_config_file="$mobile_dir/.env.$ENVIRONMENT"
    if [ "$DRY_RUN" = false ]; then
      cat > "$env_config_file" << EOF
# ChainFinity Mobile Frontend Configuration
# Environment: $ENVIRONMENT
# Generated on: $(date)

REACT_NATIVE_APP_ENV=$ENVIRONMENT
EXPO_PUBLIC_API_URL=${API_URL:-http://localhost:8080}
REACT_NATIVE_BLOCKCHAIN_NETWORK=${BLOCKCHAIN_NETWORK:-$ENVIRONMENT}
REACT_NATIVE_INFURA_KEY=${INFURA_API_KEY:-your_infura_api_key}
EOF
      log "INFO" "Created environment config: $env_config_file"
    fi

    # Build the mobile app
    log "INFO" "Building mobile application (preparation only)..."
    if [ "$DRY_RUN" = false ]; then
      local deploy_dir="$PROJECT_DIR/deployments/$ENVIRONMENT/mobile-frontend"
      mkdir -p "$deploy_dir"

      # Copy necessary files for deployment
      rsync -av --exclude='node_modules' --exclude='.git' \
        "$mobile_dir/" "$deploy_dir/"

      # Create deployment info file
      local version=$(jq -r '.version' package.json 2>/dev/null || echo "unknown")
      cat > "$deploy_dir/deployment-info.json" << EOF
{
  "environment": "$ENVIRONMENT",
  "buildTime": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "version": "$version"
}
EOF
      log "SUCCESS" "Mobile frontend prepared for deployment at $deploy_dir"
      log "INFO" "Note: For actual mobile deployment, use platform-specific build tools (e.g., Xcode, Android Studio)"
    fi
  ) || return 1
  return 0
}

# Function to update infrastructure
update_infrastructure() {
  log "INFO" "Updating infrastructure for $ENVIRONMENT environment..."

  local infra_dir="$PROJECT_DIR/infrastructure"
  if [ ! -d "$infra_dir" ]; then
    log "ERROR" "Infrastructure directory not found: $infra_dir"
    return 1
  fi

  create_backup "infrastructure" "$infra_dir"

  # Check for Terraform files
  if [ -d "$infra_dir/terraform" ]; then
    log "INFO" "Found Terraform configuration"
    if command_exists terraform; then
      local tf_env_dir="$infra_dir/terraform/$ENVIRONMENT"
      if [ -d "$tf_env_dir" ]; then
        (
          cd "$tf_env_dir"
          if [ "$DRY_RUN" = true ]; then
            log "INFO" "[DRY RUN] Would run Terraform plan and apply"
          else
            log "INFO" "Running Terraform init..."
            terraform init -input=false

            log "INFO" "Running Terraform plan..."
            terraform plan -out=tfplan -input=false

            log "INFO" "Applying Terraform changes..."
            terraform apply -auto-approve tfplan -input=false

            if [ $? -ne 0 ]; then
              log "ERROR" "Terraform apply failed"
              return 1
            fi
            log "SUCCESS" "Infrastructure updated with Terraform"
          fi
        ) || return 1
      else
        log "WARNING" "Terraform environment directory not found: $tf_env_dir. Skipping Terraform deployment."
      fi
    else
      log "WARNING" "Terraform not installed, skipping infrastructure update with Terraform"
    fi
  fi

  # Check for the Docker Compose file (single compose file lives in
  # infrastructure/; there are no per-environment compose files).
  local compose_file="$infra_dir/docker-compose.yml"
  local compose_cmd=""
  if docker compose version &> /dev/null; then
    compose_cmd="docker compose"
  elif command_exists docker-compose; then
    compose_cmd="docker-compose"
  fi
  if [ -f "$compose_file" ]; then
    log "INFO" "Found Docker Compose configuration: $compose_file"
    if [ -n "$compose_cmd" ]; then
      if [ "$DRY_RUN" = true ]; then
        log "INFO" "[DRY RUN] Would run Docker Compose up"
      else
        log "INFO" "Starting/Updating Docker Compose services..."
        if ! $compose_cmd -f "$compose_file" up -d --build --remove-orphans; then
          log "ERROR" "Docker Compose up failed"
          return 1
        fi
        log "SUCCESS" "Infrastructure updated with Docker Compose"
      fi
    else
      log "WARNING" "Docker Compose not installed, skipping container deployment"
    fi
  fi

  return 0
}

# Function to generate deployment report
generate_deployment_report() {
  log "INFO" "Generating deployment report..."

  local report_file="$PROJECT_DIR/deployments/$ENVIRONMENT/deployment-report.html"
  mkdir -p "$(dirname "$report_file")"

  # Use a temporary file for the report content to avoid issues with EOF
  local temp_report=$(mktemp)

  cat > "$temp_report" << EOF
<!DOCTYPE html>
<html>
<head>
  <title>ChainFinity Deployment Report - $ENVIRONMENT</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    h1 { color: #333366; }
    .section { margin-bottom: 20px; }
    .success { color: green; }
    .warning { color: orange; }
    .error { color: red; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; }
    tr:nth-child(even) { background-color: #f9f9f9; }
  </style>
</head>
<body>
  <h1>ChainFinity Deployment Report</h1>
  <p><strong>Environment:</strong> $ENVIRONMENT</p>
  <p><strong>Deployment Time:</strong> $(date +%Y-%m-%d\ %H:%M:%S)</p>

  <div class="section">
    <h2>Deployment Summary</h2>
    <table>
      <tr>
        <th>Component</th>
        <th>Status</th>
        <th>Location</th>
      </tr>
EOF

  # Add component statuses
  local components=("blockchain" "backend" "frontend" "mobile-frontend" "infrastructure")
  for component in "${components[@]}"; do
    local status="Not Deployed"
    local location="N/A"

    if [ -d "$PROJECT_DIR/deployments/$ENVIRONMENT/$component" ]; then
      status="<span class=\"success\">Deployed</span>"
      location="$PROJECT_DIR/deployments/$ENVIRONMENT/$component"
    fi

    cat >> "$temp_report" << EOF
      <tr>
        <td>$component</td>
        <td>$status</td>
        <td>$location</td>
      </tr>
EOF
  done

  # Add environment variables (sanitized)
  cat >> "$temp_report" << EOF
    </table>
  </div>

  <div class="section">
    <h2>Environment Configuration</h2>
    <table>
      <tr>
        <th>Variable</th>
        <th>Value</th>
      </tr>
EOF

  # Add sanitized environment variables
  if [ -f "$ENV_FILE" ]; then
    while IFS='=' read -r key value; do
      # Skip comments and empty lines
      key=$(echo "$key" | xargs)
      value=$(echo "$value" | xargs)
      [[ $key =~ ^# ]] && continue
      [[ -z $key ]] && continue

      # Sanitize sensitive values
      if [[ $key =~ (KEY|SECRET|PASSWORD|TOKEN|PRIVATE_KEY) ]]; then
        value="********"
      fi

      cat >> "$temp_report" << EOF
      <tr>
        <td>$key</td>
        <td>$value</td>
      </tr>
EOF
    done < "$ENV_FILE"
  fi

  # Close the report
  cat >> "$temp_report" << EOF
    </table>
  </div>

  <div class="section">
    <h2>Deployment Log (Last 50 lines)</h2>
    <pre>$(tail -n 50 "$LOG_FILE")</pre>
  </div>
</body>
</html>
EOF

  mv "$temp_report" "$report_file"
  log "SUCCESS" "Deployment report generated: $report_file"
}

# --- Main Function ---

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project-dir)
      PROJECT_DIR="$2"
      shift 2
      ;;
    --log-dir)
      LOG_DIR="$2"
      shift 2
      ;;
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --backup-dir)
      BACKUP_DIR="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --component)
      DEPLOY_COMPONENT="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --project-dir DIR     Set project directory (default: current directory)"
      echo "  --log-dir DIR         Log directory (default: ./logs)"
      echo "  --env-file FILE       Environment file (default: .env)"
      echo "  --environment ENV     Deployment environment (development, staging, production)"
      echo "  --backup-dir DIR      Backup directory (default: ./backups/YYYYMMDD_HHMMSS)"
      echo "  --dry-run             Perform a dry run without making changes"
      echo "  --component NAME      Deploy only specific component (blockchain, backend, frontend, mobile, infrastructure, all)"
      echo "  --help                Show this help message"
      exit 0
      ;;
    *)
      log "ERROR" "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create directories if they don't exist
mkdir -p "$LOG_DIR"
mkdir -p "$BACKUP_DIR"

# Log file
LOG_FILE="$LOG_DIR/deploy_$(date +%Y%m%d_%H%M%S).log"

main() {
  log "INFO" "Starting ChainFinity deployment for $ENVIRONMENT environment..."
  log "INFO" "Project directory: $PROJECT_DIR"

  if [ "$DRY_RUN" = true ]; then
    log "WARNING" "Running in DRY RUN mode - no changes will be made"
  fi

  # Load environment variables
  load_env

  # Track overall success
  local success=true

  # Deploy based on component selection
  case "${DEPLOY_COMPONENT}" in
    "blockchain")
      deploy_blockchain || success=false
      ;;
    "backend")
      deploy_backend || success=false
      ;;
    "frontend")
      deploy_frontend || success=false
      ;;
    "mobile")
      deploy_mobile_frontend || success=false
      ;;
    "infrastructure")
      update_infrastructure || success=false
      ;;
    "all")
      # Deploy in the correct order
      update_infrastructure || success=false
      deploy_blockchain || success=false
      deploy_backend || success=false
      deploy_frontend || success=false
      deploy_mobile_frontend || success=false
      ;;
    *)
      log "ERROR" "Unknown component: $DEPLOY_COMPONENT"
      exit 1
      ;;
  esac

  # Generate deployment report
  generate_deployment_report

  # Final status
  if [ "$success" = true ]; then
    log "SUCCESS" "Deployment to $ENVIRONMENT environment completed successfully!"
    exit 0
  else
    log "ERROR" "Deployment to $ENVIRONMENT environment failed. Check the report for details."
    exit 1
  fi
}

# Run main function
main

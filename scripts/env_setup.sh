#!/bin/bash
# Enhanced ChainFinity Environment Setup Script
# This script automates the setup process for ChainFinity development environment

# --- Configuration ---
# Exit immediately if a command exits with a non-zero status, treat unset variables as an error, and fail if any command in a pipeline fails
set -euo pipefail

# Color definitions for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log levels
INFO="INFO"
WARNING="WARNING"
ERROR="ERROR"
SUCCESS="SUCCESS"

# Default Configuration variables
DEFAULT_PROJECT_DIR="$(pwd)"
DEFAULT_NODE_VERSION="18"
DEFAULT_PYTHON_VERSION="3.11"
DEFAULT_INSTALL_DOCKER=true
DEFAULT_SETUP_DATABASES=true
DEFAULT_ENVIRONMENT="development"

# --- Utility Functions ---

# Logging function
log() {
  local level="$1"
  local message="$2"
  local timestamp
  timestamp=$(date +"%Y-%m-%d %H:%M:%S")

  case $level in
    "$INFO")
      echo -e "${BLUE}[${timestamp}] [${level}] ${message}${NC}"
      ;;
    "$WARNING")
      echo -e "${YELLOW}[${timestamp}] [${level}] ${message}${NC}"
      ;;
    "$ERROR")
      echo -e "${RED}[${timestamp}] [${level}] ${message}${NC}"
      ;;
    "$SUCCESS")
      echo -e "${GREEN}[${timestamp}] [${level}] ${message}${NC}"
      ;;
  esac

  echo "[${timestamp}] [${level}] ${message}" >> "$LOG_FILE"
}

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to handle errors
handle_error() {
  local exit_code=$1
  local error_message=$2

  if [ "$exit_code" -ne 0 ]; then
    log "$ERROR" "$error_message (Exit code: $exit_code)"
    log "$ERROR" "Check the log file for more details: $LOG_FILE"
    exit "$exit_code"
  fi
}

# Function to create backup of configuration files
backup_config() {
  local file="$1"
  if [ -f "$file" ]; then
    local backup_file
    backup_file="${file}.bak.$(date +%Y%m%d_%H%M%S)"
    cp "$file" "$backup_file"
    log "$INFO" "Created backup of $file at $backup_file"
  fi
}

# --- Setup Functions ---

setup_system_tools() {
  log "$INFO" "Checking and installing system tools..."
  local tools_to_install=""
  for tool in git curl wget unzip jq; do
    if ! command_exists "$tool"; then
      tools_to_install+="$tool "
    fi
  done

  if [ -n "$tools_to_install" ]; then
    log "$INFO" "Installing missing tools: $tools_to_install"
    sudo apt-get update && sudo apt-get install -y $tools_to_install
    handle_error $? "Failed to install system tools"
  else
    log "$SUCCESS" "All required system tools are installed."
  fi
}

setup_nodejs() {
  log "$INFO" "Setting up Node.js environment..."
  # Check for NVM
  if ! command_exists nvm; then
    log "$INFO" "Installing NVM (Node Version Manager)..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
  fi

  # Use NVM to install and use the desired Node.js version
  if ! nvm ls "$NODE_VERSION" | grep -q "$NODE_VERSION"; then
    log "$INFO" "Installing Node.js $NODE_VERSION..."
    nvm install "$NODE_VERSION"
    handle_error $? "Failed to install Node.js $NODE_VERSION"
  fi

  nvm use "$NODE_VERSION"
  handle_error $? "Failed to use Node.js $NODE_VERSION"

  log "$SUCCESS" "Node.js $(node -v) is ready."

  # Install global Node.js packages
  log "$INFO" "Installing global Node.js packages..."
  npm_packages=("npm" "yarn" "hardhat" "truffle" "solc")
  for package in "${npm_packages[@]}"; do
    if ! command_exists "$package"; then
      npm install -g "$package"
      handle_error $? "Failed to install $package"
      log "$SUCCESS" "Installed $package globally"
    else
      log "$INFO" "$package is already installed"
    fi
  done
}

setup_python() {
  log "$INFO" "Setting up Python environment..."
  # Check for pyenv
  if ! command_exists pyenv; then
    log "$INFO" "Installing pyenv..."
    curl https://pyenv.run | bash
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"
  fi

  # Use pyenv to install and set the desired Python version
  if ! pyenv versions | grep -q "$PYTHON_VERSION"; then
    log "$INFO" "Installing Python $PYTHON_VERSION..."
    pyenv install "$PYTHON_VERSION"
    handle_error $? "Failed to install Python $PYTHON_VERSION"
  fi

  pyenv global "$PYTHON_VERSION"
  handle_error $? "Failed to set Python $PYTHON_VERSION as global"

  log "$SUCCESS" "Python $(python3 --version) is ready."

  # Setup Python virtual environment
  log "$INFO" "Setting up Python virtual environment..."
  if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
    handle_error $? "Failed to create Python virtual environment"
    log "$SUCCESS" "Created Python virtual environment"
  else
    log "$INFO" "Python virtual environment already exists"
  fi

  # Activate virtual environment
  source "$PROJECT_DIR/venv/bin/activate"
  handle_error $? "Failed to activate Python virtual environment"
  log "$INFO" "Activated Python virtual environment"

  # Install Python dependencies
  log "$INFO" "Installing Python dependencies..."
  if [ -f "$PROJECT_DIR/code/backend/requirements.txt" ]; then
    pip install -r "$PROJECT_DIR/code/backend/requirements.txt" --quiet
    handle_error $? "Failed to install Python dependencies"
    log "$SUCCESS" "Installed Python dependencies"
  else
    log "$WARNING" "Python requirements.txt not found at $PROJECT_DIR/code/backend/requirements.txt"
  fi

  # Install development Python packages
  pip install black flake8 pytest pytest-cov mypy --quiet
  handle_error $? "Failed to install Python development packages"
  log "$SUCCESS" "Installed Python development packages"
}

setup_docker() {
  if [ "$INSTALL_DOCKER" = true ]; then
    log "$INFO" "Setting up Docker..."
    if ! command_exists docker; then
      log "$INFO" "Installing Docker..."
      curl -fsSL https://get.docker.com -o get-docker.sh
      sudo sh get-docker.sh
      handle_error $? "Failed to install Docker"

      # Add current user to docker group
      sudo usermod -aG docker "$USER"
      log "$WARNING" "Docker installed. You may need to log out and log back in for group changes to take effect."
    else
      log "$INFO" "Docker is already installed"
    fi

    # Install Docker Compose
    if ! command_exists docker-compose; then
      log "$INFO" "Installing Docker Compose..."
      # Use the official Docker Compose installation method
      sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
      sudo chmod +x /usr/local/bin/docker-compose
      handle_error $? "Failed to install Docker Compose"
      log "$SUCCESS" "Docker Compose installed successfully"
    else
      log "$INFO" "Docker Compose is already installed"
    fi
  else
    log "$INFO" "Skipping Docker setup as requested."
  fi
}

setup_databases() {
  if [ "$SETUP_DATABASES" = true ]; then
    log "$INFO" "Setting up databases..."

    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
      log "$WARNING" "Docker is not running. Attempting to start Docker..."
      sudo systemctl start docker || log "$WARNING" "Failed to start Docker. Database setup may fail."
    fi

    # Create docker-compose file for databases if it doesn't exist
    local dev_compose_file="$PROJECT_DIR/infrastructure/docker-compose.yml"
    if [ ! -f "$dev_compose_file" ]; then
      mkdir -p "$PROJECT_DIR/infrastructure"
      cat > "$dev_compose_file" << EOF
version: '3.8'

services:
  postgres:
    image: timescale/timescaledb:latest-pg14
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: chainfinity
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
EOF
      log "$INFO" "Created docker-compose.yml for databases"
    fi

    # Start database containers
    log "$INFO" "Starting database containers..."
    docker-compose -f "$dev_compose_file" up -d
    handle_error $? "Failed to start database containers"
    log "$SUCCESS" "Database containers started successfully"
  else
    log "$INFO" "Skipping database setup as requested."
  fi
}

setup_project_dependencies() {
  log "$INFO" "Installing project dependencies..."

  # Install blockchain dependencies
  if [ -f "$PROJECT_DIR/code/blockchain/package.json" ]; then
    log "$INFO" "Installing blockchain dependencies..."
    (cd "$PROJECT_DIR/code/blockchain" && npm install --silent)
    handle_error $? "Failed to install blockchain dependencies"
    log "$SUCCESS" "Installed blockchain dependencies"
  fi

  # Install frontend dependencies
  if [ -f "$PROJECT_DIR/web-frontend/package.json" ]; then
    log "$INFO" "Installing frontend dependencies..."
    (cd "$PROJECT_DIR/web-frontend" && npm install --silent)
    handle_error $? "Failed to install frontend dependencies"
    log "$SUCCESS" "Installed frontend dependencies"
  fi

  # Install mobile-frontend dependencies
  if [ -f "$PROJECT_DIR/mobile-frontend/package.json" ]; then
    log "$INFO" "Installing mobile-frontend dependencies..."
    (cd "$PROJECT_DIR/mobile-frontend" && npm install --silent)
    handle_error $? "Failed to install mobile-frontend dependencies"
    log "$SUCCESS" "Installed mobile-frontend dependencies"
  fi
}

create_activation_script() {
  # Create a convenience script to activate the environment
  local activate_script="$PROJECT_DIR/activate_env.sh"
  cat > "$activate_script" << EOF
#!/bin/bash
# ChainFinity Environment Activation Script
# Generated by setup script on $(date)

# Activate Python virtual environment
if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
  source "$PROJECT_DIR/venv/bin/activate"
fi

# Set Node.js version via NVM
export NVM_DIR="\$HOME/.nvm"
[ -s "\$NVM_DIR/nvm.sh" ] && \. "\$NVM_DIR/nvm.sh"
if command -v nvm &> /dev/null; then
  nvm use $NODE_VERSION
fi

# Set environment variables
export NODE_ENV=$ENVIRONMENT
export PROJECT_DIR="$PROJECT_DIR"

echo "ChainFinity environment activated for $ENVIRONMENT"
echo "Project directory: $PROJECT_DIR"
EOF

  chmod +x "$activate_script"
  log "$SUCCESS" "Created environment activation script: activate_env.sh"
}

# --- Main Execution ---

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project-dir)
      PROJECT_DIR="$2"
      shift 2
      ;;
    --node-version)
      NODE_VERSION="$2"
      shift 2
      ;;
    --python-version)
      PYTHON_VERSION="$2"
      shift 2
      ;;
    --skip-docker)
      INSTALL_DOCKER=false
      shift
      ;;
    --skip-databases)
      SETUP_DATABASES=false
      shift
      ;;
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --project-dir DIR       Set project directory (default: current directory)"
      echo "  --node-version VERSION  Set Node.js version (default: 18)"
      echo "  --python-version VERSION Set Python version (default: 3.11)"
      echo "  --skip-docker           Skip Docker installation"
      echo "  --skip-databases        Skip database setup"
      echo "  --environment ENV       Set environment (development, staging, production)"
      echo "  --help                  Show this help message"
      exit 0
      ;;
    *)
      log "$ERROR" "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Set defaults for unspecified options
PROJECT_DIR="${PROJECT_DIR:-$DEFAULT_PROJECT_DIR}"
NODE_VERSION="${NODE_VERSION:-$DEFAULT_NODE_VERSION}"
PYTHON_VERSION="${PYTHON_VERSION:-$DEFAULT_PYTHON_VERSION}"
INSTALL_DOCKER="${INSTALL_DOCKER:-$DEFAULT_INSTALL_DOCKER}"
SETUP_DATABASES="${SETUP_DATABASES:-$DEFAULT_SETUP_DATABASES}"
ENVIRONMENT="${ENVIRONMENT:-$DEFAULT_ENVIRONMENT}"

# Create log directory and set log file path
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/setup_$(date +%Y%m%d_%H%M%S).log"

main() {
  log "$INFO" "Starting ChainFinity environment setup for $ENVIRONMENT environment"
  log "$INFO" "Project directory: $PROJECT_DIR"

  # Validate project directory
  if [ ! -d "$PROJECT_DIR" ]; then
    log "$ERROR" "Project directory does not exist: $PROJECT_DIR"
    exit 1
  fi

  # Change to project directory
  cd "$PROJECT_DIR" || handle_error $? "Failed to change to project directory"
  log "$INFO" "Changed to project directory: $(pwd)"

  # Run setup steps
  setup_system_tools
  setup_nodejs
  setup_python
  setup_docker
  setup_databases
  setup_project_dependencies
  create_activation_script

  # Final setup steps
  log "$INFO" "Performing final setup steps..."

  # Create necessary directories if they don't exist
  directories=(
    "code/blockchain"
    "code/backend"
    "web-frontend"
    "mobile-frontend"
    "docs"
    "infrastructure"
    "data"
    "logs"
    "scripts"
  )

  for dir in "${directories[@]}"; do
    if [ ! -d "$PROJECT_DIR/$dir" ]; then
      mkdir -p "$PROJECT_DIR/$dir"
      log "$INFO" "Created directory: $dir"
    fi
  done

  # Create .env file if it doesn't exist
  if [ ! -f "$PROJECT_DIR/.env" ]; then
    if [ -f "$PROJECT_DIR/env.example" ]; then
      cp "$PROJECT_DIR/env.example" "$PROJECT_DIR/.env"
      log "$INFO" "Created .env file from env.example"
    else
      # Create default .env file
      cat > "$PROJECT_DIR/.env" << EOF
# ChainFinity Environment Configuration
# Generated by setup script on $(date)
# Environment: $ENVIRONMENT

# General
ENVIRONMENT=$ENVIRONMENT
LOG_LEVEL=info

# Backend (FastAPI). DATABASE_URL must use the +asyncpg driver the async
# engine requires. SECRET_KEY and ENCRYPTION_KEY are required by the app.
BACKEND_PORT=8080
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/chainfinity
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-to-a-32-char-minimum-secret-value
ENCRYPTION_KEY=change-me-to-a-fernet-key

# Blockchain
BLOCKCHAIN_NETWORK=${ENVIRONMENT}
INFURA_API_KEY=your_infura_api_key
ETHERSCAN_API_KEY=your_etherscan_api_key
PRIVATE_KEY=your_private_key_for_deployment

# Frontend
REACT_APP_API_URL=http://localhost:8080
REACT_APP_CHAIN_ID=1
EOF
      log "$INFO" "Created default .env file"
    fi
  else
    backup_config "$PROJECT_DIR/.env"
    log "$INFO" ".env file already exists, created backup"
  fi

  # Setup complete
  log "$SUCCESS" "ChainFinity environment setup completed successfully!"
  log "$INFO" "To activate the environment, run: source $PROJECT_DIR/activate_env.sh"
  log "$INFO" "To start the application, run: $PROJECT_DIR/scripts/run_chainfinity.sh"
  log "$INFO" "Setup log saved to: $LOG_FILE"
}

# Run main function
main

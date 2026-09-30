# ChainFinity Installation Guide

This guide provides comprehensive installation instructions for ChainFinity across different platforms and deployment scenarios.

## System Prerequisites

Before installing ChainFinity, ensure your system meets these requirements:

| Component          | Minimum Version | Recommended Version | Notes                                           |
| ------------------ | --------------- | ------------------- | ----------------------------------------------- |
| **Node.js**        | 16.x            | 18.x or higher      | Required for blockchain and frontend components |
| **Python**         | 3.9             | 3.11 or higher      | Required for backend and AI models              |
| **PostgreSQL**     | 13              | 15 or higher        | Primary database                                |
| **Redis**          | 6.x             | 7 or higher         | Caching and session storage                     |
| **Docker**         | 20.x            | Latest              | For containerized deployment                    |
| **Docker Compose** | 2.x             | Latest              | Multi-container orchestration                   |
| **Git**            | 2.x             | Latest              | Version control                                 |

### Hardware Requirements

| Environment     | CPU       | RAM    | Storage    | Network    |
| --------------- | --------- | ------ | ---------- | ---------- |
| **Development** | 4 cores   | 8 GB   | 50 GB SSD  | Broadband  |
| **Staging**     | 8 cores   | 16 GB  | 100 GB SSD | High-speed |
| **Production**  | 16+ cores | 32+ GB | 500 GB SSD | Enterprise |

## Installation Options

### Option 1: Quick Start with Setup Scripts (Recommended)

The fastest way to get ChainFinity running locally.

```bash
# Clone the repository
git clone https://github.com/abrar2030/ChainFinity.git
cd ChainFinity

# Run automated setup
./scripts/env_setup.sh

# Start all services
./scripts/run_chainfinity.sh
```

The setup script will:

- Install all dependencies (Node.js, Python packages)
- Set up databases (PostgreSQL, Redis)
- Configure environment variables
- Initialize the blockchain network
- Start all services

### Option 2: Manual Installation from Source

For developers who want full control over the installation process.

#### Step 1: Clone Repository

```bash
git clone https://github.com/abrar2030/ChainFinity.git
cd ChainFinity
```

#### Step 2: Install Blockchain Dependencies

```bash
cd code/blockchain
npm install
```

**Blockchain Dependencies:**

- Hardhat 3.0+ - Ethereum development environment
- OpenZeppelin Contracts 5.4+ - Secure smart contract library
- Chainlink CCIP - Cross-chain interoperability

#### Step 3: Install Backend Dependencies

```bash
cd ../backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Backend Dependencies:**

- FastAPI 0.104.1 - High-performance web framework
- SQLAlchemy 2.0.23 - Database ORM
- Web3.py 6.11.1 - Blockchain interaction
- TensorFlow 2.x (optional) - AI models

#### Step 4: Install Frontend Dependencies

```bash
# Web Frontend
cd ../web-frontend
npm install

# Mobile Frontend (optional)
cd ../mobile-frontend
pnpm install
```

#### Step 5: Set Up Databases

```bash
# Start PostgreSQL and Redis with Docker
docker-compose -f code/backend/docker-compose.yml up -d postgres redis

# Run database migrations
cd code/backend
alembic upgrade head
```

#### Step 6: Configure Environment Variables

```bash
# Backend configuration
cd code/backend
cp .env.example .env
nano .env  # Edit with your settings

# Blockchain configuration
cd ../blockchain
cp .env.example .env
nano .env  # Add your RPC URLs and API keys

# Frontend configuration
cd ../web-frontend
cp .env.example .env
nano .env  # Configure API endpoints
```

**Critical Environment Variables:**

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT signing key (generate with `openssl rand -hex 32`)
- `ETH_RPC_URL` - Ethereum node RPC endpoint
- `ETHERSCAN_API_KEY` - Block explorer API key

#### Step 7: Start Services

```bash
# Terminal 1: Start blockchain node
cd code/blockchain
npx hardhat node

# Terminal 2: Start backend API
cd code/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Start frontend
cd code/web-frontend
npm start
```

### Option 3: Docker Deployment

For production-like environments with containerization.

```bash
# Clone repository
git clone https://github.com/abrar2030/ChainFinity.git
cd ChainFinity

# Configure environment
cp code/backend/.env.example code/backend/.env
# Edit .env with production settings

# Build and start all services
docker-compose -f code/backend/docker-compose.yml up -d

# View logs
docker-compose -f code/backend/docker-compose.yml logs -f

# Check service health
docker-compose -f code/backend/docker-compose.yml ps
```

**Docker Services:**

- `api` - FastAPI backend (port 8000)
- `postgres` - PostgreSQL database (port 5432)
- `redis` - Redis cache (port 6379)
- `nginx` - Reverse proxy (port 80/443)

### Option 4: Kubernetes Deployment

For production-scale deployments with orchestration.

```bash
# Install kubectl and helm (if not already installed)
# See https://kubernetes.io/docs/tasks/tools/

# Navigate to infrastructure
cd infrastructure/kubernetes

# Create namespace
kubectl create namespace chainfinity

# Deploy PostgreSQL
kubectl apply -f postgres/

# Deploy Redis
kubectl apply -f redis/

# Deploy backend API
kubectl apply -f deployment.yaml

# Verify deployment
kubectl get pods -n chainfinity
kubectl get services -n chainfinity
```

## Platform-Specific Installation

### Ubuntu/Debian

```bash
# Update package lists
sudo apt update

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install Redis
sudo apt install -y redis-server

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Proceed with installation steps above
```

### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install node python@3.11 postgresql@15 redis docker

# Start services
brew services start postgresql@15
brew services start redis

# Proceed with installation steps above
```

### Windows

```powershell
# Install with Chocolatey (recommended)
# First install Chocolatey: https://chocolatey.org/install

choco install nodejs python postgresql redis docker-desktop -y

# Or use Windows Subsystem for Linux (WSL2) and follow Ubuntu instructions
```

## Post-Installation

### Verify Installation

```bash
# Check backend health
curl http://localhost:8000/health

# Check API documentation
open http://localhost:8000/docs

# Check frontend
open http://localhost:3000

# Check database connection
psql -h localhost -U postgres -d chainfinity -c "SELECT version();"

# Check Redis
redis-cli ping
```

### Deploy Smart Contracts

```bash
cd code/blockchain

# Compile contracts
npx hardhat compile

# Deploy to local network
npx hardhat run scripts/deploy.js --network localhost

# Deploy to testnet (e.g., Sepolia)
npx hardhat run scripts/deploy.js --network sepolia
```

### Initialize AI Models (Optional)

```bash
cd code/ai_models

# Install ML dependencies
pip install tensorflow scikit-learn pandas numpy

# Train correlation model
python train_correlation_model.py

# Preprocess historical data
python data_preprocessing.py
```

## Troubleshooting Installation

| Issue                          | Solution                                                                     |
| ------------------------------ | ---------------------------------------------------------------------------- |
| **Port already in use**        | Change port in `.env` or kill process: `lsof -ti:8000 \| xargs kill -9`      |
| **Database connection failed** | Verify PostgreSQL is running: `pg_isready -h localhost`                      |
| **Redis connection failed**    | Check Redis status: `redis-cli ping`                                         |
| **npm install fails**          | Clear cache: `npm cache clean --force && rm -rf node_modules && npm install` |
| **Python package conflicts**   | Use fresh venv: `deactivate && rm -rf venv && python -m venv venv`           |
| **Docker permission denied**   | Add user to docker group: `sudo usermod -aG docker $USER` (then log out/in)  |

## Next Steps

After successful installation:

1. **Configure your setup** - Review [Configuration Guide](./CONFIGURATION.md)
2. **Explore the API** - Check [API Reference](./API.md)
3. **Run examples** - Try [example workflows](./examples/)
4. **Deploy contracts** - See blockchain deployment guide
5. **Set up monitoring** - Configure monitoring with `./scripts/monitor_chainfinity.sh`

## Uninstallation

To completely remove ChainFinity:

```bash
# Stop all services
docker-compose -f code/backend/docker-compose.yml down -v

# Remove installation
cd ..
rm -rf ChainFinity

# Remove databases (optional)
dropdb chainfinity
# Remove Redis data if needed
```

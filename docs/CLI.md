# ChainFinity CLI Reference

ChainFinity provides command-line tools for managing deployments, running tests, monitoring services, and performing administrative tasks.

## Table of Contents

- [Script Overview](#script-overview)
- [Environment Setup](#environment-setup)
- [Deployment Commands](#deployment-commands)
- [Testing Commands](#testing-commands)
- [Monitoring Commands](#monitoring-commands)
- [Utility Commands](#utility-commands)

## Script Overview

ChainFinity includes several automation scripts in the `scripts/` directory:

| Script                   | Purpose                          | Location                         |
| ------------------------ | -------------------------------- | -------------------------------- |
| `env_setup.sh`           | Automated environment setup      | `scripts/env_setup.sh`           |
| `run_chainfinity.sh`     | Start all services               | `scripts/run_chainfinity.sh`     |
| `deploy_chainfinity.sh`  | Deploy to different environments | `scripts/deploy_chainfinity.sh`  |
| `test_chainfinity.sh`    | Run test suites                  | `scripts/test_chainfinity.sh`    |
| `monitor_chainfinity.sh` | Monitor system health            | `scripts/monitor_chainfinity.sh` |
| `cleanup_chainfinity.sh` | Clean up resources               | `scripts/cleanup_chainfinity.sh` |
| `lint-all.sh`            | Code quality checks              | `scripts/lint-all.sh`            |

## Environment Setup

### env_setup.sh

Automates the complete environment setup for ChainFinity development.

**Command:**

```bash
./scripts/env_setup.sh [options]
```

**Options:**

| Flag               | Argument  | Default           | Description                                        |
| ------------------ | --------- | ----------------- | -------------------------------------------------- |
| `--project-dir`    | `DIR`     | Current directory | Set project directory                              |
| `--node-version`   | `VERSION` | 18                | Set Node.js version                                |
| `--python-version` | `VERSION` | 3.11              | Set Python version                                 |
| `--skip-docker`    | -         | false             | Skip Docker installation                           |
| `--skip-databases` | -         | false             | Skip database setup                                |
| `--environment`    | `ENV`     | development       | Set environment (development, staging, production) |
| `--help`           | -         | -                 | Show help message                                  |

**Examples:**

```bash
# Basic setup with defaults
./scripts/env_setup.sh

# Custom Python version
./scripts/env_setup.sh --python-version 3.10

# Skip Docker installation
./scripts/env_setup.sh --skip-docker

# Staging environment setup
./scripts/env_setup.sh --environment staging

# Full custom setup
./scripts/env_setup.sh \
  --project-dir /opt/chainfinity \
  --node-version 20 \
  --python-version 3.11 \
  --environment production
```

**What it does:**

1. Installs system dependencies (Node.js, Python, Docker)
2. Sets up Python virtual environment
3. Installs Python packages
4. Installs Node.js packages for all components
5. Sets up PostgreSQL and Redis
6. Creates and configures `.env` files
7. Runs database migrations

## Deployment Commands

### deploy_chainfinity.sh

Orchestrates deployment to different environments with backup and rollback capabilities.

**Command:**

```bash
./scripts/deploy_chainfinity.sh [options]
```

**Options:**

| Flag            | Argument | Default               | Description                     |
| --------------- | -------- | --------------------- | ------------------------------- |
| `--project-dir` | `DIR`    | Current directory     | Set project directory           |
| `--log-dir`     | `DIR`    | `./logs`              | Log directory                   |
| `--env-file`    | `FILE`   | `.env`                | Environment file                |
| `--environment` | `ENV`    | development           | Deployment environment          |
| `--backup-dir`  | `DIR`    | `./backups/TIMESTAMP` | Backup directory                |
| `--dry-run`     | -        | false                 | Perform dry run without changes |
| `--component`   | `NAME`   | all                   | Deploy specific component       |
| `--help`        | -        | -                     | Show help message               |

**Components:**

- `blockchain` - Smart contracts only
- `backend` - Backend API only
- `frontend` - Web frontend only
- `all` - All components (default)

**Examples:**

```bash
# Deploy to development
./scripts/deploy_chainfinity.sh --environment development

# Deploy backend only to staging
./scripts/deploy_chainfinity.sh \
  --environment staging \
  --component backend

# Production deployment with backup
./scripts/deploy_chainfinity.sh \
  --environment production \
  --backup-dir /backups/prod-$(date +%Y%m%d)

# Dry run (no actual changes)
./scripts/deploy_chainfinity.sh \
  --environment production \
  --dry-run

# Deploy with custom environment file
./scripts/deploy_chainfinity.sh \
  --environment staging \
  --env-file .env.staging
```

**Deployment Process:**

1. Validates environment configuration
2. Creates backup of current deployment
3. Builds Docker images
4. Runs database migrations
5. Deploys smart contracts (if needed)
6. Starts/updates services
7. Runs health checks
8. Generates deployment report

## Testing Commands

### test_chainfinity.sh

Runs comprehensive test suites across all components.

**Command:**

```bash
./scripts/test_chainfinity.sh [options]
```

**Options:**

| Flag                   | Argument | Default           | Description               |
| ---------------------- | -------- | ----------------- | ------------------------- |
| `--project-dir`        | `DIR`    | Current directory | Set project directory     |
| `--log-dir`            | `DIR`    | `./logs`          | Log directory             |
| `--report-dir`         | `DIR`    | `./test-reports`  | Test report directory     |
| `--timeout`            | `SEC`    | 300               | Test timeout in seconds   |
| `--no-parallel`        | -        | false             | Disable parallel testing  |
| `--coverage-threshold` | `NUM`    | 80                | Minimum code coverage (%) |
| `--component`          | `NAME`   | all               | Test specific component   |
| `--help`               | -        | -                 | Show help message         |

**Examples:**

```bash
# Run all tests
./scripts/test_chainfinity.sh

# Run backend tests only
./scripts/test_chainfinity.sh --component backend

# Run with higher coverage threshold
./scripts/test_chainfinity.sh --coverage-threshold 90

# Sequential testing (no parallel)
./scripts/test_chainfinity.sh --no-parallel

# Custom timeout and output
./scripts/test_chainfinity.sh \
  --timeout 600 \
  --report-dir ./coverage-reports \
  --component all
```

**Test Components:**

- Smart contract tests (Hardhat)
- Backend unit tests (pytest)
- Backend integration tests (pytest)
- Frontend component tests (Jest)
- E2E tests (Cypress)

## Monitoring Commands

### monitor_chainfinity.sh

Comprehensive monitoring for ChainFinity platform health and performance.

**Command:**

```bash
./scripts/monitor_chainfinity.sh [options]
```

**Options:**

| Flag                | Argument  | Default               | Description                         |
| ------------------- | --------- | --------------------- | ----------------------------------- |
| `--config`          | `FILE`    | `monitor_config.json` | Configuration file path             |
| `--log-dir`         | `DIR`     | `./logs`              | Log directory                       |
| `--alert-threshold` | `NUM`     | 80                    | Alert threshold percentage          |
| `--check-interval`  | `SEC`     | 300                   | Check interval in seconds           |
| `--report-interval` | `SEC`     | 86400                 | Report interval in seconds          |
| `--slack-webhook`   | `URL`     | -                     | Slack webhook URL for notifications |
| `--email`           | `ADDRESS` | -                     | Email address for notifications     |
| `--help`            | -         | -                     | Show help message                   |

**Examples:**

```bash
# Basic monitoring with defaults
./scripts/monitor_chainfinity.sh

# Custom alert threshold and intervals
./scripts/monitor_chainfinity.sh \
  --alert-threshold 90 \
  --check-interval 60 \
  --report-interval 3600

# With Slack notifications
./scripts/monitor_chainfinity.sh \
  --slack-webhook https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Custom configuration
./scripts/monitor_chainfinity.sh \
  --config /etc/chainfinity/monitor.json \
  --log-dir /var/log/chainfinity
```

**Monitored Metrics:**

- System resources (CPU, memory, disk)
- Docker container health
- Database connections and performance
- Redis cache hit rate
- API response times
- Blockchain node status
- Error rates

## Utility Commands

### run_chainfinity.sh

Start all ChainFinity services locally.

**Command:**

```bash
./scripts/run_chainfinity.sh
```

**What it does:**

1. Starts PostgreSQL and Redis
2. Starts blockchain node (Hardhat)
3. Starts backend API
4. Starts frontend development server

**Example:**

```bash
# Start all services
./scripts/run_chainfinity.sh

# View logs
tail -f logs/backend.log
tail -f logs/frontend.log
```

### cleanup_chainfinity.sh

Clean up temporary files, build artifacts, and stop services.

**Command:**

```bash
./scripts/cleanup_chainfinity.sh [options]
```

**Options:**

- `--full` - Full cleanup including node_modules and venv
- `--logs` - Clean up log files
- `--cache` - Clear cache files

**Examples:**

```bash
# Basic cleanup
./scripts/cleanup_chainfinity.sh

# Full cleanup
./scripts/cleanup_chainfinity.sh --full

# Clean logs only
./scripts/cleanup_chainfinity.sh --logs
```

### lint-all.sh

Run linting and code quality checks across all components.

**Command:**

```bash
./scripts/lint-all.sh
```

**What it checks:**

- Python: Black, Flake8, mypy
- JavaScript/TypeScript: ESLint, Prettier
- Solidity: Solhint, Prettier
- YAML: yamllint

**Example:**

```bash
# Run all linters
./scripts/lint-all.sh

# Auto-fix issues
./scripts/lint-all.sh --fix
```

## Backend Management Commands

### Database Migrations

Using Alembic for database schema management.

**Commands:**

```bash
cd code/backend

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

### Start Backend Server

**Development:**

```bash
cd code/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production:**

```bash
cd code/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Blockchain Commands

### Hardhat CLI

**Commands:**

```bash
cd code/blockchain

# Compile contracts
npx hardhat compile

# Run tests
npx hardhat test

# Run specific test file
npx hardhat test test/CrossChainManager.test.js

# Start local node
npx hardhat node

# Deploy contracts
npx hardhat run scripts/deploy.js --network localhost

# Verify contract on Etherscan
npx hardhat verify --network mainnet CONTRACT_ADDRESS

# Clean build artifacts
npx hardhat clean
```

## Docker Commands

### Container Management

```bash
# Start all services
docker-compose -f code/backend/docker-compose.yml up -d

# Stop all services
docker-compose -f code/backend/docker-compose.yml down

# View logs
docker-compose -f code/backend/docker-compose.yml logs -f

# Restart specific service
docker-compose -f code/backend/docker-compose.yml restart api

# Scale services
docker-compose -f code/backend/docker-compose.yml up -d --scale api=3

# Check service status
docker-compose -f code/backend/docker-compose.yml ps
```

## Kubernetes Commands

### Kubectl Operations

```bash
# Deploy to Kubernetes
kubectl apply -f infrastructure/kubernetes/

# Check pod status
kubectl get pods -n chainfinity

# View logs
kubectl logs -f -n chainfinity deployment/chainfinity-api

# Port forward to service
kubectl port-forward -n chainfinity svc/chainfinity-api 8000:8000

# Scale deployment
kubectl scale deployment chainfinity-api --replicas=3 -n chainfinity

# Update image
kubectl set image deployment/chainfinity-api \
  api=chainfinity/api:v2.0.0 -n chainfinity
```

## Environment Variables for Scripts

Set these environment variables to customize script behavior:

```bash
# Global settings
export CHAINFINITY_HOME=/opt/chainfinity
export CHAINFINITY_ENV=production

# Logging
export LOG_LEVEL=INFO
export LOG_DIR=/var/log/chainfinity

# Notifications
export SLACK_WEBHOOK_URL=https://hooks.slack.com/...
export ALERT_EMAIL=admin@example.com
```

## Troubleshooting CLI Issues

| Issue                    | Solution                                           |
| ------------------------ | -------------------------------------------------- |
| **Permission denied**    | Make scripts executable: `chmod +x scripts/*.sh`   |
| **Command not found**    | Ensure script is run from project root             |
| **Docker not running**   | Start Docker daemon: `sudo systemctl start docker` |
| **Port already in use**  | Check with `lsof -i :8000` and kill process        |
| **Missing dependencies** | Run `./scripts/env_setup.sh`                       |

## Next Steps

- Review [API Reference](./API.md) for API endpoints
- Check [Examples](./examples/) for usage examples
- See [Troubleshooting](./TROUBLESHOOTING.md) for common issues

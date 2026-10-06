# ChainFinity Code

This directory contains the core application code for ChainFinity, a blockchain-based financial platform designed for institutional-grade portfolio management, risk assessment, market analytics, and DeFi protocol integration. The code is organized into three primary areas: the FastAPI backend, machine learning models for financial intelligence, and the blockchain smart contract layer.

## Directory Structure

```
code/
├── backend/           # FastAPI backend services and API layer
├── ai_models/         # Layered ML package: core, preprocessing, models, cli, tests
└── blockchain/        # Solidity smart contracts and blockchain tooling
```

## Backend

The `backend/` directory houses the main application server built with Python and FastAPI. It is a production-ready, enterprise-grade backend emphasizing financial industry standards, comprehensive security, regulatory compliance, and multi-chain blockchain integration.

### Key Components

| Directory     | Purpose                                                                                          |
| ------------- | ------------------------------------------------------------------------------------------------ |
| `app/`        | FastAPI application factory, route registration, and core app setup                              |
| `config/`     | Environment-specific configuration, security policies, and feature flags                         |
| `services/`   | Core business logic for portfolios, transactions, risk assessment, and blockchain interactions   |
| `models/`     | SQLAlchemy ORM models for users, portfolios, transactions, compliance records, and risk metrics  |
| `schemas/`    | Pydantic request/response validation schemas                                                     |
| `routes/`     | API endpoint definitions organized by domain (auth, users, portfolios, transactions, compliance) |
| `middleware/` | Custom middleware for authentication, rate limiting, logging, and CORS                           |
| `exceptions/` | Custom exception classes and global error handlers                                               |
| `monitoring/` | Prometheus metrics, structured logging, and health check endpoints                               |
| `migrations/` | Alembic database migration scripts                                                               |
| `nginx/`      | Nginx reverse proxy and load balancer configuration                                              |
| `scripts/`    | Operational and utility scripts                                                                  |
| `tests/`      | Comprehensive test suite including unit, integration, and functional tests                       |

### Notable Features

- **Enterprise Security**: JWT authentication with refresh tokens, TOTP multi-factor authentication, role-based access control, sliding window rate limiting, field-level PII encryption, bcrypt password hashing, and account lockout protection
- **Financial Compliance**: KYC/AML integration with identity and document verification, sanctions screening, PEP checks, real-time transaction monitoring, suspicious activity detection, and regulatory reporting
- **Risk Management**: Portfolio risk metrics, real-time risk scoring, position limits and controls, stress testing capabilities, and risk-based alerting
- **Blockchain Integration**: Multi-chain support via Web3.py for Ethereum, Polygon, and BSC networks; smart contract interaction and transaction management
- **Scalable Infrastructure**: Async database operations with SQLAlchemy, Redis caching and session management, connection pooling, Docker support, and horizontal scaling via Docker Compose

### Running the Backend

Local development:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m uvicorn main:app --reload
```

With Docker:

```bash
cd backend
docker-compose up -d
```

Services included in Docker Compose:

| Service    | Purpose                         |
| ---------- | ------------------------------- |
| API        | ChainFinity backend application |
| PostgreSQL | Primary transactional database  |
| Redis      | Cache and session store         |
| Nginx      | Reverse proxy and load balancer |
| Prometheus | Metrics collection              |
| Grafana    | Monitoring dashboards           |

For full backend documentation, see [backend/README.md](backend/README.md).

## AI Models

The `ai_models/` package contains the machine learning stack behind ChainFinity's predictive analytics and risk detection. It is imported as `ai_models` and integrated with the backend through `backend/services/ai`. See [ai_models/README.md](ai_models/README.md) for the full package guide.

### Layout

| Path                            | Purpose                                                                                 |
| ------------------------------- | --------------------------------------------------------------------------------------- |
| `ai_models/core/`               | Lazy TensorFlow loading, versioned and checksummed artifact persistence, model registry |
| `ai_models/preprocessing/`      | OHLCV validation, imputation, outlier handling, technical features, sequences, scaling  |
| `ai_models/models/volatility/`  | LSTM volatility forecaster with Monte Carlo intervals and an EWMA fallback              |
| `ai_models/models/correlation/` | LSTM correlation predictor with a Ledoit-Wolf shrinkage fallback                        |
| `ai_models/models/exploit/`     | Isolation forest and LSTM autoencoder exploit detector                                  |
| `ai_models/models/liquidity/`   | Rule-based liquidity crisis detector (TVL drain, spreads, depeg, contagion)             |
| `ai_models/models/smart_money/` | Wallet clustering, scoring, PageRank centrality and movement signals                    |
| `ai_models/cli.py`              | `python -m ai_models train <model>` and `python -m ai_models inspect`                   |
| `ai_models/tests/`              | Unit tests that run without a GPU or network access                                     |

### Backend integration

| Endpoint                                      | Description                                                     |
| --------------------------------------------- | --------------------------------------------------------------- |
| `GET  /api/v1/ai/status`                      | Which models are trained and which are running in fallback mode |
| `POST /api/v1/ai/volatility`                  | Volatility forecast for a symbol or supplied prices             |
| `POST /api/v1/ai/correlation`                 | Predicted correlation matrix                                    |
| `POST /api/v1/ai/exploit-detection`           | Exploit risk scores and alerts for on-chain observations        |
| `POST /api/v1/ai/liquidity`                   | Liquidity crisis scores and alerts                              |
| `POST /api/v1/ai/smart-money`                 | Wallet profiles, signals and cross-chain flows                  |
| `GET  /api/v1/ai/portfolio/{id}/insights`     | Volatility forecasts and correlations for a portfolio's assets  |
| `POST /api/v1/ai/models/{name}/train` (admin) | Start a background training job                                 |
| `GET  /api/v1/ai/jobs`, `/jobs/{id}` (admin)  | Training job status                                             |
| `POST /api/v1/ai/models/reload` (admin)       | Reload artifacts from disk                                      |

The risk service (`/api/v1/risk/assess`, `/metrics`, `/monitor`) uses the same models: forecast volatility feeds the overall risk score and recommendations, and predicted correlations drive the correlation matrix and drift alerts. Without trained artifacts every model degrades to its documented fallback, and responses report the model that produced them.

### Training and deployment

```bash
cd code
pip install -r ai_models/requirements-ml.txt
python -m ai_models train volatility --data prices.csv --artifacts-dir backend/ai_artifacts
python -m ai_models inspect --artifacts-dir backend/ai_artifacts
```

The backend loads artifacts from `AI_ARTIFACTS_DIR` (default `ai_artifacts` inside the backend directory) at startup. Docker images are built from the `code/` directory so that `ai_models` is packaged with the backend; set `INSTALL_ML=false` to build without TensorFlow.

## Blockchain

The `blockchain/` directory contains the Solidity smart contract layer and blockchain tooling for ChainFinity's on-chain operations. It supports the Ethereum ecosystem using Hardhat as the development framework.

### Key Components

| Directory/File      | Purpose                                                                                          |
| ------------------- | ------------------------------------------------------------------------------------------------ |
| `contracts/`        | Solidity smart contracts for portfolio management, asset custody, and DeFi integrations          |
| `subgraph/`         | The Graph protocol subgraph configuration for indexing on-chain events and making them queryable |
| `test/`             | Hardhat test suite using Waffle/Chai for contract validation                                     |
| `hardhat.config.js` | Hardhat network configuration for Ethereum, Polygon, and BSC deployments                         |
| `package.json`      | Node.js dependencies including Hardhat, OpenZeppelin contracts, Waffle, and Chai                 |

### Technology Stack

| Component        | Technology             |
| ---------------- | ---------------------- |
| Language         | Solidity 0.8.19+       |
| Framework        | Hardhat / Foundry      |
| Networks         | Ethereum, Polygon, BSC |
| Contract Library | OpenZeppelin Contracts |
| Testing          | Waffle + Chai          |
| Indexing         | The Graph (subgraph)   |

### Working with Smart Contracts

Compile contracts:

```bash
cd blockchain
npm install
npx hardhat compile
```

Run tests:

```bash
npx hardhat test
```

Deploy to a network:

```bash
npx hardhat run scripts/deploy.js --network <network-name>
```

## Technology Stack Summary

| Layer          | Technology                                |
| -------------- | ----------------------------------------- |
| Backend        | Python 3.11+, FastAPI 0.104.1             |
| Database       | PostgreSQL 15+ with async SQLAlchemy      |
| Cache          | Redis 7+                                  |
| Authentication | JWT with refresh tokens, TOTP MFA         |
| Blockchain     | Solidity 0.8.19+, Hardhat, Web3.py        |
| Networks       | Ethereum, Polygon, BSC                    |
| ML/AI          | TensorFlow, PyTorch, Pandas, NumPy        |
| Monitoring     | Prometheus, Grafana, structured logging   |
| Deployment     | Docker, Docker Compose, Nginx             |
| Testing        | pytest (backend), Waffle/Chai (contracts) |

## Integration Between Components

The three code areas work together as an integrated platform:

1. The **backend** serves as the central API layer, handling user authentication, portfolio management, compliance workflows, and risk assessments. It communicates with the blockchain layer via Web3.py to read on-chain data and submit transactions.

2. The **AI models** are called by backend services during portfolio analysis, risk evaluation, and market monitoring operations. Predictions from the exploit detection, volatility forecasting, and liquidity crisis models feed directly into the risk scoring engine and alerting system.

3. The **blockchain** layer provides the trustless, on-chain settlement and custody layer. Smart contracts manage asset allocations and DeFi interactions, while the subgraph indexes events for efficient querying by the backend.

## Testing

Each subdirectory maintains its own test suite:

| Component       | Test Location      | Framework               |
| --------------- | ------------------ | ----------------------- |
| Backend         | `backend/tests/`   | pytest                  |
| Smart Contracts | `blockchain/test/` | Hardhat + Waffle + Chai |

Run all backend tests:

```bash
cd backend
pytest
```

Run contract tests:

```bash
cd blockchain
npx hardhat test
```

## Environment Setup

Before running any component, copy and configure the environment files:

```bash
cd backend && cp .env.example .env
cd ../blockchain && cp .env.example .env  # if available
```

Required environment variables include database URIs, Redis connection strings, JWT secrets, blockchain RPC endpoints, and API keys for external market data providers.

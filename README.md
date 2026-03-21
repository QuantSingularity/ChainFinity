# ChainFinity

![CI/CD Status](https://img.shields.io/github/actions/workflow/status/quantsingularity/ChainFinity/cicd.yml?branch=main&label=CI/CD&logo=github)
[![Test Coverage](https://img.shields.io/badge/coverage-79%25-yellow)](https://github.com/quantsingularity/ChainFinity/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Cross-Chain DeFi Risk Management Platform

ChainFinity is an advanced cross-chain DeFi risk management platform that leverages AI and quantitative models to analyze, predict, and mitigate risks across multiple blockchain networks.

<div align="center">
  <img src="docs/images/ChainFinity_dashboard.bmp" alt="ChainFinity Dashboard" width="80%">
</div>

> **Note**: This project is under active development. Features and functionalities are continuously being enhanced to improve risk management capabilities and cross-chain interoperability.

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Installation](#installation)
- [Deployment](#deployment)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Overview

ChainFinity provides comprehensive risk management solutions for DeFi protocols and users operating across multiple blockchain networks. By combining AI-driven predictive analytics with cross-chain communication protocols, ChainFinity enables real-time risk assessment, automated hedging strategies, and optimized capital efficiency across the fragmented DeFi ecosystem.

## Project Structure

The project is organized into several main components:

```
ChainFinity/
├── code/                   # Core backend logic, services, and shared utilities
├── docs/                   # Project documentation
├── infrastructure/         # DevOps, deployment, and infra-related code
├── mobile-frontend/        # Mobile application
├── web-frontend/           # Web dashboard
├── scripts/                # Automation, setup, and utility scripts
├── LICENSE                 # License information
├── README.md               # Project overview and instructions
└── tools/                  # Formatter configs, linting tools, and dev utilities
```

## Key Features

### Cross-Chain Risk Analytics

| Feature                        | Description                                                                |
| :----------------------------- | :------------------------------------------------------------------------- |
| **Multi-Chain Monitoring**     | Real-time data collection and analysis across 15+ blockchain networks      |
| **Risk Correlation Matrix**    | Identification of cross-chain risk correlations and contagion paths        |
| **Protocol Risk Scoring**      | Comprehensive risk assessment of DeFi protocols across multiple dimensions |
| **Liquidity Analysis**         | Deep liquidity analysis across DEXs and lending platforms                  |
| **Bridge Security Monitoring** | Risk assessment of cross-chain bridges and wrapped assets                  |

### AI-Powered Prediction Models

| Feature                             | Description                                              |
| :---------------------------------- | :------------------------------------------------------- |
| **Market Volatility Forecasting**   | LSTM-based models for predicting price volatility        |
| **Smart Money Tracking**            | AI analysis of whale wallet movements across chains      |
| **Protocol Exploit Prediction**     | Anomaly detection for potential security vulnerabilities |
| **Liquidity Crisis Alerts**         | Early warning system for potential liquidity crises      |
| **Correlation Breakdown Detection** | Identification of unusual correlation patterns           |

### Automated Risk Management

| Feature                           | Description                                               |
| :-------------------------------- | :-------------------------------------------------------- |
| **Cross-Chain Hedging**           | Automated position hedging across multiple networks       |
| **Dynamic Collateral Management** | Optimal collateral allocation based on risk models        |
| **Liquidation Protection**        | Proactive measures to prevent liquidations                |
| **Flash Loan Defense**            | Protection against flash loan attack vectors              |
| **MEV Protection**                | Strategies to mitigate maximal extractable value exposure |

### Cross-Chain Infrastructure

| Feature                  | Description                                                          |
| :----------------------- | :------------------------------------------------------------------- |
| **CCIP Integration**     | Chainlink Cross-Chain Interoperability Protocol for secure messaging |
| **Multi-Chain Oracles**  | Decentralized price feeds across all supported networks              |
| **Gas Optimization**     | Efficient cross-chain transactions with optimal gas usage            |
| **Unified Liquidity**    | Aggregated liquidity access across multiple DEXs and chains          |
| **Cross-Chain Identity** | Unified identity and reputation system across networks               |

## Tech Stack

**Blockchain**

- Solidity 0.8 for smart contracts
- Chainlink CCIP for cross-chain communication
- Hardhat for development and testing
- The Graph for blockchain data indexing

**Backend**

- FastAPI for high-performance API endpoints
- NumPy and SciPy for numerical computations
- Pandas for data manipulation and analysis
- WebSocket for real-time data streaming

**AI/ML**

- TensorFlow 2.12 for deep learning models
- LSTM Networks for time series prediction
- Prophet for trend forecasting
- Scikit-learn for statistical models

**Frontend**

- React 18 with TypeScript for UI
- Recharts for data visualization
- Ethers.js 6 for blockchain interaction
- Material-UI for component library

**Database**

- TimescaleDB for time-series data
- Redis for caching and real-time data
- PostgreSQL for relational data
- IPFS for decentralized storage

**Infrastructure**

- Kubernetes for container orchestration
- Terraform for infrastructure as code
- AWS EKS for managed Kubernetes
- ArgoCD for GitOps deployment

## Architecture

```
ChainFinity/
├── Frontend Layer
│   ├── Risk Dashboard
│   ├── Analytics Interface
│   ├── Strategy Builder
│   └── Admin Panel
├── API Gateway
│   ├── Authentication
│   ├── Rate Limiting
│   ├── Request Routing
│   └── Response Caching
├── Risk Engine
│   ├── Risk Calculator
│   ├── Position Monitor
│   ├── Alert Generator
│   └── Strategy Executor
├── AI Models
│   ├── Volatility Predictor
│   ├── Correlation Analyzer
│   ├── Anomaly Detector
│   └── Trend Forecaster
├── Quant Library
│   ├── Risk Metrics
│   ├── Portfolio Optimization
│   ├── Hedging Algorithms
│   └── Backtesting Engine
├── Cross-Chain Manager
│   ├── CCIP Integration
│   ├── Bridge Monitor
│   ├── Gas Optimizer
│   └── Transaction Router
└── Data Layer
    ├── TimescaleDB
    ├── Redis Cache
    ├── The Graph Indexers
    └── IPFS Storage
```

## Installation

```bash
# Clone repository
git clone https://github.com/quantsingularity/ChainFinity.git
cd ChainFinity

# Install dependencies
cd code/blockchain && npm install
cd ../backend && pip install -r requirements.txt
cd ../frontend && npm install

# Configure environment
cp .env.example .env
# Add your API keys and chain configurations

# Start services
docker-compose -f infrastructure/docker-compose.dev.yml up -d
cd code/blockchain && npx hardhat node
cd ../backend && uvicorn app:app --reload
cd ../frontend && npm start
```

For a quick setup using the provided script:

```bash
# Clone and setup
git clone https://github.com/quantsingularity/ChainFinity.git
cd ChainFinity
./setup_chainfinity_env.sh
./run_chainfinity.sh
```

## Deployment

### Local Development

```bash
# Start all services locally
docker-compose up -d
```

### Staging Environment

```bash
# Deploy to staging
./deploy.sh staging
```

### Production Environment

```bash
# Deploy to production
./deploy.sh production
```

## Testing

The project maintains comprehensive test coverage across all components to ensure reliability and security.

### Test Coverage

| Component           | Coverage | Status |
| ------------------- | -------- | ------ |
| Smart Contracts     | 85%      | ✅     |
| Risk Engine         | 82%      | ✅     |
| Cross-Chain Manager | 78%      | ✅     |
| AI Models           | 75%      | ✅     |
| Backend Services    | 80%      | ✅     |
| Frontend Components | 72%      | ✅     |
| Overall             | 79%      | ✅     |

### Smart Contract Tests

| Test Type          | Description                  |
| :----------------- | :--------------------------- |
| Unit tests         | For all contract functions   |
| Integration tests  | For cross-chain interactions |
| Security tests     | Using Slither and Mythril    |
| Optimization tests | For gas usage                |

### Backend Tests

| Test Type                     | Description                              |
| :---------------------------- | :--------------------------------------- |
| API endpoint tests            | To ensure correct routing and response   |
| Service layer unit tests      | For core business logic                  |
| Database integration tests    | To verify data persistence and retrieval |
| WebSocket communication tests | For real-time data streaming             |

### AI Model Tests

| Test Type                          | Description                              |
| :--------------------------------- | :--------------------------------------- |
| Model accuracy validation          | To ensure predictive power               |
| Prediction performance tests       | To check speed and efficiency            |
| Data pipeline tests                | To verify data flow and transformation   |
| Cross-chain data consistency tests | To ensure data integrity across networks |

### Frontend Tests

| Test Type                  | Description                                  |
| :------------------------- | :------------------------------------------- |
| Component tests            | With React Testing Library for UI elements   |
| Integration tests          | With Cypress for feature flows               |
| End-to-end user flow tests | To verify complete user journeys             |
| Web3 integration tests     | For blockchain connectivity and transactions |

### Running Tests

```bash
# Run smart contract tests
cd code/blockchain
npx hardhat test

# Run backend tests
cd code/backend
pytest

# Run frontend tests
cd code/frontend
npm test

# Run all tests
./run_all_tests.sh
```

## CI/CD Pipeline

ChainFinity uses GitHub Actions for continuous integration and deployment:

| Stage                | Control Area                    | Institutional-Grade Detail                                                              |
| :------------------- | :------------------------------ | :-------------------------------------------------------------------------------------- |
| **Formatting Check** | Change Triggers                 | Enforced on all `push` and `pull_request` events to `main` and `develop`                |
|                      | Manual Oversight                | On-demand execution via controlled `workflow_dispatch`                                  |
|                      | Source Integrity                | Full repository checkout with complete Git history for auditability                     |
|                      | Python Runtime Standardization  | Python 3.10 with deterministic dependency caching                                       |
|                      | Backend Code Hygiene            | `autoflake` to detect unused imports/variables using non-mutating diff-based validation |
|                      | Backend Style Compliance        | `black --check` to enforce institutional formatting standards                           |
|                      | Non-Intrusive Validation        | Temporary workspace comparison to prevent unauthorized source modification              |
|                      | Node.js Runtime Control         | Node.js 18 with locked dependency installation via `npm ci`                             |
|                      | Web Frontend Formatting Control | Prettier checks for web-facing assets                                                   |
|                      | Mobile Frontend Formatting      | Prettier enforcement for mobile application codebases                                   |
|                      | Documentation Governance        | Repository-wide Markdown formatting enforcement                                         |
|                      | Infrastructure Configuration    | Prettier validation for YAML/YML infrastructure definitions                             |
|                      | Compliance Gate                 | Any formatting deviation fails the pipeline and blocks merge                            |

## Documentation

For detailed documentation, please refer to the following resources:

| Document                    | Path                 | Description                                                 |
| :-------------------------- | :------------------- | :---------------------------------------------------------- |
| **README**                  | `README.md`          | High-level overview, project scope, and quickstart          |
| **API Reference**           | `API.md`             | Detailed documentation for all API endpoints                |
| **CLI Reference**           | `CLI.md`             | Command-line interface usage, commands, and examples        |
| **Installation Guide**      | `INSTALLATION.md`    | Step-by-step installation and environment setup             |
| **User Guide**              | `USAGE.md`           | Comprehensive guide for end-users, workflows, and examples  |
| **Contributing Guidelines** | `CONTRIBUTING.md`    | Contribution process, coding standards, and PR requirements |
| **Architecture Overview**   | `ARCHITECTURE.md`    | System architecture, components, and design rationale       |
| **Configuration Guide**     | `CONFIGURATION.md`   | Configuration options, environment variables, and tuning    |
| **Feature Matrix**          | `FEATURE_MATRIX.md`  | Feature capabilities, coverage, and roadmap alignment       |
| **Troubleshooting**         | `TROUBLESHOOTING.md` | Common issues, diagnostics, and remediation steps           |

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

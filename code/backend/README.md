# ChainFinity Production Backend

A production-ready, enterprise-grade backend for the ChainFinity cryptocurrency portfolio management platform. Built with financial industry standards, comprehensive security, and regulatory compliance.

## Architecture Overview

### Core Features

| Feature                        | Description                                                       |
| :----------------------------- | :---------------------------------------------------------------- |
| **Enterprise Security**        | JWT authentication, MFA, field-level encryption, rate limiting    |
| **Financial Compliance**       | KYC/AML integration, transaction monitoring, regulatory reporting |
| **Risk Management**            | Real-time risk assessment, portfolio analytics, alert system      |
| **Blockchain Integration**     | Multi-chain support (Ethereum, Polygon, BSC)                      |
| **Scalable Infrastructure**    | Async database operations, Redis caching, connection pooling      |
| **Monitoring & Observability** | Comprehensive logging, metrics, health checks                     |

### Technology Stack

| Component          | Technology                                     |
| :----------------- | :--------------------------------------------- |
| **Framework**      | FastAPI 0.104.1                                |
| **Database**       | PostgreSQL with async SQLAlchemy               |
| **Cache**          | Redis for session management and rate limiting |
| **Authentication** | JWT with refresh tokens, TOTP MFA              |
| **Blockchain**     | Web3.py for Ethereum ecosystem                 |
| **Monitoring**     | Prometheus metrics, structured logging         |
| **Deployment**     | Docker with production-ready configuration     |

## Prerequisites

The following software is required to run the backend:

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (for containerized deployment)

## Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd chainfinity_backend_production

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 3. Database Setup

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run database migrations
alembic upgrade head
```

### 4. Run Application

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Docker Deployment

### Full Stack Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Scale API instances
docker-compose up -d --scale api=3
```

### Services Included

| Service        | Purpose                         |
| :------------- | :------------------------------ |
| **API**        | ChainFinity backend application |
| **PostgreSQL** | Primary database                |
| **Redis**      | Cache and session store         |
| **Nginx**      | Reverse proxy and load balancer |
| **Prometheus** | Metrics collection              |
| **Grafana**    | Monitoring dashboard            |

## Database Schema

### Core Models

| Model            | Description                                          |
| :--------------- | :--------------------------------------------------- |
| **Users**        | Enhanced user management with KYC and risk profiling |
| **Transactions** | Comprehensive transaction tracking with compliance   |
| **Portfolios**   | Multi-asset portfolio management                     |
| **Compliance**   | Audit logs, regulatory reporting, AML checks         |
| **Risk**         | Risk assessments, metrics, and alerting              |
| **Blockchain**   | Network management and smart contract integration    |

### Key Features

| Feature          | Description                                   |
| :--------------- | :-------------------------------------------- |
| **Audit Trail**  | Complete audit logging for all operations     |
| **Soft Deletes** | Data retention with soft delete functionality |
| **Encryption**   | Field-level encryption for sensitive data     |
| **Versioning**   | Optimistic locking for data consistency       |

## Security Features

### Authentication & Authorization

| Feature            | Details                            |
| :----------------- | :--------------------------------- |
| **Tokens**         | JWT access and refresh tokens      |
| **MFA**            | Multi-factor authentication (TOTP) |
| **Access Control** | Role-based access control          |
| **Sessions**       | Session management with Redis      |
| **Passwords**      | Password strength validation       |
| **Lockout**        | Account lockout protection         |

### API Security

| Feature           | Details                             |
| :---------------- | :---------------------------------- |
| **Rate Limiting** | Sliding window rate limiting        |
| **Validation**    | Request validation and sanitization |
| **Headers**       | Security headers (HSTS, CSP, etc.)  |
| **CORS**          | CORS configuration                  |
| **Input**         | Input validation with Pydantic      |

### Data Protection

| Feature      | Details                          |
| :----------- | :------------------------------- |
| **PII**      | Field-level encryption for PII   |
| **Hashing**  | Secure password hashing (bcrypt) |
| **API Keys** | API key management               |
| **Logging**  | Audit logging for all operations |

## Compliance & Risk Management

### KYC/AML Integration

| Feature        | Details                                 |
| :------------- | :-------------------------------------- |
| **Identity**   | Identity verification workflows         |
| **Documents**  | Document verification                   |
| **Screening**  | Sanctions screening                     |
| **PEP Checks** | PEP (Politically Exposed Person) checks |
| **Monitoring** | Ongoing monitoring                      |

### Transaction Monitoring

| Feature       | Details                        |
| :------------ | :----------------------------- |
| **Analysis**  | Real-time transaction analysis |
| **Detection** | Suspicious activity detection  |
| **Alerting**  | Threshold-based alerting       |
| **Patterns**  | Pattern recognition            |
| **Reporting** | Regulatory reporting           |

### Risk Assessment

| Feature      | Details                      |
| :----------- | :--------------------------- |
| **Metrics**  | Portfolio risk metrics       |
| **Scoring**  | Real-time risk scoring       |
| **Controls** | Position limits and controls |
| **Testing**  | Stress testing capabilities  |
| **Alerting** | Risk-based alerting          |

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Current user info

### User Management

- `GET /api/v1/users/profile` - User profile
- `PUT /api/v1/users/profile` - Update profile
- `POST /api/v1/users/kyc` - Submit KYC
- `GET /api/v1/users/risk-profile` - Risk assessment

### Portfolio Management

- `GET /api/v1/portfolios` - List portfolios
- `POST /api/v1/portfolios` - Create portfolio
- `GET /api/v1/portfolios/{id}` - Portfolio details
- `PUT /api/v1/portfolios/{id}` - Update portfolio

### Transactions

- `GET /api/v1/transactions` - List transactions
- `GET /api/v1/transactions/{id}` - Transaction details
- `POST /api/v1/transactions/analyze` - Risk analysis

### Compliance

- `GET /api/v1/compliance/checks` - Compliance status
- `GET /api/v1/compliance/audit-logs` - Audit trail
- `POST /api/v1/compliance/reports` - Generate reports

## Monitoring & Observability

### Health Checks

- `GET /health` - Application health
- Database connectivity check
- Redis connectivity check
- External service status

### Metrics

- Request/response metrics
- Database performance
- Cache hit rates
- Business metrics
- Error rates and latency

### Logging

- Structured JSON logging
- Request/response logging
- Security event logging
- Performance logging
- Error tracking

## Configuration

### Environment Variables

Key configuration options:

```bash
# Application
APP_NAME=ChainFinity API
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
REDIS_URL=redis://host:port/db

# Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
RATE_LIMIT_PER_MINUTE=60

# Blockchain
ETH_RPC_URL=https://mainnet.infura.io/v3/PROJECT_ID
ETHERSCAN_API_KEY=your-api-key

# Compliance
KYC_ENABLED=true
AML_ENABLED=true
TRANSACTION_MONITORING_ENABLED=true
```

## Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

### Test Categories

- Unit tests for services and utilities
- Integration tests for API endpoints
- Database tests with test fixtures
- Security tests for authentication
- Performance tests for critical paths

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

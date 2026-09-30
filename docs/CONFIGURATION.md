# ChainFinity Configuration Guide

This document describes all configuration options for ChainFinity components, including environment variables, configuration files, and network settings.

## Configuration Overview

ChainFinity uses environment variables for configuration across all components. Each component has its own `.env` file:

- **Backend**: `code/backend/.env`
- **Blockchain**: `code/blockchain/.env`
- **Web Frontend**: `web-frontend/.env`
- **Mobile Frontend**: `mobile-frontend/.env`

## Backend Configuration

### Application Settings

| Option            | Type    | Default           | Description                                         | Where to set |
| ----------------- | ------- | ----------------- | --------------------------------------------------- | ------------ |
| `APP_NAME`        | string  | "ChainFinity API" | Application name displayed in API docs              | env file     |
| `APP_VERSION`     | string  | "2.0.0"           | Application version                                 | env file     |
| `APP_DESCRIPTION` | string  | -                 | API description                                     | env file     |
| `ENVIRONMENT`     | enum    | "development"     | Environment: `development`, `staging`, `production` | env file     |
| `DEBUG`           | boolean | false             | Enable debug mode (detailed errors)                 | env file     |
| `HOST`            | string  | "0.0.0.0"         | Server bind address                                 | env file     |
| `PORT`            | integer | 8000              | Server port                                         | env file     |
| `WORKERS`         | integer | 4                 | Number of worker processes (production only)        | env file     |

**Example:**

```bash
APP_NAME=ChainFinity API
APP_VERSION=2.0.0
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000
WORKERS=4
```

### API Configuration

| Option          | Type   | Default   | Description                  | Where to set |
| --------------- | ------ | --------- | ---------------------------- | ------------ |
| `API_V1_PREFIX` | string | "/api/v1" | API version 1 URL prefix     | env file     |
| `DOCS_URL`      | string | "/docs"   | Swagger UI documentation URL | env file     |
| `REDOC_URL`     | string | "/redoc"  | ReDoc documentation URL      | env file     |

### Database Configuration

| Option              | Type    | Default | Description                       | Where to set |
| ------------------- | ------- | ------- | --------------------------------- | ------------ |
| `DATABASE_URL`      | string  | -       | PostgreSQL connection URL (async) | env file     |
| `DATABASE_READ_URL` | string  | -       | Read replica URL (optional)       | env file     |
| `DB_POOL_SIZE`      | integer | 20      | Connection pool size              | env file     |
| `DB_MAX_OVERFLOW`   | integer | 30      | Max overflow connections          | env file     |
| `DB_POOL_TIMEOUT`   | integer | 30      | Connection timeout (seconds)      | env file     |
| `DB_POOL_RECYCLE`   | integer | 3600    | Connection recycle time (seconds) | env file     |
| `DB_ECHO`           | boolean | false   | Log all SQL statements            | env file     |
| `DB_ECHO_POOL`      | boolean | false   | Log connection pool events        | env file     |

**Connection String Format:**

```bash
DATABASE_URL=postgresql+asyncpg://username:password@host:port/database
# Example:
DATABASE_URL=postgresql+asyncpg://postgres:mypassword@localhost:5432/chainfinity
```

### Redis Configuration

| Option                         | Type    | Default | Description                  | Where to set |
| ------------------------------ | ------- | ------- | ---------------------------- | ------------ |
| `REDIS_URL`                    | string  | -       | Redis connection URL         | env file     |
| `REDIS_PASSWORD`               | string  | -       | Redis password (if required) | env file     |
| `REDIS_DB`                     | integer | 0       | Redis database number        | env file     |
| `REDIS_MAX_CONNECTIONS`        | integer | 20      | Maximum connections in pool  | env file     |
| `REDIS_SOCKET_TIMEOUT`         | integer | 5       | Socket timeout (seconds)     | env file     |
| `REDIS_SOCKET_CONNECT_TIMEOUT` | integer | 5       | Connect timeout (seconds)    | env file     |
| `CACHE_TTL`                    | integer | 3600    | Default cache TTL (seconds)  | env file     |
| `SESSION_TTL`                  | integer | 86400   | Session TTL (seconds)        | env file     |

**Example:**

```bash
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
REDIS_DB=0
CACHE_TTL=3600
SESSION_TTL=86400
```

### Security Configuration

| Option                        | Type    | Default     | Description                            | Where to set |
| ----------------------------- | ------- | ----------- | -------------------------------------- | ------------ |
| `SECRET_KEY`                  | string  | -           | JWT signing key (**REQUIRED**)         | env file     |
| `JWT_ALGORITHM`               | string  | "HS256"     | JWT algorithm                          | env file     |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | integer | 30          | Access token expiry                    | env file     |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | integer | 7           | Refresh token expiry                   | env file     |
| `PASSWORD_MIN_LENGTH`         | integer | 8           | Minimum password length                | env file     |
| `PASSWORD_REQUIRE_UPPERCASE`  | boolean | true        | Require uppercase letters              | env file     |
| `PASSWORD_REQUIRE_LOWERCASE`  | boolean | true        | Require lowercase letters              | env file     |
| `PASSWORD_REQUIRE_NUMBERS`    | boolean | true        | Require numbers                        | env file     |
| `PASSWORD_REQUIRE_SPECIAL`    | boolean | true        | Require special characters             | env file     |
| `RATE_LIMIT_PER_MINUTE`       | integer | 60          | API rate limit per minute              | env file     |
| `RATE_LIMIT_BURST`            | integer | 100         | Burst allowance                        | env file     |
| `API_KEY_HEADER`              | string  | "X-API-Key" | API key header name                    | env file     |
| `CORS_ORIGINS`                | string  | "\*"        | Allowed CORS origins (comma-separated) | env file     |
| `CORS_ALLOW_CREDENTIALS`      | boolean | true        | Allow credentials in CORS              | env file     |
| `ENCRYPTION_KEY`              | string  | -           | Field encryption key (32 chars)        | env file     |
| `FIELD_ENCRYPTION_ENABLED`    | boolean | true        | Enable field-level encryption          | env file     |

**Generate SECRET_KEY:**

```bash
openssl rand -hex 32
# Or in Python:
python -c "import secrets; print(secrets.token_hex(32))"
```

### Blockchain Configuration

| Option                     | Type    | Default  | Description                        | Where to set |
| -------------------------- | ------- | -------- | ---------------------------------- | ------------ |
| `ETH_RPC_URL`              | string  | -        | Ethereum RPC endpoint              | env file     |
| `ETH_WEBSOCKET_URL`        | string  | -        | Ethereum WebSocket endpoint        | env file     |
| `ETH_CHAIN_ID`             | integer | 1        | Ethereum chain ID (1=mainnet)      | env file     |
| `POLYGON_RPC_URL`          | string  | -        | Polygon RPC endpoint               | env file     |
| `POLYGON_CHAIN_ID`         | integer | 137      | Polygon chain ID                   | env file     |
| `BSC_RPC_URL`              | string  | -        | BSC RPC endpoint                   | env file     |
| `BSC_CHAIN_ID`             | integer | 56       | BSC chain ID                       | env file     |
| `GAS_PRICE_STRATEGY`       | enum    | "medium" | Gas price: `low`, `medium`, `high` | env file     |
| `MAX_GAS_PRICE`            | integer | 100      | Maximum gas price (Gwei)           | env file     |
| `GOVERNANCE_TOKEN_ADDRESS` | string  | -        | Deployed governance token address  | env file     |
| `ASSET_VAULT_ADDRESS`      | string  | -        | Deployed asset vault address       | env file     |
| `ETHERSCAN_API_KEY`        | string  | -        | Etherscan API key                  | env file     |
| `POLYGONSCAN_API_KEY`      | string  | -        | Polygonscan API key                | env file     |

**Example RPC URLs:**

```bash
# Infura
ETH_RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID
ETH_WEBSOCKET_URL=wss://mainnet.infura.io/ws/v3/YOUR_PROJECT_ID

# Alchemy
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY

# Public endpoints (not recommended for production)
POLYGON_RPC_URL=https://polygon-rpc.com
BSC_RPC_URL=https://bsc-dataseed.binance.org/
```

### Compliance Configuration

| Option                           | Type    | Default       | Description                           | Where to set |
| -------------------------------- | ------- | ------------- | ------------------------------------- | ------------ |
| `KYC_ENABLED`                    | boolean | true          | Enable KYC verification               | env file     |
| `KYC_PROVIDER`                   | string  | "jumio"       | KYC provider: `jumio`, `onfido`, etc. | env file     |
| `KYC_API_KEY`                    | string  | -             | KYC provider API key                  | env file     |
| `KYC_API_SECRET`                 | string  | -             | KYC provider API secret               | env file     |
| `AML_ENABLED`                    | boolean | true          | Enable AML screening                  | env file     |
| `AML_PROVIDER`                   | string  | "chainalysis" | AML provider                          | env file     |
| `AML_API_KEY`                    | string  | -             | AML provider API key                  | env file     |
| `TRANSACTION_MONITORING_ENABLED` | boolean | true          | Enable transaction monitoring         | env file     |
| `SUSPICIOUS_AMOUNT_THRESHOLD`    | float   | 10000.0       | Suspicious transaction threshold      | env file     |
| `DAILY_TRANSACTION_LIMIT`        | float   | 50000.0       | Daily transaction limit per user      | env file     |
| `REGULATORY_REPORTING_ENABLED`   | boolean | true          | Enable regulatory reporting           | env file     |
| `AUDIT_LOG_RETENTION_DAYS`       | integer | 2555          | Audit log retention (7 years)         | env file     |

### Monitoring Configuration

| Option                  | Type    | Default | Description                                    | Where to set |
| ----------------------- | ------- | ------- | ---------------------------------------------- | ------------ |
| `LOG_LEVEL`             | enum    | "INFO"  | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` | env file     |
| `LOG_FORMAT`            | enum    | "json"  | Log format: `json`, `text`                     | env file     |
| `LOG_FILE`              | string  | -       | Log file path (empty for stdout)               | env file     |
| `METRICS_ENABLED`       | boolean | true    | Enable Prometheus metrics                      | env file     |
| `METRICS_PORT`          | integer | 8001    | Metrics endpoint port                          | env file     |
| `HEALTH_CHECK_INTERVAL` | integer | 30      | Health check interval (seconds)                | env file     |
| `SENTRY_DSN`            | string  | -       | Sentry error tracking DSN                      | env file     |
| `SENTRY_ENVIRONMENT`    | string  | -       | Sentry environment tag                         | env file     |

### Email Configuration

| Option          | Type    | Default | Description          | Where to set |
| --------------- | ------- | ------- | -------------------- | ------------ |
| `SMTP_HOST`     | string  | -       | SMTP server hostname | env file     |
| `SMTP_PORT`     | integer | 587     | SMTP server port     | env file     |
| `SMTP_USERNAME` | string  | -       | SMTP username        | env file     |
| `SMTP_PASSWORD` | string  | -       | SMTP password        | env file     |
| `SMTP_USE_TLS`  | boolean | true    | Use TLS encryption   | env file     |
| `FROM_EMAIL`    | string  | -       | Sender email address | env file     |

### Celery Configuration

| Option                     | Type   | Default | Description                 | Where to set |
| -------------------------- | ------ | ------- | --------------------------- | ------------ |
| `CELERY_BROKER_URL`        | string | -       | Message broker URL (Redis)  | env file     |
| `CELERY_RESULT_BACKEND`    | string | -       | Result backend URL (Redis)  | env file     |
| `CELERY_TASK_SERIALIZER`   | string | "json"  | Task serialization format   | env file     |
| `CELERY_RESULT_SERIALIZER` | string | "json"  | Result serialization format | env file     |
| `CELERY_TIMEZONE`          | string | "UTC"   | Celery timezone             | env file     |

## Blockchain Configuration

File: `code/blockchain/.env`

| Option              | Type   | Default     | Description                              | Where to set |
| ------------------- | ------ | ----------- | ---------------------------------------- | ------------ |
| `INFURA_PROJECT_ID` | string | -           | Infura project ID                        | env file     |
| `ETHERSCAN_API_KEY` | string | -           | Etherscan API key for verification       | env file     |
| `PRIVATE_KEY`       | string | -           | Deployer private key (without 0x prefix) | env file     |
| `HARDHAT_NETWORK`   | string | "localhost" | Default network for Hardhat              | env file     |

**Example:**

```bash
INFURA_PROJECT_ID=your_infura_project_id
ETHERSCAN_API_KEY=your_etherscan_api_key
PRIVATE_KEY=your_private_key_without_0x_prefix
```

## Frontend Configuration

### Web Frontend

File: `web-frontend/.env`

| Option                  | Type    | Default                  | Description      | Where to set |
| ----------------------- | ------- | ------------------------ | ---------------- | ------------ |
| `REACT_APP_API_URL`     | string  | "http://localhost:8000"  | Backend API URL  | env file     |
| `REACT_APP_WS_URL`      | string  | "ws://localhost:8000/ws" | WebSocket URL    | env file     |
| `REACT_APP_CHAIN_ID`    | integer | 1                        | Default chain ID | env file     |
| `REACT_APP_ENVIRONMENT` | string  | "development"            | Environment      | env file     |

### Mobile Frontend

File: `mobile-frontend/.env`

| Option                 | Type    | Default | Description      | Where to set |
| ---------------------- | ------- | ------- | ---------------- | ------------ |
| `NEXT_PUBLIC_API_URL`  | string  | -       | Backend API URL  | env file     |
| `NEXT_PUBLIC_CHAIN_ID` | integer | 1       | Default chain ID | env file     |

## Environment-Specific Configuration

### Development Environment

```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DB_ECHO=true
WORKERS=1
CORS_ORIGINS=*
```

### Staging Environment

```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
DB_ECHO=false
WORKERS=2
CORS_ORIGINS=https://staging.chainfinity.com
```

### Production Environment

```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DB_ECHO=false
WORKERS=4
CORS_ORIGINS=https://chainfinity.com,https://www.chainfinity.com
SENTRY_DSN=your_sentry_dsn
METRICS_ENABLED=true
```

## Configuration Best Practices

1. **Never commit `.env` files** - Use `.env.example` as template
2. **Use strong secrets** - Generate with `openssl rand -hex 32`
3. **Rotate secrets regularly** - Especially in production
4. **Use separate databases** - Different DB for each environment
5. **Enable monitoring** - Set up Sentry and Prometheus in production
6. **Limit CORS origins** - Be specific in production
7. **Use environment variables** - Never hardcode credentials
8. **Backup configuration** - Store securely (e.g., AWS Secrets Manager)

## Configuration Validation

Validate your configuration:

```bash
# Check backend configuration
cd code/backend
python -c "from config.settings import settings; print('✓ Configuration valid')"

# Test database connection
python -c "from config.database import check_database_health; import asyncio; asyncio.run(check_database_health())"

# Test Redis connection
python -c "from config.database import check_redis_health; import asyncio; asyncio.run(check_redis_health())"
```

## Loading Configuration Files

ChainFinity automatically loads configuration in this order:

1. Environment variables
2. `.env` file in component directory
3. Default values in `config/settings.py`

To override configuration:

```bash
# Set environment variable (takes precedence)
export DATABASE_URL=postgresql+asyncpg://localhost/mydb

# Or modify .env file
echo "DATABASE_URL=postgresql+asyncpg://localhost/mydb" >> .env
```

## Next Steps

- Review [API Reference](./API.md) to understand API endpoints
- Check [Usage Guide](./USAGE.md) for common workflows
- See [Deployment Guide](./deployment.md) for production deployment

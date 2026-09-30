# ChainFinity API Reference

Complete API documentation for ChainFinity v2.0 REST API.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL & Versioning](#base-url--versioning)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Authentication Endpoints](#authentication-endpoints)
- [User Management Endpoints](#user-management-endpoints)
- [Portfolio Endpoints](#portfolio-endpoints)
- [Transaction Endpoints](#transaction-endpoints)
- [Risk Assessment Endpoints](#risk-assessment-endpoints)
- [Compliance Endpoints](#compliance-endpoints)
- [Blockchain Endpoints](#blockchain-endpoints)

## Overview

The ChainFinity API is a RESTful API that provides programmatic access to DeFi risk management, portfolio tracking, and cross-chain operations.

**Key Features:**

- JWT authentication with refresh tokens
- RESTful design with JSON responses
- Comprehensive error handling
- Rate limiting (60 requests/minute)
- WebSocket support for real-time updates

## Authentication

ChainFinity uses JWT (JSON Web Tokens) for authentication.

### Authentication Flow

1. **Register** or **Login** to receive access and refresh tokens
2. Include `Authorization: Bearer <access_token>` header in subsequent requests
3. Refresh tokens when access token expires

**Example:**

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Use token
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <access_token>"
```

## Base URL & Versioning

| Environment     | Base URL                                     |
| --------------- | -------------------------------------------- |
| **Development** | `http://localhost:8000/api/v1`               |
| **Staging**     | `https://staging-api.chainfinity.com/api/v1` |
| **Production**  | `https://api.chainfinity.com/api/v1`         |

## Response Format

### Success Response

```json
{
  "success": true,
  "data": {/* response data */},
  "message": "Optional success message"
}
```

### Error Response

```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE",
  "details": [/* optional error details */]
}
```

### Pagination

Paginated endpoints return:

```json
{
  "success": true,
  "data": [/* array of items */],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 150,
    "pages": 8
  }
}
```

## Error Handling

### HTTP Status Codes

| Code  | Meaning               | Description                       |
| ----- | --------------------- | --------------------------------- |
| `200` | OK                    | Request successful                |
| `201` | Created               | Resource created successfully     |
| `400` | Bad Request           | Invalid request parameters        |
| `401` | Unauthorized          | Authentication required or failed |
| `403` | Forbidden             | Insufficient permissions          |
| `404` | Not Found             | Resource not found                |
| `422` | Validation Error      | Request validation failed         |
| `429` | Too Many Requests     | Rate limit exceeded               |
| `500` | Internal Server Error | Server error                      |

### Error Codes

| Code                       | Description                     |
| -------------------------- | ------------------------------- |
| `VALIDATION_ERROR`         | Request validation failed       |
| `AUTHENTICATION_FAILED`    | Invalid credentials             |
| `TOKEN_EXPIRED`            | Access token expired            |
| `INSUFFICIENT_PERMISSIONS` | User lacks required permissions |
| `RESOURCE_NOT_FOUND`       | Requested resource not found    |
| `RATE_LIMIT_EXCEEDED`      | Too many requests               |

## Authentication Endpoints

### POST /auth/register

Register a new user account.

**Request Body:**

| Field               | Type    | Required | Description               | Example            |
| ------------------- | ------- | -------- | ------------------------- | ------------------ |
| `email`             | string  | Yes      | User email address        | `user@example.com` |
| `password`          | string  | Yes      | Password (min 8 chars)    | `SecureP@ss123`    |
| `wallet_address`    | string  | No       | Ethereum wallet address   | `0x742d...`        |
| `terms_accepted`    | boolean | Yes      | Terms acceptance          | `true`             |
| `privacy_accepted`  | boolean | Yes      | Privacy policy acceptance | `true`             |
| `marketing_consent` | boolean | No       | Marketing emails consent  | `false`            |

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
  "kyc_status": "pending",
  "created_at": "2025-01-08T12:00:00Z"
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecureP@ss123",
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
    "terms_accepted": true,
    "privacy_accepted": true
  }'
```

### POST /auth/login

Authenticate user and receive JWT tokens.

**Request Body:**

| Field      | Type   | Required | Description           | Example            |
| ---------- | ------ | -------- | --------------------- | ------------------ |
| `email`    | string | Yes      | User email            | `user@example.com` |
| `password` | string | Yes      | User password         | `SecureP@ss123`    |
| `mfa_code` | string | No       | MFA code (if enabled) | `123456`           |

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecureP@ss123"}'
```

### POST /auth/refresh

Refresh access token using refresh token.

**Request Body:**

| Field           | Type   | Required | Description         |
| --------------- | ------ | -------- | ------------------- |
| `refresh_token` | string | Yes      | Valid refresh token |

**Response:**

```json
{
  "access_token": "new_access_token",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### POST /auth/logout

Invalidate user session and tokens.

**Headers:** Authorization required

**Response:**

```json
{
  "success": true,
  "message": "Successfully logged out"
}
```

## User Management Endpoints

### GET /users/me

Get current user profile.

**Headers:** Authorization required

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
  "kyc_status": "verified",
  "risk_profile": "moderate",
  "created_at": "2025-01-08T12:00:00Z",
  "updated_at": "2025-01-08T15:30:00Z"
}
```

**Example:**

```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <access_token>"
```

### PUT /users/me

Update current user profile.

**Headers:** Authorization required

**Request Body:**

| Field                      | Type   | Required | Description           | Example           |
| -------------------------- | ------ | -------- | --------------------- | ----------------- |
| `wallet_address`           | string | No       | Update wallet address | `0x742d...`       |
| `notification_preferences` | object | No       | Notification settings | `{"email": true}` |

**Response:** Updated user object

## Portfolio Endpoints

### GET /portfolios

List user's portfolios.

**Headers:** Authorization required

**Query Parameters:**

| Parameter   | Type    | Default      | Description                | Example       |
| ----------- | ------- | ------------ | -------------------------- | ------------- |
| `page`      | integer | 1            | Page number                | `1`           |
| `page_size` | integer | 20           | Items per page             | `50`          |
| `sort_by`   | string  | `created_at` | Sort field                 | `total_value` |
| `order`     | enum    | `desc`       | Sort order (`asc`, `desc`) | `desc`        |

**Response:**

```json
{
  "data": [
    {
      "id": "portfolio-uuid",
      "name": "Main Portfolio",
      "total_value": "125430.50",
      "total_value_usd": 125430.5,
      "assets_count": 12,
      "risk_score": 6.5,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 3,
    "pages": 1
  }
}
```

**Example:**

```bash
curl -X GET "http://localhost:8000/api/v1/portfolios?page=1&page_size=20" \
  -H "Authorization: Bearer <access_token>"
```

### POST /portfolios

Create a new portfolio.

**Headers:** Authorization required

**Request Body:**

| Field         | Type   | Required | Description           | Example               |
| ------------- | ------ | -------- | --------------------- | --------------------- |
| `name`        | string | Yes      | Portfolio name        | `DeFi Holdings`       |
| `description` | string | No       | Portfolio description | `My DeFi investments` |
| `tags`        | array  | No       | Portfolio tags        | `["defi", "yield"]`   |

**Response:** Created portfolio object (201 status)

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/portfolios \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DeFi Holdings",
    "description": "My DeFi investments",
    "tags": ["defi", "yield"]
  }'
```

### GET /portfolios/{portfolio_id}

Get detailed portfolio information.

**Headers:** Authorization required

**Path Parameters:**

| Parameter      | Type          | Description          |
| -------------- | ------------- | -------------------- |
| `portfolio_id` | string (UUID) | Portfolio identifier |

**Response:**

```json
{
  "id": "portfolio-uuid",
  "name": "Main Portfolio",
  "description": "My main crypto portfolio",
  "total_value_usd": 125430.5,
  "assets": [
    {
      "token_address": "0x...",
      "symbol": "ETH",
      "amount": "10.5",
      "value_usd": 25000.0,
      "chain": "ethereum"
    }
  ],
  "risk_metrics": {
    "risk_score": 6.5,
    "volatility": 0.45,
    "sharpe_ratio": 1.8
  },
  "created_at": "2025-01-01T00:00:00Z"
}
```

### PUT /portfolios/{portfolio_id}

Update portfolio details.

**Headers:** Authorization required

**Request Body:** Partial update supported

### DELETE /portfolios/{portfolio_id}

Delete a portfolio.

**Headers:** Authorization required

**Response:** 204 No Content

## Transaction Endpoints

### GET /transactions

List user transactions.

**Headers:** Authorization required

**Query Parameters:**

| Parameter   | Type    | Default | Description             |
| ----------- | ------- | ------- | ----------------------- |
| `page`      | integer | 1       | Page number             |
| `page_size` | integer | 20      | Items per page          |
| `type`      | enum    | all     | Transaction type filter |
| `status`    | enum    | all     | Status filter           |
| `from_date` | string  | -       | Start date (ISO 8601)   |
| `to_date`   | string  | -       | End date (ISO 8601)     |

**Response:**

```json
{
  "data": [
    {
      "id": "tx-uuid",
      "hash": "0x123...",
      "type": "transfer",
      "status": "confirmed",
      "amount": "100.00",
      "token": "USDC",
      "chain": "ethereum",
      "timestamp": "2025-01-08T12:00:00Z"
    }
  ],
  "pagination": {/* ... */}
}
```

### GET /transactions/{transaction_id}

Get transaction details.

**Headers:** Authorization required

**Path Parameters:**

| Parameter        | Type          | Description            |
| ---------------- | ------------- | ---------------------- |
| `transaction_id` | string (UUID) | Transaction identifier |

**Response:** Detailed transaction object

### POST /transactions/analyze

Analyze transaction risk.

**Headers:** Authorization required

**Request Body:**

| Field              | Type   | Required | Description                 |
| ------------------ | ------ | -------- | --------------------------- |
| `transaction_hash` | string | Yes      | Blockchain transaction hash |
| `chain`            | string | Yes      | Blockchain network          |

**Response:** Risk analysis result

## Risk Assessment Endpoints

### GET /risk/assessments

List risk assessments.

**Headers:** Authorization required

**Response:**

```json
{
  "data": [
    {
      "id": "assessment-uuid",
      "portfolio_id": "portfolio-uuid",
      "risk_score": 6.5,
      "volatility": 0.45,
      "var_95": 0.15,
      "sharpe_ratio": 1.8,
      "created_at": "2025-01-08T12:00:00Z"
    }
  ]
}
```

### POST /risk/assess/{portfolio_id}

Assess portfolio risk.

**Headers:** Authorization required

**Path Parameters:**

| Parameter      | Type          | Description         |
| -------------- | ------------- | ------------------- |
| `portfolio_id` | string (UUID) | Portfolio to assess |

**Response:** New risk assessment object

## Compliance Endpoints

### GET /compliance/checks

List compliance checks for current user.

**Headers:** Authorization required

**Response:**

```json
{
  "data": [
    {
      "id": "check-uuid",
      "type": "kyc",
      "status": "passed",
      "completed_at": "2025-01-08T12:00:00Z"
    }
  ]
}
```

### GET /compliance/audit-logs

Get audit log entries.

**Headers:** Authorization required (Admin role)

**Query Parameters:**

| Parameter   | Type   | Description           |
| ----------- | ------ | --------------------- |
| `user_id`   | string | Filter by user        |
| `action`    | string | Filter by action type |
| `from_date` | string | Start date            |

## Blockchain Endpoints

### GET /blockchain/networks

List supported blockchain networks.

**Response:**

```json
{
  "data": [
    {
      "id": "ethereum",
      "name": "Ethereum",
      "chain_id": 1,
      "rpc_url": "https://...",
      "explorer_url": "https://etherscan.io"
    }
  ]
}
```

### GET /blockchain/contracts

List deployed smart contracts.

**Response:** Array of contract objects with addresses and ABIs

## WebSocket API

### Real-Time Price Updates

**Endpoint:** `ws://localhost:8000/ws/prices`

**Authentication:** Include access token in connection params

**Message Format:**

```json
{
  "type": "price_update",
  "data": {
    "symbol": "ETH",
    "price": 2500.0,
    "change_24h": 0.05,
    "timestamp": "2025-01-08T12:00:00Z"
  }
}
```

## Rate Limiting

- **Default Limit:** 60 requests per minute per user
- **Burst Allowance:** 100 requests
- **Headers:**
  - `X-RateLimit-Limit`: Total limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset timestamp

## SDK Examples

### Python

```python
import requests

base_url = "http://localhost:8000/api/v1"

# Login
response = requests.post(f"{base_url}/auth/login", json={
    "email": "user@example.com",
    "password": "SecureP@ss123"
})
token = response.json()["access_token"]

# Get portfolios
headers = {"Authorization": f"Bearer {token}"}
portfolios = requests.get(f"{base_url}/portfolios", headers=headers).json()
```

### JavaScript

```javascript
const BASE_URL = "http://localhost:8000/api/v1";

// Login
const response = await fetch(`${BASE_URL}/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    password: "SecureP@ss123",
  }),
});
const { access_token } = await response.json();

// Get portfolios
const portfolios = await fetch(`${BASE_URL}/portfolios`, {
  headers: { Authorization: `Bearer ${access_token}` },
}).then((r) => r.json());
```

## Next Steps

- Review [CLI Reference](./CLI.md) for command-line tools
- Check [Examples](./examples/) for complete workflows
- See [Troubleshooting](./TROUBLESHOOTING.md) for common API issues

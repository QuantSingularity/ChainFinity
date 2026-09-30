# ChainFinity Usage Guide

This guide demonstrates typical usage patterns and workflows for ChainFinity's CLI, API, and UI interfaces.

## Table of Contents

- [Getting Started](#getting-started)
- [Common Workflows](#common-workflows)
- [CLI Usage](#cli-usage)
- [API Usage](#api-usage)
- [Library Usage](#library-usage)
- [UI Usage](#ui-usage)

## Getting Started

### Prerequisites

Before using ChainFinity, ensure you have:

1. Installed ChainFinity (see [Installation Guide](./INSTALLATION.md))
2. Configured environment variables (see [Configuration Guide](./CONFIGURATION.md))
3. Started all services (`./scripts/run_chainfinity.sh`)
4. Created a user account

### Quick Start: Three-Step Workflow

```bash
# 1. Start services
./scripts/run_chainfinity.sh

# 2. Access the platform
# Web UI: http://localhost:3000
# API: http://localhost:8000/docs
# WebSocket: ws://localhost:8000/ws

# 3. Create account and explore
# Register through UI or API
```

## Common Workflows

### Workflow 1: User Registration and Authentication

#### Via Web UI

1. Navigate to `http://localhost:3000/register`
2. Fill in email, password, and wallet address
3. Accept terms and privacy policy
4. Click "Create Account"
5. Check email for verification link (if enabled)

#### Via API

```bash
# 1. Register new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecureP@ss123",
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
    "terms_accepted": true,
    "privacy_accepted": true
  }'

# 2. Login to get tokens
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecureP@ss123"
  }'

# Response:
# {
#   "access_token": "eyJhbGci...",
#   "refresh_token": "eyJhbGci...",
#   "token_type": "bearer"
# }

# 3. Use token in subsequent requests
export TOKEN="your_access_token"
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
```

### Workflow 2: Create and Manage Portfolio

#### Via Web UI

1. Login to dashboard
2. Click "Create Portfolio"
3. Enter portfolio name and description
4. Add assets by:
   - Entering wallet address for auto-import
   - Manually adding token holdings
5. View portfolio analytics and risk metrics

#### Via API

```bash
# 1. Create portfolio
curl -X POST http://localhost:8000/api/v1/portfolios \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DeFi Portfolio",
    "description": "My DeFi yield farming positions"
  }'

# Response:
# {
#   "id": "550e8400-e29b-41d4-a716-446655440000",
#   "name": "DeFi Portfolio",
#   "total_value_usd": 0,
#   "created_at": "2025-01-08T12:00:00Z"
# }

# 2. Get all portfolios
curl -X GET http://localhost:8000/api/v1/portfolios \
  -H "Authorization: Bearer $TOKEN"

# 3. Get specific portfolio details
PORTFOLIO_ID="550e8400-e29b-41d4-a716-446655440000"
curl -X GET http://localhost:8000/api/v1/portfolios/$PORTFOLIO_ID \
  -H "Authorization: Bearer $TOKEN"

# 4. Update portfolio
curl -X PUT http://localhost:8000/api/v1/portfolios/$PORTFOLIO_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated DeFi Portfolio",
    "description": "Including new positions"
  }'
```

### Workflow 3: Risk Assessment

#### Via API

```bash
# 1. Assess portfolio risk
curl -X POST http://localhost:8000/api/v1/risk/assess/$PORTFOLIO_ID \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "id": "assessment-uuid",
#   "portfolio_id": "portfolio-uuid",
#   "risk_score": 6.5,
#   "risk_level": "moderate",
#   "metrics": {
#     "volatility": 0.45,
#     "var_95": 0.15,
#     "sharpe_ratio": 1.8,
#     "max_drawdown": 0.22
#   },
#   "recommendations": [
#     "Consider diversifying across more chains",
#     "High concentration in ETH (45%)"
#   ],
#   "created_at": "2025-01-08T12:00:00Z"
# }

# 2. Get all risk assessments
curl -X GET http://localhost:8000/api/v1/risk/assessments \
  -H "Authorization: Bearer $TOKEN"

# 3. Get specific assessment
ASSESSMENT_ID="assessment-uuid"
curl -X GET http://localhost:8000/api/v1/risk/assessments/$ASSESSMENT_ID \
  -H "Authorization: Bearer $TOKEN"
```

### Workflow 4: Cross-Chain Transfer

#### Via Smart Contract

```javascript
// 1. Connect to CrossChainManager contract
const ethers = require('ethers');
const provider = new ethers.providers.JsonRpcProvider(process.env.ETH_RPC_URL);
const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);

const contractAddress = "0x..."; // CrossChainManager address
const contractABI = [...]; // Contract ABI
const contract = new ethers.Contract(contractAddress, contractABI, wallet);

// 2. Initiate cross-chain transfer
const tx = await contract.initiateCrossChainTransfer(
  "0xTokenAddress",      // Token address
  ethers.utils.parseEther("10"), // Amount
  64,                     // Target chain selector (Polygon)
  "0xRecipientAddress"   // Recipient on target chain
);

await tx.wait();
console.log("Transfer initiated:", tx.hash);

// 3. Monitor transfer status
const transferId = ethers.utils.keccak256(tx.hash);
const transfer = await contract.transfers(transferId);
console.log("Transfer status:", transfer);
```

### Workflow 5: Monitor Transactions

#### Via API

```bash
# 1. List recent transactions
curl -X GET "http://localhost:8000/api/v1/transactions?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# 2. Filter by date range
curl -X GET "http://localhost:8000/api/v1/transactions?from_date=2025-01-01&to_date=2025-01-08" \
  -H "Authorization: Bearer $TOKEN"

# 3. Get transaction details
TRANSACTION_ID="tx-uuid"
curl -X GET http://localhost:8000/api/v1/transactions/$TRANSACTION_ID \
  -H "Authorization: Bearer $TOKEN"

# 4. Analyze transaction risk
curl -X POST http://localhost:8000/api/v1/transactions/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_hash": "0x123...",
    "chain": "ethereum"
  }'
```

## CLI Usage

### Environment Setup

```bash
# Complete environment setup
./scripts/env_setup.sh --environment production

# Custom setup
./scripts/env_setup.sh \
  --python-version 3.11 \
  --node-version 18 \
  --skip-docker
```

### Deployment

```bash
# Deploy to staging
./scripts/deploy_chainfinity.sh --environment staging

# Deploy backend only
./scripts/deploy_chainfinity.sh \
  --environment production \
  --component backend

# Dry run deployment
./scripts/deploy_chainfinity.sh \
  --environment production \
  --dry-run
```

### Testing

```bash
# Run all tests
./scripts/test_chainfinity.sh

# Run backend tests only with coverage
./scripts/test_chainfinity.sh \
  --component backend \
  --coverage-threshold 85

# Run tests sequentially
./scripts/test_chainfinity.sh --no-parallel
```

### Monitoring

```bash
# Start monitoring with defaults
./scripts/monitor_chainfinity.sh

# Custom monitoring with alerts
./scripts/monitor_chainfinity.sh \
  --alert-threshold 90 \
  --check-interval 60 \
  --slack-webhook https://hooks.slack.com/...
```

## API Usage

### Python Client Example

```python
import requests
from typing import Dict, Optional

class ChainFinityClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = f"{base_url}/api/v1"
        self.token: Optional[str] = None

    def login(self, email: str, password: str) -> Dict:
        """Login and store access token"""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        return data

    def get_headers(self) -> Dict:
        """Get authorization headers"""
        if not self.token:
            raise ValueError("Not authenticated. Call login() first.")
        return {"Authorization": f"Bearer {self.token}"}

    def create_portfolio(self, name: str, description: str = "") -> Dict:
        """Create a new portfolio"""
        response = requests.post(
            f"{self.base_url}/portfolios",
            json={"name": name, "description": description},
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()

    def get_portfolios(self, page: int = 1, page_size: int = 20) -> Dict:
        """List portfolios"""
        response = requests.get(
            f"{self.base_url}/portfolios",
            params={"page": page, "page_size": page_size},
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()

    def assess_risk(self, portfolio_id: str) -> Dict:
        """Assess portfolio risk"""
        response = requests.post(
            f"{self.base_url}/risk/assess/{portfolio_id}",
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()

# Usage
client = ChainFinityClient()
client.login("user@example.com", "SecureP@ss123")

# Create portfolio
portfolio = client.create_portfolio(
    name="My DeFi Portfolio",
    description="Yield farming positions"
)
print(f"Created portfolio: {portfolio['id']}")

# Assess risk
risk = client.assess_risk(portfolio['id'])
print(f"Risk score: {risk['risk_score']}")
```

### JavaScript/Node.js Client Example

```javascript
const axios = require("axios");

class ChainFinityClient {
  constructor(baseUrl = "http://localhost:8000") {
    this.baseUrl = `${baseUrl}/api/v1`;
    this.token = null;
  }

  async login(email, password) {
    const response = await axios.post(`${this.baseUrl}/auth/login`, {
      email,
      password,
    });
    this.token = response.data.access_token;
    return response.data;
  }

  getHeaders() {
    if (!this.token) {
      throw new Error("Not authenticated. Call login() first.");
    }
    return {
      Authorization: `Bearer ${this.token}`,
    };
  }

  async createPortfolio(name, description = "") {
    const response = await axios.post(
      `${this.baseUrl}/portfolios`,
      { name, description },
      { headers: this.getHeaders() },
    );
    return response.data;
  }

  async getPortfolios(page = 1, pageSize = 20) {
    const response = await axios.get(`${this.baseUrl}/portfolios`, {
      params: { page, page_size: pageSize },
      headers: this.getHeaders(),
    });
    return response.data;
  }

  async assessRisk(portfolioId) {
    const response = await axios.post(
      `${this.baseUrl}/risk/assess/${portfolioId}`,
      {},
      { headers: this.getHeaders() },
    );
    return response.data;
  }
}

// Usage
(async () => {
  const client = new ChainFinityClient();

  // Login
  await client.login("user@example.com", "SecureP@ss123");

  // Create portfolio
  const portfolio = await client.createPortfolio(
    "My DeFi Portfolio",
    "Yield farming positions",
  );
  console.log(`Created portfolio: ${portfolio.id}`);

  // Assess risk
  const risk = await client.assessRisk(portfolio.id);
  console.log(`Risk score: ${risk.risk_score}`);
})();
```

## Library Usage

### Smart Contract Integration

```javascript
// Example: Interacting with AssetVault contract
const { ethers } = require("ethers");

// Setup
const provider = new ethers.providers.JsonRpcProvider(process.env.ETH_RPC_URL);
const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
const vaultAddress = process.env.ASSET_VAULT_ADDRESS;
const vaultABI = require("./abis/AssetVault.json");
const vault = new ethers.Contract(vaultAddress, vaultABI, wallet);

// Deposit tokens
async function depositTokens(tokenAddress, amount) {
  // Approve token spend
  const token = new ethers.Contract(tokenAddress, ERC20_ABI, wallet);
  const approveTx = await token.approve(vaultAddress, amount);
  await approveTx.wait();

  // Deposit
  const depositTx = await vault.deposit(tokenAddress, amount);
  await depositTx.wait();
  console.log("Deposit successful:", depositTx.hash);
}

// Withdraw tokens
async function withdrawTokens(tokenAddress, amount) {
  const withdrawTx = await vault.withdraw(tokenAddress, amount);
  await withdrawTx.wait();
  console.log("Withdrawal successful:", withdrawTx.hash);
}

// Get balance
async function getBalance(tokenAddress, userAddress) {
  const balance = await vault.balanceOf(userAddress, tokenAddress);
  return ethers.utils.formatEther(balance);
}
```

## UI Usage

### Web Dashboard

1. **Dashboard Overview**
   - View total portfolio value across all chains
   - Monitor real-time price changes
   - Check risk score and alerts

2. **Portfolio Management**
   - Create/edit/delete portfolios
   - Add assets manually or via wallet import
   - View asset allocation charts

3. **Risk Analysis**
   - Run risk assessments
   - View historical risk metrics
   - Get AI-powered recommendations

4. **Transaction History**
   - View all transactions across chains
   - Filter by date, type, status
   - Export to CSV

5. **Settings**
   - Update profile and preferences
   - Configure notifications
   - Manage API keys
   - Set up MFA

### Mobile App

Similar functionality to web dashboard, optimized for mobile:

1. Portfolio overview with swipe gestures
2. Quick actions for common tasks
3. Push notifications for alerts
4. Biometric authentication

## WebSocket Real-Time Updates

```javascript
// Connect to WebSocket
const ws = new WebSocket("ws://localhost:8000/ws/prices");

// Authenticate
ws.onopen = () => {
  ws.send(
    JSON.stringify({
      type: "auth",
      token: accessToken,
    }),
  );
};

// Receive price updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === "price_update") {
    console.log(`${data.data.symbol}: $${data.data.price}`);
    // Update UI with new price
  }
};

// Handle errors
ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

// Subscribe to specific assets
ws.send(
  JSON.stringify({
    type: "subscribe",
    symbols: ["ETH", "BTC", "USDC"],
  }),
);
```

## Best Practices

### Security

1. **Never commit credentials** - Use environment variables
2. **Rotate API keys** - Regularly update access tokens
3. **Use HTTPS** - Always in production
4. **Validate input** - On both client and server
5. **Rate limiting** - Implement backoff strategies

### Performance

1. **Cache responses** - Use Redis or local cache
2. **Paginate large datasets** - Don't fetch all at once
3. **Batch requests** - Combine related API calls
4. **Use WebSockets** - For real-time data
5. **Optimize queries** - Add appropriate filters

### Error Handling

```python
# Example: Robust API client with retry
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def get_session_with_retry():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Use session with automatic retry
session = get_session_with_retry()
response = session.get('http://localhost:8000/api/v1/portfolios')
```

## Next Steps

- Review [API Reference](./API.md) for complete endpoint documentation
- Check [Examples](./examples/) for detailed code examples
- See [CLI Reference](./CLI.md) for command-line tools
- Explore [Architecture](./ARCHITECTURE.md) to understand system design

# Portfolio Management Example

This example demonstrates how to create, manage, and analyze portfolios using the ChainFinity API.

## Overview

Portfolio management in ChainFinity allows users to:

- Create and organize multiple portfolios
- Add and track assets across chains
- Monitor real-time portfolio values
- Analyze performance metrics
- Export portfolio data

## Prerequisites

- ChainFinity account (registered user)
- Access token (from authentication)
- Basic understanding of REST APIs

## Step 1: Authentication

First, authenticate to obtain an access token:

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "user@example.com",
    "password": "SecureP@ss123"
})

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print(f"✓ Authenticated successfully")
```

## Step 2: Create a Portfolio

```python
def create_portfolio(name, description="", tags=None):
    """Create a new portfolio"""

    payload = {
        "name": name,
        "description": description,
        "tags": tags or []
    }

    response = requests.post(
        f"{BASE_URL}/portfolios",
        json=payload,
        headers=headers
    )

    response.raise_for_status()
    portfolio = response.json()

    print(f"✓ Created portfolio: {portfolio['id']}")
    print(f"  Name: {portfolio['name']}")
    print(f"  Created: {portfolio['created_at']}")

    return portfolio

# Create portfolios
defi_portfolio = create_portfolio(
    name="DeFi Yield Farming",
    description="Yield farming positions across multiple protocols",
    tags=["defi", "yield", "staking"]
)

nft_portfolio = create_portfolio(
    name="NFT Collection",
    description="Digital art and collectibles",
    tags=["nft", "collectibles"]
)
```

## Step 3: Add Assets to Portfolio

```python
def add_asset_to_portfolio(portfolio_id, asset_data):
    """Add an asset to a portfolio"""

    response = requests.post(
        f"{BASE_URL}/portfolios/{portfolio_id}/assets",
        json=asset_data,
        headers=headers
    )

    response.raise_for_status()
    asset = response.json()

    print(f"✓ Added asset: {asset['symbol']}")
    print(f"  Amount: {asset['amount']}")
    print(f"  Value: ${asset['value_usd']:.2f}")

    return asset

# Add Ethereum to DeFi portfolio
eth_asset = add_asset_to_portfolio(
    portfolio_id=defi_portfolio['id'],
    asset_data={
        "token_address": "0x0000000000000000000000000000000000000000",  # Native ETH
        "symbol": "ETH",
        "name": "Ethereum",
        "amount": "10.5",
        "chain": "ethereum",
        "decimals": 18
    }
)

# Add USDC
usdc_asset = add_asset_to_portfolio(
    portfolio_id=defi_portfolio['id'],
    asset_data={
        "token_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "symbol": "USDC",
        "name": "USD Coin",
        "amount": "50000",
        "chain": "ethereum",
        "decimals": 6
    }
)

# Add Aave tokens on Polygon
aave_asset = add_asset_to_portfolio(
    portfolio_id=defi_portfolio['id'],
    asset_data={
        "token_address": "0xD6DF932A45C0f255f85145f286eA0b292B21C90B",
        "symbol": "AAVE",
        "name": "Aave",
        "amount": "100",
        "chain": "polygon",
        "decimals": 18
    }
)
```

## Step 4: List All Portfolios

```python
def list_portfolios(page=1, page_size=20, sort_by="created_at", order="desc"):
    """List all portfolios with pagination"""

    params = {
        "page": page,
        "page_size": page_size,
        "sort_by": sort_by,
        "order": order
    }

    response = requests.get(
        f"{BASE_URL}/portfolios",
        params=params,
        headers=headers
    )

    response.raise_for_status()
    data = response.json()

    print(f"\n=== Your Portfolios ===")
    print(f"Total: {data['pagination']['total']}")
    print()

    for portfolio in data['data']:
        print(f"Portfolio: {portfolio['name']}")
        print(f"  ID: {portfolio['id']}")
        print(f"  Value: ${portfolio['total_value_usd']:,.2f}")
        print(f"  Assets: {portfolio['assets_count']}")
        print(f"  Risk Score: {portfolio['risk_score']:.1f}/10")
        print()

    return data

# List portfolios sorted by value
portfolios = list_portfolios(sort_by="total_value", order="desc")
```

## Step 5: Get Portfolio Details

```python
def get_portfolio_details(portfolio_id):
    """Get detailed portfolio information including all assets"""

    response = requests.get(
        f"{BASE_URL}/portfolios/{portfolio_id}",
        headers=headers
    )

    response.raise_for_status()
    portfolio = response.json()

    print(f"\n=== Portfolio Details: {portfolio['name']} ===")
    print(f"ID: {portfolio['id']}")
    print(f"Description: {portfolio['description']}")
    print(f"Total Value: ${portfolio['total_value_usd']:,.2f}")
    print(f"Risk Score: {portfolio.get('risk_score', 'N/A')}")
    print(f"Created: {portfolio['created_at']}")
    print()

    print("Assets:")
    for asset in portfolio['assets']:
        print(f"  {asset['symbol']} ({asset['chain']})")
        print(f"    Amount: {asset['amount']}")
        print(f"    Value: ${asset['value_usd']:,.2f}")
        print(f"    Percentage: {asset['percentage']:.2f}%")
        print()

    if 'risk_metrics' in portfolio:
        metrics = portfolio['risk_metrics']
        print("Risk Metrics:")
        print(f"  Volatility: {metrics.get('volatility', 'N/A')}")
        print(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A')}")
        print(f"  VaR (95%): {metrics.get('var_95', 'N/A')}")
        print(f"  Max Drawdown: {metrics.get('max_drawdown', 'N/A')}")
        print()

    return portfolio

# Get DeFi portfolio details
defi_details = get_portfolio_details(defi_portfolio['id'])
```

## Step 6: Update Portfolio

```python
def update_portfolio(portfolio_id, updates):
    """Update portfolio name, description, or tags"""

    response = requests.put(
        f"{BASE_URL}/portfolios/{portfolio_id}",
        json=updates,
        headers=headers
    )

    response.raise_for_status()
    portfolio = response.json()

    print(f"✓ Updated portfolio: {portfolio['name']}")
    return portfolio

# Update portfolio description
updated_portfolio = update_portfolio(
    portfolio_id=defi_portfolio['id'],
    updates={
        "description": "Diversified DeFi positions with focus on blue-chip protocols",
        "tags": ["defi", "yield", "staking", "lp"]
    }
)
```

## Step 7: Update Asset in Portfolio

```python
def update_asset(portfolio_id, asset_id, updates):
    """Update asset amount or other properties"""

    response = requests.put(
        f"{BASE_URL}/portfolios/{portfolio_id}/assets/{asset_id}",
        json=updates,
        headers=headers
    )

    response.raise_for_status()
    asset = response.json()

    print(f"✓ Updated asset: {asset['symbol']}")
    print(f"  New amount: {asset['amount']}")
    print(f"  New value: ${asset['value_usd']:.2f}")

    return asset

# Update ETH amount (e.g., after selling some)
updated_eth = update_asset(
    portfolio_id=defi_portfolio['id'],
    asset_id=eth_asset['id'],
    updates={"amount": "8.5"}  # Reduced from 10.5 to 8.5
)
```

## Step 8: Remove Asset from Portfolio

```python
def remove_asset(portfolio_id, asset_id):
    """Remove an asset from portfolio"""

    response = requests.delete(
        f"{BASE_URL}/portfolios/{portfolio_id}/assets/{asset_id}",
        headers=headers
    )

    response.raise_for_status()
    print(f"✓ Removed asset from portfolio")

# Example: Remove an asset (uncomment to use)
# remove_asset(defi_portfolio['id'], some_asset_id)
```

## Step 9: Portfolio Performance Analytics

```python
def get_portfolio_performance(portfolio_id, period="30d"):
    """Get historical performance metrics"""

    response = requests.get(
        f"{BASE_URL}/portfolios/{portfolio_id}/performance",
        params={"period": period},
        headers=headers
    )

    response.raise_for_status()
    performance = response.json()

    print(f"\n=== Performance ({period}) ===")
    print(f"Starting Value: ${performance['start_value']:,.2f}")
    print(f"Current Value: ${performance['current_value']:,.2f}")
    print(f"Absolute Return: ${performance['absolute_return']:,.2f}")
    print(f"Percentage Return: {performance['percentage_return']:.2f}%")
    print(f"Volatility: {performance['volatility']:.2f}%")
    print(f"Sharpe Ratio: {performance['sharpe_ratio']:.2f}")
    print()

    return performance

# Get 30-day performance
perf_30d = get_portfolio_performance(defi_portfolio['id'], period="30d")

# Get all-time performance
perf_all = get_portfolio_performance(defi_portfolio['id'], period="all")
```

## Step 10: Export Portfolio Data

```python
def export_portfolio(portfolio_id, format="json"):
    """Export portfolio data to JSON or CSV"""

    response = requests.get(
        f"{BASE_URL}/portfolios/{portfolio_id}/export",
        params={"format": format},
        headers=headers
    )

    response.raise_for_status()

    # Save to file
    filename = f"portfolio_{portfolio_id}.{format}"

    if format == "json":
        with open(filename, 'w') as f:
            import json
            json.dump(response.json(), f, indent=2)
    else:  # csv
        with open(filename, 'wb') as f:
            f.write(response.content)

    print(f"✓ Exported portfolio to {filename}")
    return filename

# Export to JSON
json_file = export_portfolio(defi_portfolio['id'], format="json")

# Export to CSV
csv_file = export_portfolio(defi_portfolio['id'], format="csv")
```

## Step 11: Delete Portfolio

```python
def delete_portfolio(portfolio_id):
    """Delete a portfolio (cannot be undone)"""

    response = requests.delete(
        f"{BASE_URL}/portfolios/{portfolio_id}",
        headers=headers
    )

    response.raise_for_status()
    print(f"✓ Deleted portfolio: {portfolio_id}")

# Example: Delete a portfolio (use with caution!)
# delete_portfolio(nft_portfolio['id'])
```

## Complete Example Workflow

```python
def main():
    """Complete portfolio management workflow"""

    print("=== ChainFinity Portfolio Management Example ===\n")

    # 1. Authentication
    print("Step 1: Authenticating...")
    # (authentication code from above)

    # 2. Create portfolio
    print("\nStep 2: Creating portfolio...")
    portfolio = create_portfolio(
        name="Diversified Crypto Portfolio",
        description="Multi-chain crypto holdings",
        tags=["crypto", "diversified"]
    )

    # 3. Add assets
    print("\nStep 3: Adding assets...")
    assets = [
        {
            "token_address": "0x0000000000000000000000000000000000000000",
            "symbol": "ETH",
            "name": "Ethereum",
            "amount": "5.0",
            "chain": "ethereum",
            "decimals": 18
        },
        {
            "token_address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
            "symbol": "WBTC",
            "name": "Wrapped Bitcoin",
            "amount": "0.5",
            "chain": "ethereum",
            "decimals": 8
        }
    ]

    for asset_data in assets:
        add_asset_to_portfolio(portfolio['id'], asset_data)

    # 4. View portfolio
    print("\nStep 4: Viewing portfolio details...")
    details = get_portfolio_details(portfolio['id'])

    # 5. Get performance
    print("\nStep 5: Analyzing performance...")
    performance = get_portfolio_performance(portfolio['id'], period="7d")

    # 6. Export data
    print("\nStep 6: Exporting portfolio...")
    export_portfolio(portfolio['id'], format="json")

    print("\n=== Portfolio Management Complete ===")
    print(f"Portfolio ID: {portfolio['id']}")
    print(f"Total Value: ${details['total_value_usd']:,.2f}")
    print(f"7-day Return: {performance['percentage_return']:.2f}%")

if __name__ == "__main__":
    main()
```

## Expected Output

```text
=== ChainFinity Portfolio Management Example ===

Step 1: Authenticating...
✓ Authenticated successfully

Step 2: Creating portfolio...
✓ Created portfolio: 550e8400-e29b-41d4-a716-446655440000
  Name: Diversified Crypto Portfolio
  Created: 2025-01-08T12:00:00Z

Step 3: Adding assets...
✓ Added asset: ETH
  Amount: 5.0
  Value: $12500.00
✓ Added asset: WBTC
  Amount: 0.5
  Value: $25000.00

Step 4: Viewing portfolio details...

=== Portfolio Details: Diversified Crypto Portfolio ===
ID: 550e8400-e29b-41d4-a716-446655440000
Description: Multi-chain crypto holdings
Total Value: $37,500.00
Risk Score: 6.5
Created: 2025-01-08T12:00:00Z

Assets:
  ETH (ethereum)
    Amount: 5.0
    Value: $12,500.00
    Percentage: 33.33%

  WBTC (ethereum)
    Amount: 0.5
    Value: $25,000.00
    Percentage: 66.67%

Risk Metrics:
  Volatility: 0.45
  Sharpe Ratio: 1.8
  VaR (95%): 0.15
  Max Drawdown: 0.22

Step 5: Analyzing performance...

=== Performance (7d) ===
Starting Value: $35,000.00
Current Value: $37,500.00
Absolute Return: $2,500.00
Percentage Return: 7.14%
Volatility: 12.50%
Sharpe Ratio: 1.95

Step 6: Exporting portfolio...
✓ Exported portfolio to portfolio_550e8400-e29b-41d4-a716-446655440000.json

=== Portfolio Management Complete ===
Portfolio ID: 550e8400-e29b-41d4-a716-446655440000
Total Value: $37,500.00
7-day Return: 7.14%
```

## Next Steps

- Review [Risk Analysis Example](./risk-analysis.md)
- Check [API Reference](../API.md#portfolio-endpoints)
- Explore [Cross-Chain Transfer Example](./cross-chain-transfer.md)
- See [Usage Guide](../USAGE.md) for more workflows

## Related Documentation

- [API Documentation](../API.md)
- [Architecture](../ARCHITECTURE.md)
- [Troubleshooting](../TROUBLESHOOTING.md#api-issues)

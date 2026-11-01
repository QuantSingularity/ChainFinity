# Risk Analysis Example

This example demonstrates how to perform comprehensive risk assessment on portfolios using ChainFinity's AI-powered risk analysis features.

## Overview

ChainFinity provides advanced risk assessment capabilities including:

- AI-powered risk scoring (0-10 scale)
- Volatility analysis
- Value at Risk (VaR) calculations
- Sharpe ratio and other performance metrics
- Portfolio concentration analysis
- AI-driven recommendations

## Prerequisites

- Existing portfolio with assets
- Access token from authentication
- Basic understanding of risk metrics

## Step 1: Assess Portfolio Risk

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

def assess_portfolio_risk(portfolio_id):
    """Run comprehensive risk assessment on a portfolio"""

    response = requests.post(
        f"{BASE_URL}/risk/assess/{portfolio_id}",
        headers=headers
    )

    response.raise_for_status()
    assessment = response.json()

    print(f"\n=== Risk Assessment ===")
    print(f"Portfolio: {portfolio_id}")
    print(f"Assessment ID: {assessment['id']}")
    print(f"Risk Score: {assessment['risk_score']:.1f}/10")
    print(f"Risk Level: {assessment['risk_level']}")
    print(f"Assessed at: {assessment['created_at']}")
    print()

    # Risk metrics
    metrics = assessment['metrics']
    print("Risk Metrics:")
    print(f"  Volatility: {metrics['volatility']:.2%}")
    print(f"  Value at Risk (95%): {metrics['var_95']:.2%}")
    print(f"  Value at Risk (99%): {metrics['var_99']:.2%}")
    print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {metrics['max_drawdown']:.2%}")
    print(f"  Beta: {metrics.get('beta', 'N/A')}")
    print()

    # Concentration analysis
    if 'concentration' in assessment:
        conc = assessment['concentration']
        print("Concentration Analysis:")
        print(f"  Top Asset: {conc['top_asset']} ({conc['top_asset_percentage']:.1f}%)")
        print(f"  Top 3 Assets: {conc['top_3_percentage']:.1f}%")
        print(f"  Herfindahl Index: {conc['herfindahl_index']:.4f}")
        print()

    # AI Recommendations
    if 'recommendations' in assessment:
        print("AI Recommendations:")
        for i, rec in enumerate(assessment['recommendations'], 1):
            print(f"  {i}. {rec}")
        print()

    return assessment

# Example: Assess a portfolio
portfolio_id = "550e8400-e29b-41d4-a716-446655440000"
assessment = assess_portfolio_risk(portfolio_id)
```

## Step 2: Interpret Risk Score

```python
def interpret_risk_score(risk_score):
    """Provide human-readable interpretation of risk score"""

    interpretations = {
        (0, 2): {
            "level": "Very Low Risk",
            "description": "Conservative portfolio with minimal volatility",
            "suitable_for": "Risk-averse investors, retirees",
            "characteristics": [
                "Stable value preservation",
                "Low expected returns",
                "Minimal drawdowns"
            ]
        },
        (2, 4): {
            "level": "Low Risk",
            "description": "Low volatility with modest growth potential",
            "suitable_for": "Conservative investors",
            "characteristics": [
                "Balanced stability and growth",
                "Moderate returns",
                "Limited downside"
            ]
        },
        (4, 6): {
            "level": "Moderate Risk",
            "description": "Balanced risk-reward profile",
            "suitable_for": "Moderate investors with medium-term horizon",
            "characteristics": [
                "Diversified holdings",
                "Reasonable returns",
                "Acceptable volatility"
            ]
        },
        (6, 8): {
            "level": "High Risk",
            "description": "Growth-oriented with significant volatility",
            "suitable_for": "Aggressive investors with long time horizon",
            "characteristics": [
                "High growth potential",
                "Significant volatility",
                "Potential for large drawdowns"
            ]
        },
        (8, 11): {
            "level": "Very High Risk",
            "description": "Speculative portfolio with extreme volatility",
            "suitable_for": "Speculative traders, high risk tolerance",
            "characteristics": [
                "Extreme volatility",
                "High return potential",
                "Substantial loss risk"
            ]
        }
    }

    for (min_score, max_score), info in interpretations.items():
        if min_score <= risk_score < max_score:
            print(f"\n=== Risk Interpretation ===")
            print(f"Score: {risk_score:.1f}/10")
            print(f"Level: {info['level']}")
            print(f"\nDescription: {info['description']}")
            print(f"\nSuitable for: {info['suitable_for']}")
            print(f"\nCharacteristics:")
            for char in info['characteristics']:
                print(f"  • {char}")
            return info

    return None

# Interpret the risk score
interpret_risk_score(assessment['risk_score'])
```

## Step 3: Historical Risk Metrics

```python
def get_historical_risk(portfolio_id, period="30d"):
    """Get historical risk metrics over time"""

    response = requests.get(
        f"{BASE_URL}/risk/assessments/history/{portfolio_id}",
        params={"period": period},
        headers=headers
    )

    response.raise_for_status()
    history = response.json()

    print(f"\n=== Historical Risk ({period}) ===")
    print(f"Data points: {len(history['data'])}")
    print()

    # Calculate trends
    scores = [point['risk_score'] for point in history['data']]
    volatilities = [point['volatility'] for point in history['data']]

    print(f"Risk Score:")
    print(f"  Current: {scores[-1]:.1f}")
    print(f"  Average: {sum(scores)/len(scores):.1f}")
    print(f"  Min: {min(scores):.1f}")
    print(f"  Max: {max(scores):.1f}")
    print()

    print(f"Volatility:")
    print(f"  Current: {volatilities[-1]:.2%}")
    print(f"  Average: {sum(volatilities)/len(volatilities):.2%}")
    print(f"  Min: {min(volatilities):.2%}")
    print(f"  Max: {max(volatilities):.2%}")
    print()

    return history

# Get 30-day risk history
risk_history = get_historical_risk(portfolio_id, period="30d")
```

## Step 4: Compare with Market Benchmark

```python
def compare_with_benchmark(portfolio_id, benchmark="ETH"):
    """Compare portfolio risk metrics with market benchmark"""

    response = requests.get(
        f"{BASE_URL}/risk/benchmark/{portfolio_id}",
        params={"benchmark": benchmark},
        headers=headers
    )

    response.raise_for_status()
    comparison = response.json()

    print(f"\n=== Benchmark Comparison ===")
    print(f"Benchmark: {benchmark}")
    print()

    # Risk metrics comparison
    print("Risk Metrics vs Benchmark:")
    for metric, values in comparison['metrics'].items():
        portfolio_val = values['portfolio']
        benchmark_val = values['benchmark']
        diff = portfolio_val - benchmark_val
        diff_pct = (diff / benchmark_val * 100) if benchmark_val != 0 else 0

        print(f"  {metric.replace('_', ' ').title()}:")
        print(f"    Portfolio: {portfolio_val:.4f}")
        print(f"    Benchmark: {benchmark_val:.4f}")
        print(f"    Difference: {diff:+.4f} ({diff_pct:+.1f}%)")
        print()

    # Correlation
    print(f"Correlation with {benchmark}: {comparison['correlation']:.2f}")
    print(f"Beta: {comparison['beta']:.2f}")
    print()

    return comparison

# Compare with ETH
benchmark_comparison = compare_with_benchmark(portfolio_id, benchmark="ETH")
```

## Step 5: Stress Testing

```python
def stress_test_portfolio(portfolio_id, scenarios):
    """Run stress test scenarios on portfolio"""

    response = requests.post(
        f"{BASE_URL}/risk/stress-test/{portfolio_id}",
        json={"scenarios": scenarios},
        headers=headers
    )

    response.raise_for_status()
    results = response.json()

    print(f"\n=== Stress Test Results ===")

    for scenario in results['scenarios']:
        print(f"\nScenario: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print(f"Impact:")
        print(f"  Current Value: ${scenario['current_value']:,.2f}")
        print(f"  Stressed Value: ${scenario['stressed_value']:,.2f}")
        print(f"  Loss: ${scenario['loss']:,.2f} ({scenario['loss_percentage']:.2f}%)")

        # Individual asset impacts
        if 'asset_impacts' in scenario:
            print(f"  Asset Impacts:")
            for asset in scenario['asset_impacts']:
                print(f"    {asset['symbol']}: {asset['impact']:+.2%}")

    return results

# Define stress test scenarios
scenarios = [
    {
        "name": "Market Crash (-50%)",
        "description": "Severe market downturn across all assets",
        "price_changes": {"*": -0.50}  # 50% drop across all assets
    },
    {
        "name": "Ethereum Crash (-70%)",
        "description": "ETH-specific crash",
        "price_changes": {"ETH": -0.70}
    },
    {
        "name": "DeFi Crisis",
        "description": "DeFi token devaluation",
        "price_changes": {
            "AAVE": -0.60,
            "UNI": -0.55,
            "COMP": -0.65
        }
    }
]

stress_results = stress_test_portfolio(portfolio_id, scenarios)
```

## Step 6: Risk Recommendations

```python
def get_risk_recommendations(portfolio_id):
    """Get AI-generated risk mitigation recommendations"""

    response = requests.get(
        f"{BASE_URL}/risk/recommendations/{portfolio_id}",
        headers=headers
    )

    response.raise_for_status()
    recommendations = response.json()

    print(f"\n=== Risk Mitigation Recommendations ===\n")

    # Prioritized recommendations
    for i, rec in enumerate(recommendations['recommendations'], 1):
        print(f"{i}. {rec['title']}")
        print(f"   Priority: {rec['priority']}")
        print(f"   Impact: {rec['estimated_impact']}")
        print(f"   Description: {rec['description']}")

        if 'action_steps' in rec:
            print(f"   Action Steps:")
            for step in rec['action_steps']:
                print(f"     • {step}")
        print()

    return recommendations

# Get recommendations
recommendations = get_risk_recommendations(portfolio_id)
```

## Step 7: Set Risk Alerts

```python
def set_risk_alerts(portfolio_id, alert_config):
    """Configure risk alert thresholds"""

    response = requests.post(
        f"{BASE_URL}/risk/alerts/{portfolio_id}",
        json=alert_config,
        headers=headers
    )

    response.raise_for_status()
    alerts = response.json()

    print(f"✓ Risk alerts configured:")
    for alert in alerts['alerts']:
        print(f"  • {alert['type']}: {alert['threshold']}")

    return alerts

# Configure alerts
alert_config = {
    "alerts": [
        {
            "type": "risk_score",
            "threshold": 8.0,
            "condition": "above",
            "notification": "email"
        },
        {
            "type": "volatility",
            "threshold": 0.50,
            "condition": "above",
            "notification": "email"
        },
        {
            "type": "drawdown",
            "threshold": 0.20,
            "condition": "above",
            "notification": "email"
        },
        {
            "type": "value_loss",
            "threshold": 10000,  # USD
            "condition": "below",
            "notification": "email"
        }
    ]
}

alerts = set_risk_alerts(portfolio_id, alert_config)
```

## Complete Risk Analysis Workflow

```python
def complete_risk_analysis(portfolio_id):
    """Perform comprehensive risk analysis"""

    print("=" * 60)
    print("ChainFinity Portfolio Risk Analysis")
    print("=" * 60)

    # 1. Initial assessment
    print("\n[1/6] Running risk assessment...")
    assessment = assess_portfolio_risk(portfolio_id)

    # 2. Interpret results
    print("\n[2/6] Interpreting risk score...")
    interpret_risk_score(assessment['risk_score'])

    # 3. Historical analysis
    print("\n[3/6] Analyzing historical risk...")
    history = get_historical_risk(portfolio_id, period="30d")

    # 4. Benchmark comparison
    print("\n[4/6] Comparing with benchmark...")
    benchmark = compare_with_benchmark(portfolio_id, benchmark="ETH")

    # 5. Stress testing
    print("\n[5/6] Running stress tests...")
    stress_scenarios = [
        {
            "name": "Market Correction (-30%)",
            "description": "Moderate market downturn",
            "price_changes": {"*": -0.30}
        }
    ]
    stress_results = stress_test_portfolio(portfolio_id, stress_scenarios)

    # 6. Get recommendations
    print("\n[6/6] Generating recommendations...")
    recommendations = get_risk_recommendations(portfolio_id)

    # Summary
    print("\n" + "=" * 60)
    print("Analysis Complete")
    print("=" * 60)
    print(f"\nRisk Score: {assessment['risk_score']:.1f}/10")
    print(f"Risk Level: {assessment['risk_level']}")
    print(f"Volatility: {assessment['metrics']['volatility']:.2%}")
    print(f"Sharpe Ratio: {assessment['metrics']['sharpe_ratio']:.2f}")
    print(f"\nRecommendations: {len(recommendations['recommendations'])}")
    print("\nNext Steps:")
    print("  1. Review AI recommendations")
    print("  2. Consider diversification improvements")
    print("  3. Set up risk alerts")
    print("  4. Monitor portfolio regularly")

if __name__ == "__main__":
    # Run complete analysis
    portfolio_id = "550e8400-e29b-41d4-a716-446655440000"
    complete_risk_analysis(portfolio_id)
```

## Expected Output

```text
============================================================
ChainFinity Portfolio Risk Analysis
============================================================

[1/6] Running risk assessment...

=== Risk Assessment ===
Portfolio: 550e8400-e29b-41d4-a716-446655440000
Assessment ID: assessment-uuid
Risk Score: 6.5/10
Risk Level: Moderate-High
Assessed at: 2025-01-08T12:00:00Z

Risk Metrics:
  Volatility: 45.30%
  Value at Risk (95%): 15.20%
  Value at Risk (99%): 22.50%
  Sharpe Ratio: 1.80
  Max Drawdown: 22.10%
  Beta: 1.15

Concentration Analysis:
  Top Asset: ETH (45.0%)
  Top 3 Assets: 85.0%
  Herfindahl Index: 0.2850

AI Recommendations:
  1. Consider diversifying to reduce ETH concentration
  2. Add stablecoins to reduce overall volatility
  3. Explore DeFi yield opportunities for better risk-adjusted returns

[2/6] Interpreting risk score...

=== Risk Interpretation ===
Score: 6.5/10
Level: High Risk

Description: Growth-oriented with significant volatility

Suitable for: Aggressive investors with long time horizon

Characteristics:
  • High growth potential
  • Significant volatility
  • Potential for large drawdowns

[3/6] Analyzing historical risk...

=== Historical Risk (30d) ===
Data points: 30

Risk Score:
  Current: 6.5
  Average: 6.3
  Min: 5.8
  Max: 7.2

Volatility:
  Current: 45.30%
  Average: 42.50%
  Min: 38.20%
  Max: 48.70%

[... additional output ...]

============================================================
Analysis Complete
============================================================

Risk Score: 6.5/10
Risk Level: Moderate-High
Volatility: 45.30%
Sharpe Ratio: 1.80

Recommendations: 5

Next Steps:
  1. Review AI recommendations
  2. Consider diversification improvements
  3. Set up risk alerts
  4. Monitor portfolio regularly
```

## Understanding Risk Metrics

### Key Metrics Explained

| Metric           | Range    | Description                            | Interpretation                                           |
| ---------------- | -------- | -------------------------------------- | -------------------------------------------------------- |
| **Risk Score**   | 0-10     | Overall risk level                     | <4: Low, 4-6: Moderate, 6-8: High, >8: Very High         |
| **Volatility**   | 0-100%+  | Price variation                        | <20%: Low, 20-40%: Moderate, 40-60%: High, >60%: Extreme |
| **VaR (95%)**    | 0-100%   | Maximum expected loss (95% confidence) | Portfolio loss not to exceed this 95% of the time        |
| **Sharpe Ratio** | -∞ to +∞ | Risk-adjusted return                   | <1: Poor, 1-2: Good, 2-3: Very Good, >3: Excellent       |
| **Max Drawdown** | 0-100%   | Largest peak-to-trough decline         | <10%: Low, 10-30%: Moderate, >30%: High                  |
| **Beta**         | -∞ to +∞ | Sensitivity to market                  | <1: Less volatile, 1: Same, >1: More volatile            |

## Next Steps

- Review [Portfolio Management Example](./portfolio-management.md)
- Check [Cross-Chain Transfer Example](./cross-chain-transfer.md)
- See [API Reference](../API.md#risk-assessment-endpoints)
- Explore [Usage Guide](../USAGE.md)

## Related Documentation

- [API Documentation](../API.md)
- [Architecture](../ARCHITECTURE.md#aiml-components)
- [Troubleshooting](../TROUBLESHOOTING.md)

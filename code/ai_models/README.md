# ChainFinity AI Models

Risk and market-intelligence models used by the ChainFinity backend. The package is imported as `ai_models`.

## Layout

```
ai_models/
  __init__.py            Public API (lazy exports, __version__)
  __main__.py            python -m ai_models
  cli.py                 Training and artifact inspection CLI
  core/
    compat.py            Lazy TensorFlow detection and loading
    persistence.py       Versioned, checksummed model artifacts
    registry.py          Model names, artifact directory names
  preprocessing/
    ohlcv.py             Validation, imputation, features, sequences, scaling
  models/
    volatility/          LSTM volatility forecaster and EWMA fallback
    correlation/         LSTM correlation predictor and Ledoit-Wolf fallback
    exploit/             Isolation forest and LSTM autoencoder exploit detector
    liquidity/           Rule-based liquidity crisis detector
    smart_money/         Wallet clustering, scoring, PageRank centrality, signals
  tests/                 Unit tests (no GPU or network needed)
  pyproject.toml         Packaging and tool configuration
  requirements*.txt      Core, ML (TensorFlow) and dev dependencies
```

## Install

```
pip install -r requirements.txt
pip install -r requirements-ml.txt
```

TensorFlow is optional. Without it the volatility and correlation models fall back to EWMA and Ledoit-Wolf shrinkage, and the exploit detector runs without its autoencoder stage.

## Usage

```python
from ai_models import VolatilityForecaster, ewma_volatility_forecast

forecaster = VolatilityForecaster().fit(ohlcv_frame, epochs=50)
forecast = forecaster.predict(ohlcv_frame)
forecaster.save("ai_artifacts/volatility_forecaster")
forecaster = VolatilityForecaster.load("ai_artifacts/volatility_forecaster")
```

| Model       | Class                     | Input                                  | Output                                                  |
| ----------- | ------------------------- | -------------------------------------- | ------------------------------------------------------- |
| Volatility  | `VolatilityForecaster`    | OHLCV frame, datetime index            | Forward annualised volatility with Monte Carlo interval |
| Correlation | `CorrelationPredictor`    | Prices, columns prefixed `asset_`      | Valid correlation matrix                                |
| Exploit     | `ExploitDetector`         | On-chain feature frame                 | Risk score, severity, alerts                            |
| Liquidity   | `LiquidityCrisisDetector` | TVL, spread, peg price, returns series | Component scores, alert level                           |
| Smart money | `SmartMoneyTracker`       | Wallet feature frame, transactions     | Profiles, signals, flows                                |

## CLI

```
python -m ai_models train volatility --data prices.csv --artifacts-dir ai_artifacts
python -m ai_models train correlation --data asset_prices.csv
python -m ai_models train exploit --data onchain.csv
python -m ai_models train smart_money --data wallets.csv --clusters 5
python -m ai_models inspect --artifacts-dir ai_artifacts
```

Input CSVs use a `timestamp` column (volatility, correlation, exploit) or an `address` column (smart money) as the index.

## Artifacts

Each artifact directory contains `meta.json` (schema version, model type, SHA-256 checksums), `state.joblib` and, for neural models, `.keras` files. Loading verifies the schema version, model type and checksums before deserialising. Only load artifacts from trusted locations.

## Backend integration

The backend loads artifacts from `AI_ARTIFACTS_DIR` at startup and serves them under `/api/v1/ai`. Missing artifacts never break the API: each model has a documented fallback and the response reports which mode produced it.

## Tests

```
pip install -r requirements-dev.txt
pytest
```

import numpy as np
import pandas as pd


def make_ohlcv(n: int = 200, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100 * np.cumprod(1 + rng.normal(0, 0.02, n))
    high = close * (1 + rng.uniform(0, 0.02, n))
    low = close * (1 - rng.uniform(0, 0.02, n))
    return pd.DataFrame(
        {
            "open": close * (1 + rng.normal(0, 0.005, n)),
            "high": high,
            "low": low,
            "close": close,
            "volume": rng.uniform(1e6, 1e7, n),
        },
        index=pd.date_range("2023-01-01", periods=n, freq="1D"),
    )


def make_wallet_df(n: int = 100, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    addrs = [f"0x{i:040x}" for i in range(n)]
    return pd.DataFrame(
        {
            "total_volume_usd_30d": rng.uniform(1e4, 1e8, n),
            "tx_count_30d": rng.integers(1, 500, n),
            "unique_protocols_30d": rng.integers(1, 20, n),
            "unique_chains": rng.integers(1, 8, n),
            "avg_hold_days": rng.uniform(0.5, 180, n),
            "pnl_30d_pct": rng.uniform(-0.5, 2.0, n),
            "pnl_90d_pct": rng.uniform(-0.8, 5.0, n),
            "win_rate": rng.uniform(0.2, 0.9, n),
            "max_single_trade_usd": rng.uniform(1e3, 5e6, n),
            "avg_trade_size_usd": rng.uniform(100, 5e5, n),
            "early_entry_ratio": rng.uniform(0, 1, n),
            "exit_timing_score": rng.uniform(0, 1, n),
            "bridge_frequency": rng.uniform(0, 1, n),
            "flash_loan_usage": rng.uniform(0, 0.3, n),
        },
        index=addrs,
    )


def make_onchain_df(n: int = 150, seed: int = 99) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "flash_loan_volume_usd": rng.uniform(0, 5e5, n),
            "large_tx_count": rng.integers(0, 20, n),
            "unique_callers": rng.integers(5, 500, n),
            "reentrancy_depth_max": rng.integers(1, 10, n),
            "token_mint_rate": rng.uniform(0, 1, n),
            "price_impact_pct": rng.uniform(0, 0.1, n),
            "tvl_change_pct": rng.normal(0, 0.02, n),
            "gas_price_percentile": rng.uniform(0, 1, n),
            "failed_tx_ratio": rng.uniform(0, 0.3, n),
            "contract_interaction_entropy": rng.uniform(0.5, 1, n),
        },
        index=pd.date_range("2023-01-01", periods=n, freq="1h"),
    )


def make_prices(
    n: int = 160, seed: int = 11, assets=("btc", "eth", "sol")
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    shared = rng.normal(0, 0.02, n)
    data = {
        f"asset_{name}": 100 * np.cumprod(1 + 0.6 * shared + rng.normal(0, 0.015, n))
        for name in assets
    }
    return pd.DataFrame(data, index=pd.date_range("2024-01-01", periods=n, freq="D"))

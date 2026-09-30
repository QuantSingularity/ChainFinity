"""
ChainFinity AI Models - Data Preprocessing Pipeline
Shared utilities used by all model modules:
  - VolatilityForecaster
  - CorrelationPredictor
  - ExploitDetector
  - SmartMoneyTracker
  - LiquidityCrisisDetector
"""

import logging
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

logger = logging.getLogger(__name__)

REQUIRED_OHLCV_COLS = ["open", "high", "low", "close", "volume"]

ImputeStrategy = Union[str, float]
ScalerType = Union[MinMaxScaler, StandardScaler, RobustScaler]


def validate_ohlcv(df: pd.DataFrame, strict: bool = False) -> pd.DataFrame:
    """Validate and coerce an OHLCV DataFrame.

    Operates on a copy so the caller's DataFrame is never mutated.
    """
    df = df.copy()
    if "close" not in df.columns:
        raise ValueError("DataFrame must contain a 'close' column.")
    if strict:
        missing = [c for c in REQUIRED_OHLCV_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required OHLCV columns: {missing}")
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            neg = (df[col] < 0).sum()
            if neg:
                logger.warning(
                    "Column '%s' has %d negative values - set to NaN.", col, neg
                )
                df.loc[df[col] < 0, col] = np.nan
    if "high" in df.columns and "low" in df.columns:
        swapped = df["high"] < df["low"]
        if swapped.any():
            df.loc[swapped, ["high", "low"]] = df.loc[swapped, ["low", "high"]].values
    if df.index.duplicated().any():
        df = df[~df.index.duplicated(keep="last")]
    df.sort_index(inplace=True)
    if "volume" in df.columns:
        df.loc[df["volume"] == 0, "volume"] = np.nan
        df["volume"] = df["volume"].ffill()
    return df


def impute_missing(
    df: pd.DataFrame,
    strategy: ImputeStrategy = "ffill",
    max_gap: int = 5,
) -> pd.DataFrame:
    """Impute missing values in a time-series DataFrame."""
    df = df.copy()
    if strategy == "ffill":
        df = df.ffill(limit=max_gap)
    elif strategy == "linear":
        df = df.interpolate(method="linear", limit=max_gap)
        df = df.ffill(limit=max_gap)
    elif strategy == "median":
        imp = SimpleImputer(strategy="median")
        df[:] = imp.fit_transform(df.values)
    elif isinstance(strategy, (int, float)):
        df.fillna(strategy, inplace=True)
    else:
        raise ValueError(f"Unknown impute strategy: {strategy!r}")
    remaining = df.isna().sum().sum()
    if remaining:
        logger.warning("%d NaN values remain after imputation.", remaining)
    return df


def clip_outliers_iqr(
    df: pd.DataFrame,
    cols: Optional[List[str]] = None,
    iqr_multiplier: float = 3.0,
) -> pd.DataFrame:
    """Clip values beyond median ± iqr_multiplier × IQR for each column."""
    df = df.copy()
    target_cols = cols or df.select_dtypes(include=np.number).columns.tolist()
    for col in target_cols:
        if col not in df.columns:
            continue
        q25, q75 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q75 - q25
        df[col] = df[col].clip(q25 - iqr_multiplier * iqr, q75 + iqr_multiplier * iqr)
    return df


def get_scaler(scaler_type: str = "minmax") -> ScalerType:
    """Return a fresh sklearn scaler instance."""
    mapping: Dict[str, ScalerType] = {
        "minmax": MinMaxScaler(feature_range=(0, 1)),
        "standard": StandardScaler(),
        "robust": RobustScaler(),
    }
    if scaler_type not in mapping:
        raise ValueError(
            f"Unknown scaler: {scaler_type!r}. Choose from {list(mapping)}"
        )
    return mapping[scaler_type]


def add_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add common technical analysis features to an OHLCV DataFrame."""
    df = df.copy()
    close = df["close"]

    df["feat_log_return"] = np.log(close / close.shift(1))
    df["feat_return_1d"] = close.pct_change(1)
    df["feat_return_7d"] = close.pct_change(7)

    for w in (7, 14, 30):
        df[f"feat_vol_{w}d"] = df["feat_log_return"].rolling(w).std() * np.sqrt(252)
        df[f"feat_sma_{w}"] = close.rolling(w).mean()
        df[f"feat_ema_{w}"] = close.ewm(span=w, adjust=False).mean()

    df["feat_price_to_sma30"] = close / df["feat_sma_30"].replace(0, np.nan)

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta).clip(lower=0).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["feat_rsi_14"] = 100 - (100 / (1 + rs))

    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    bb_up = sma20 + 2 * std20
    bb_lo = sma20 - 2 * std20
    bb_width = (bb_up - bb_lo) / sma20.replace(0, np.nan)
    df["feat_bb_width"] = bb_width
    df["feat_bb_position"] = (close - bb_lo) / ((bb_up - bb_lo).replace(0, np.nan))

    if "high" in df.columns and "low" in df.columns:
        df["feat_hl_range"] = (df["high"] - df["low"]) / close.replace(0, np.nan)
        hl = df["high"] - df["low"]
        hc = (df["high"] - close.shift(1)).abs()
        lc = (df["low"] - close.shift(1)).abs()
        df["feat_atr_14"] = (
            pd.concat([hl, hc, lc], axis=1).max(axis=1).rolling(14).mean()
        )

    if "volume" in df.columns:
        vol_sma = df["volume"].rolling(14).mean()
        df["feat_volume_ratio"] = df["volume"] / vol_sma.replace(0, np.nan)
        direction = np.sign(df["feat_log_return"].fillna(0))
        df["feat_obv"] = (direction * df["volume"]).cumsum()

    return df


def build_sequences(
    features: np.ndarray,
    targets: np.ndarray,
    sequence_length: int,
    step: int = 1,
) -> Tuple[np.ndarray, np.ndarray]:
    """Construct (X, y) pairs for supervised LSTM training."""
    X, y = [], []
    for i in range(0, len(features) - sequence_length, step):
        X.append(features[i : i + sequence_length])
        y.append(targets[i + sequence_length])
    return np.array(X), np.array(y)


def build_autoencoder_sequences(
    features: np.ndarray,
    sequence_length: int,
    step: int = 1,
) -> np.ndarray:
    """Unsupervised sequences for autoencoder training (X only)."""
    seqs = []
    for i in range(0, len(features) - sequence_length + 1, step):
        seqs.append(features[i : i + sequence_length])
    return np.array(seqs)


def time_split(
    df: pd.DataFrame,
    val_frac: float = 0.10,
    test_frac: float = 0.10,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split a time-ordered DataFrame into train/val/test without shuffling."""
    n = len(df)
    n_test = max(1, int(n * test_frac))
    n_val = max(1, int(n * val_frac))
    n_train = n - n_val - n_test
    if n_train < 1:
        raise ValueError(
            f"Not enough data ({n} rows) for the requested split fractions."
        )
    return (
        df.iloc[:n_train],
        df.iloc[n_train : n_train + n_val],
        df.iloc[n_train + n_val :],
    )


def align_multi_chain(
    chain_dfs: Dict[str, "pd.DataFrame"],
    freq: str = "1h",
    fill_strategy: ImputeStrategy = "ffill",
) -> "pd.DataFrame":
    """Resample and align price DataFrames from multiple chains to a common index."""
    resampled: Dict[str, pd.Series] = {}
    for name, df in chain_dfs.items():
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        resampled[name] = df["close"].resample(freq).last()
    combined = pd.DataFrame(resampled)
    combined = impute_missing(combined, strategy=fill_strategy)
    combined.dropna(how="all", inplace=True)
    logger.info(
        "Aligned %d chains, %d timesteps at freq=%s.",
        len(chain_dfs),
        len(combined),
        freq,
    )
    return combined


def preprocess_ohlcv(
    df: pd.DataFrame,
    scaler_type: str = "minmax",
    add_features: bool = True,
    outlier_clip: bool = True,
    impute_strategy: ImputeStrategy = "ffill",
) -> Tuple["pd.DataFrame", ScalerType]:
    """
    Full preprocessing pipeline for a single OHLCV DataFrame.
    Returns (processed_df, fitted_scaler).
    """
    df = validate_ohlcv(df.copy())
    df = impute_missing(df, strategy=impute_strategy)
    if outlier_clip:
        df = clip_outliers_iqr(df, cols=["close", "volume"])
    if add_features:
        df = add_technical_features(df)
    df.dropna(inplace=True)
    scaler = get_scaler(scaler_type)
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols].values)
    logger.info(
        "Preprocessing complete: %d rows × %d features.", len(df), len(numeric_cols)
    )
    return df, scaler

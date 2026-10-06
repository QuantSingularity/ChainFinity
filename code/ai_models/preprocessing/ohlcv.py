import logging
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

logger = logging.getLogger(__name__)

ANNUALIZATION_FACTOR = 365
REQUIRED_OHLCV_COLS = ["open", "high", "low", "close", "volume"]
PRICE_COLS = ["open", "high", "low", "close"]

ImputeStrategy = Union[str, float]
ScalerType = Union[MinMaxScaler, StandardScaler, RobustScaler]


def validate_ohlcv(df: pd.DataFrame, strict: bool = False) -> pd.DataFrame:
    if "close" not in df.columns:
        raise ValueError("DataFrame must contain a 'close' column.")
    if strict:
        missing = [c for c in REQUIRED_OHLCV_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required OHLCV columns: {missing}")
    df = df.copy()
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in PRICE_COLS:
        if col in df.columns:
            invalid = df[col] <= 0
            if invalid.any():
                logger.warning(
                    "Column '%s' has %d non-positive values; set to NaN.",
                    col,
                    int(invalid.sum()),
                )
                df.loc[invalid, col] = np.nan
    if "volume" in df.columns:
        negative = df["volume"] < 0
        if negative.any():
            logger.warning(
                "Column 'volume' has %d negative values; set to NaN.",
                int(negative.sum()),
            )
            df.loc[negative, "volume"] = np.nan
    if "high" in df.columns and "low" in df.columns:
        swapped = df["high"] < df["low"]
        if swapped.any():
            df.loc[swapped, ["high", "low"]] = df.loc[swapped, ["low", "high"]].values
    if df.index.duplicated().any():
        df = df[~df.index.duplicated(keep="last")]
    df = df.sort_index()
    if "volume" in df.columns:
        df.loc[df["volume"] == 0, "volume"] = np.nan
        df["volume"] = df["volume"].ffill()
    return df


def impute_missing(
    df: pd.DataFrame,
    strategy: ImputeStrategy = "ffill",
    max_gap: int = 5,
) -> pd.DataFrame:
    df = df.copy()
    if isinstance(strategy, bool):
        raise ValueError(f"Unknown impute strategy: {strategy!r}")
    if isinstance(strategy, str):
        if strategy == "ffill":
            df = df.ffill(limit=max_gap)
        elif strategy == "linear":
            df = df.interpolate(method="linear", limit=max_gap).ffill(limit=max_gap)
        elif strategy == "median":
            df = df.fillna(df.median(numeric_only=True))
        else:
            raise ValueError(f"Unknown impute strategy: {strategy!r}")
    elif isinstance(strategy, (int, float)):
        df = df.fillna(strategy)
    else:
        raise ValueError(f"Unknown impute strategy: {strategy!r}")
    remaining = int(df.isna().sum().sum())
    if remaining:
        logger.warning("%d NaN values remain after imputation.", remaining)
    return df


def clip_outliers_iqr(
    df: pd.DataFrame,
    cols: Optional[List[str]] = None,
    iqr_multiplier: float = 3.0,
) -> pd.DataFrame:
    df = df.copy()
    target_cols = cols or df.select_dtypes(include=np.number).columns.tolist()
    for col in target_cols:
        if col not in df.columns:
            continue
        q25, q75 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q75 - q25
        if not np.isfinite(iqr) or iqr == 0:
            continue
        df[col] = df[col].clip(q25 - iqr_multiplier * iqr, q75 + iqr_multiplier * iqr)
    return df


def get_scaler(scaler_type: str = "minmax") -> ScalerType:
    factories = {
        "minmax": lambda: MinMaxScaler(feature_range=(0, 1)),
        "standard": StandardScaler,
        "robust": RobustScaler,
    }
    if scaler_type not in factories:
        raise ValueError(
            f"Unknown scaler: {scaler_type!r}. Choose from {list(factories)}"
        )
    return factories[scaler_type]()


def add_technical_features(
    df: pd.DataFrame, periods_per_year: int = ANNUALIZATION_FACTOR
) -> pd.DataFrame:
    df = df.copy()
    close = df["close"]
    annualizer = np.sqrt(periods_per_year)

    df["feat_log_return"] = np.log(close / close.shift(1))
    df["feat_return_1d"] = close.pct_change(1)
    df["feat_return_7d"] = close.pct_change(7)

    for w in (7, 14, 30):
        df[f"feat_vol_{w}d"] = df["feat_log_return"].rolling(w).std() * annualizer
        df[f"feat_sma_{w}"] = close.rolling(w).mean()
        df[f"feat_ema_{w}"] = close.ewm(span=w, adjust=False).mean()

    df["feat_price_to_sma30"] = close / df["feat_sma_30"].replace(0, np.nan)

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta).clip(lower=0).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.where(loss != 0, 100.0)
    rsi = rsi.where(~((loss == 0) & (gain == 0)), 50.0)
    df["feat_rsi_14"] = rsi

    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    bb_up = sma20 + 2 * std20
    bb_lo = sma20 - 2 * std20
    df["feat_bb_width"] = (bb_up - bb_lo) / sma20.replace(0, np.nan)
    df["feat_bb_position"] = (close - bb_lo) / (bb_up - bb_lo).replace(0, np.nan)

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

    return df.replace([np.inf, -np.inf], np.nan)


def build_sequences(
    features: np.ndarray,
    targets: np.ndarray,
    sequence_length: int,
    step: int = 1,
) -> Tuple[np.ndarray, np.ndarray]:
    features = np.asarray(features)
    targets = np.asarray(targets)
    if features.ndim == 1:
        features = features.reshape(-1, 1)
    if len(features) != len(targets):
        raise ValueError("features and targets must have the same length.")
    if sequence_length < 1 or step < 1:
        raise ValueError("sequence_length and step must be positive integers.")
    starts = np.arange(0, len(features) - sequence_length, step)
    if len(starts) == 0:
        return (
            np.empty((0, sequence_length, features.shape[1])),
            np.empty((0,) + targets.shape[1:]),
        )
    X = np.stack([features[i : i + sequence_length] for i in starts])
    y = targets[starts + sequence_length]
    return X, y


def build_autoencoder_sequences(
    features: np.ndarray,
    sequence_length: int,
    step: int = 1,
) -> np.ndarray:
    features = np.asarray(features)
    if features.ndim == 1:
        features = features.reshape(-1, 1)
    if sequence_length < 1 or step < 1:
        raise ValueError("sequence_length and step must be positive integers.")
    starts = np.arange(0, len(features) - sequence_length + 1, step)
    if len(starts) == 0:
        return np.empty((0, sequence_length, features.shape[1]))
    return np.stack([features[i : i + sequence_length] for i in starts])


def time_split(
    df: pd.DataFrame,
    val_frac: float = 0.10,
    test_frac: float = 0.10,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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
    chain_dfs: Dict[str, pd.DataFrame],
    freq: str = "1h",
    fill_strategy: ImputeStrategy = "ffill",
) -> pd.DataFrame:
    if not chain_dfs:
        raise ValueError("chain_dfs must contain at least one DataFrame.")
    resampled: Dict[str, pd.Series] = {}
    for name, df in chain_dfs.items():
        close = df["close"].copy()
        if not isinstance(close.index, pd.DatetimeIndex):
            close.index = pd.to_datetime(close.index)
        resampled[name] = close.resample(freq).last()
    combined = pd.DataFrame(resampled)
    combined = impute_missing(combined, strategy=fill_strategy)
    combined = combined.dropna(how="all")
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
    scaler: Optional[ScalerType] = None,
) -> Tuple[pd.DataFrame, ScalerType]:
    df = validate_ohlcv(df)
    df = impute_missing(df, strategy=impute_strategy)
    if outlier_clip:
        df = clip_outliers_iqr(
            df, cols=[c for c in ("close", "volume") if c in df.columns]
        )
    if add_features:
        df = add_technical_features(df)
    df = df.dropna()
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    if not numeric_cols or df.empty:
        raise ValueError("No usable rows remain after preprocessing.")
    if scaler is None:
        scaler = get_scaler(scaler_type)
        scaled = scaler.fit_transform(df[numeric_cols].values)
    else:
        scaled = scaler.transform(df[numeric_cols].values)
    df[numeric_cols] = scaled
    logger.info(
        "Preprocessing complete: %d rows x %d features.", len(df), len(numeric_cols)
    )
    return df, scaler

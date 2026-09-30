"""
Market Volatility Forecaster
Predicts short-term price volatility using an LSTM model with GARCH-inspired
feature engineering. Supports multiple assets and chains.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

try:
    import tensorflow as tf

    _TF_AVAILABLE = True
except ImportError:  # pragma: no cover
    tf = None  # type: ignore[assignment]
    _TF_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VolatilityForecaster:
    """
    Forecasts rolling realized volatility N steps ahead using stacked LSTMs.

    Features per timestep:
        - Log returns
        - Realized volatility (14-day rolling std of log returns * sqrt(252))
        - Absolute log returns  (proxy for vol-of-vol)
        - Squared log returns
        - High-Low range (if OHLCV supplied)
        - Parkinson volatility estimate (if OHLCV supplied)
    """

    # Number of annualised-vol output buckets: low / medium / high / extreme
    VOL_BUCKETS: Dict[str, Tuple[float, float]] = {
        "low": (0.0, 0.30),
        "medium": (0.30, 0.60),
        "high": (0.60, 1.00),
        "extreme": (1.00, float("inf")),
    }

    def __init__(
        self,
        sequence_length: int = 30,
        forecast_horizon: int = 7,
        lstm_units: Tuple[int, int] = (128, 64),
        dropout_rate: float = 0.3,
    ) -> None:
        self.sequence_length = sequence_length
        self.forecast_horizon = forecast_horizon
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model: Optional[tf.keras.Model] = None
        self.feature_names: List[str] = []
        self._is_fitted: bool = False

    # ------------------------------------------------------------------
    # Feature engineering
    # ------------------------------------------------------------------

    @staticmethod
    def _log_returns(prices: pd.Series) -> pd.Series:
        return np.log(prices / prices.shift(1))

    @staticmethod
    def _realized_vol(log_ret: pd.Series, window: int = 14) -> pd.Series:
        return log_ret.rolling(window).std() * np.sqrt(252)

    @staticmethod
    def _parkinson_vol(high: pd.Series, low: pd.Series, window: int = 14) -> pd.Series:
        """Parkinson (1980) high-low range estimator of volatility."""
        hl_ratio = np.log(high / low) ** 2
        return np.sqrt(hl_ratio.rolling(window).mean() / (4 * np.log(2))) * np.sqrt(252)

    def _build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build feature matrix from a price DataFrame.
        Required column: 'close'.
        Optional columns: 'high', 'low', 'volume'.
        """
        feat = pd.DataFrame(index=df.index)

        log_ret = self._log_returns(df["close"])
        feat["log_return"] = log_ret
        feat["abs_log_return"] = log_ret.abs()
        feat["sq_log_return"] = log_ret**2
        feat["realized_vol_14"] = self._realized_vol(log_ret, 14)
        feat["realized_vol_7"] = self._realized_vol(log_ret, 7)
        feat["realized_vol_30"] = self._realized_vol(log_ret, 30)

        if "high" in df.columns and "low" in df.columns:
            feat["hl_range"] = np.log(df["high"] / df["low"])
            feat["parkinson_vol"] = self._parkinson_vol(df["high"], df["low"])

        if "volume" in df.columns:
            feat["volume_change"] = df["volume"].pct_change()

        feat.dropna(inplace=True)
        self.feature_names = list(feat.columns)
        return feat

    def _build_target(self, df: pd.DataFrame) -> pd.Series:
        """
        Target = realized volatility over the NEXT `forecast_horizon` days.

        The rolling realized vol at time t covers the window ending at t
        (i.e. the past). Shifting it back by `forecast_horizon` aligns the
        value computed over [t+1, t+horizon] with timestamp t, so the model
        is trained to predict future volatility instead of reproducing the
        volatility it can already observe in its input features.
        """
        log_ret = self._log_returns(df["close"])
        past_vol = self._realized_vol(log_ret, self.forecast_horizon)
        # Align future-window vol with the present timestamp.
        target = past_vol.shift(-self.forecast_horizon)
        return target

    # ------------------------------------------------------------------
    # Sequence construction
    # ------------------------------------------------------------------

    def _make_sequences(
        self, features: np.ndarray, targets: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        X, y = [], []
        for i in range(self.sequence_length, len(features)):
            X.append(features[i - self.sequence_length : i])
            y.append(targets[i])
        return np.array(X), np.array(y)

    # ------------------------------------------------------------------
    # Model definition
    # ------------------------------------------------------------------

    def _build_model(self, n_features: int) -> Any:
        if not _TF_AVAILABLE:
            raise ImportError(
                "TensorFlow is required for VolatilityForecaster. "
                "Install it with: pip install tensorflow"
            )
        units_1, units_2 = self.lstm_units
        model = tf.keras.Sequential(
            [
                tf.keras.layers.LSTM(
                    units_1,
                    return_sequences=True,
                    input_shape=(self.sequence_length, n_features),
                    kernel_regularizer=tf.keras.regularizers.l2(1e-4),
                ),
                tf.keras.layers.Dropout(self.dropout_rate),
                tf.keras.layers.LSTM(
                    units_2,
                    kernel_regularizer=tf.keras.regularizers.l2(1e-4),
                ),
                tf.keras.layers.Dropout(self.dropout_rate),
                tf.keras.layers.Dense(32, activation="relu"),
                tf.keras.layers.Dense(1, activation="softplus"),  # vol ≥ 0
            ]
        )
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
            loss="huber",  # robust to outlier vol spikes
            metrics=["mae"],
        )
        logger.info("VolatilityForecaster model built (n_features=%d).", n_features)
        return model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(
        self,
        df: pd.DataFrame,
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.15,
        verbose: int = 0,
    ) -> "VolatilityForecaster":
        """Train the forecaster on historical OHLCV data."""
        if not _TF_AVAILABLE:
            raise ImportError("TensorFlow is required for VolatilityForecaster.")
        features_df = self._build_features(df)
        target_series = self._build_target(df).reindex(features_df.index).dropna()
        features_df = features_df.reindex(target_series.index)

        scaled = self.scaler.fit_transform(features_df.values)
        X, y = self._make_sequences(scaled, target_series.values)

        self.model = self._build_model(X.shape[2])
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss", patience=8, restore_best_weights=True
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=4
            ),
        ]
        self.model.fit(
            X,
            y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=verbose,
        )
        self._is_fitted = True
        logger.info("VolatilityForecaster training complete.")
        return self

    def predict(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Predict next-period volatility for the most recent `sequence_length` rows.

        Returns
        -------
        dict with:
            predicted_vol    : float  (annualised)
            vol_bucket       : str    (low / medium / high / extreme)
            confidence       : float  (placeholder - extend with MC-Dropout)
            recent_realized  : float  (last 14-day realized vol for comparison)
        """
        if not self._is_fitted or self.model is None:
            raise RuntimeError("Model must be fitted before calling predict().")

        features_df = self._build_features(df)
        if len(features_df) < self.sequence_length:
            raise ValueError(
                f"Need at least {self.sequence_length} rows after feature "
                f"engineering, got {len(features_df)}."
            )

        recent = features_df.iloc[-self.sequence_length :]
        scaled = self.scaler.transform(recent.values)
        X = scaled.reshape(1, self.sequence_length, -1)
        predicted_vol = float(self.model.predict(X, verbose=0)[0, 0])

        bucket = "extreme"
        for name, (lo, hi) in self.VOL_BUCKETS.items():
            if lo <= predicted_vol < hi:
                bucket = name
                break

        recent_realized = float(
            self._realized_vol(self._log_returns(df["close"].iloc[-30:]), 14).iloc[-1]
        )

        return {
            "predicted_vol": round(predicted_vol, 4),
            "vol_bucket": bucket,
            "confidence": 0.80,  # extend with MC-Dropout for true uncertainty
            "recent_realized_vol": round(recent_realized, 4),
            "forecast_horizon_days": self.forecast_horizon,
        }

    def classify_vol_regime(self, annualised_vol: float) -> str:
        """Map an annualised volatility value to a regime label."""
        for name, (lo, hi) in self.VOL_BUCKETS.items():
            if lo <= annualised_vol < hi:
                return name
        return "extreme"

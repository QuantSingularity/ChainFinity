import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from ...core.compat import require_tensorflow
from ...core.persistence import load_artifact, save_artifact
from ...preprocessing.ohlcv import ANNUALIZATION_FACTOR

logger = logging.getLogger(__name__)

MODEL_TYPE = "volatility_forecaster"

VOL_BUCKETS: Dict[str, Tuple[float, float]] = {
    "low": (0.0, 0.30),
    "medium": (0.30, 0.60),
    "high": (0.60, 1.00),
    "extreme": (1.00, float("inf")),
}


def classify_volatility(annualised_vol: float) -> str:
    for name, (lo, hi) in VOL_BUCKETS.items():
        if lo <= annualised_vol < hi:
            return name
    return "extreme"


def _log_returns(prices: pd.Series) -> pd.Series:
    return np.log(prices / prices.shift(1)).replace([np.inf, -np.inf], np.nan)


def ewma_volatility_forecast(
    df: pd.DataFrame,
    forecast_horizon: int = 7,
    decay: float = 0.94,
    periods_per_year: int = ANNUALIZATION_FACTOR,
    min_rows: int = 15,
) -> Dict[str, Any]:
    if "close" not in df.columns:
        raise ValueError("DataFrame must contain a 'close' column.")
    log_ret = _log_returns(pd.to_numeric(df["close"], errors="coerce")).dropna()
    if len(log_ret) < min_rows:
        raise ValueError(
            f"Need at least {min_rows} return observations, got {len(log_ret)}."
        )
    variance = (log_ret**2).ewm(alpha=1 - decay, adjust=False).mean()
    annualised = float(np.sqrt(variance.iloc[-1] * periods_per_year))
    realized = float(log_ret.iloc[-14:].std() * np.sqrt(periods_per_year))
    return {
        "predicted_vol": round(annualised, 4),
        "predicted_vol_std": None,
        "confidence_interval": None,
        "vol_bucket": classify_volatility(annualised),
        "confidence": None,
        "recent_realized_vol": round(realized, 4),
        "forecast_horizon_days": forecast_horizon,
        "model": "ewma_fallback",
    }


class VolatilityForecaster:
    VOL_BUCKETS = VOL_BUCKETS

    def __init__(
        self,
        sequence_length: int = 30,
        forecast_horizon: int = 7,
        lstm_units: Tuple[int, int] = (128, 64),
        dropout_rate: float = 0.3,
        learning_rate: float = 1e-3,
        mc_samples: int = 30,
        periods_per_year: int = ANNUALIZATION_FACTOR,
        random_state: int = 42,
    ) -> None:
        if sequence_length < 2 or forecast_horizon < 2:
            raise ValueError("sequence_length and forecast_horizon must be >= 2.")
        self.sequence_length = sequence_length
        self.forecast_horizon = forecast_horizon
        self.lstm_units = tuple(lstm_units)
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.mc_samples = mc_samples
        self.periods_per_year = periods_per_year
        self.random_state = random_state
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model: Optional[Any] = None
        self.feature_names: List[str] = []
        self._is_fitted: bool = False

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    @staticmethod
    def _log_returns(prices: pd.Series) -> pd.Series:
        return _log_returns(prices)

    def _realized_vol(self, log_ret: pd.Series, window: int = 14) -> pd.Series:
        return log_ret.rolling(window).std() * np.sqrt(self.periods_per_year)

    def _parkinson_vol(
        self, high: pd.Series, low: pd.Series, window: int = 14
    ) -> pd.Series:
        hl_ratio = np.log(high / low) ** 2
        return np.sqrt(hl_ratio.rolling(window).mean() / (4 * np.log(2))) * np.sqrt(
            self.periods_per_year
        )

    def _build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if "close" not in df.columns:
            raise ValueError("DataFrame must contain a 'close' column.")
        close = pd.to_numeric(df["close"], errors="coerce")
        feat = pd.DataFrame(index=df.index)
        log_ret = self._log_returns(close)
        feat["log_return"] = log_ret
        feat["abs_log_return"] = log_ret.abs()
        feat["sq_log_return"] = log_ret**2
        feat["realized_vol_14"] = self._realized_vol(log_ret, 14)
        feat["realized_vol_7"] = self._realized_vol(log_ret, 7)
        feat["realized_vol_30"] = self._realized_vol(log_ret, 30)
        if "high" in df.columns and "low" in df.columns:
            high = pd.to_numeric(df["high"], errors="coerce")
            low = pd.to_numeric(df["low"], errors="coerce")
            feat["hl_range"] = np.log(high / low)
            feat["parkinson_vol"] = self._parkinson_vol(high, low)
        if "volume" in df.columns:
            volume = pd.to_numeric(df["volume"], errors="coerce")
            feat["volume_change"] = volume.pct_change().clip(-10, 10)
        return feat.replace([np.inf, -np.inf], np.nan).dropna()

    def _build_target(self, df: pd.DataFrame) -> pd.Series:
        log_ret = self._log_returns(pd.to_numeric(df["close"], errors="coerce"))
        forward_vol = self._realized_vol(log_ret, self.forecast_horizon)
        return forward_vol.shift(-self.forecast_horizon)

    def _make_sequences(
        self, features: np.ndarray, targets: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        n_features = features.shape[1]
        if len(features) < self.sequence_length:
            return np.empty((0, self.sequence_length, n_features)), np.empty((0,))
        X, y = [], []
        for end in range(self.sequence_length, len(features) + 1):
            X.append(features[end - self.sequence_length : end])
            y.append(targets[end - 1])
        return np.array(X), np.array(y)

    def _build_model(self, n_features: int) -> Any:
        tf_module = require_tensorflow("VolatilityForecaster")
        layers = tf_module.keras.layers
        units_1, units_2 = self.lstm_units
        regularizer = tf_module.keras.regularizers.l2(1e-4)
        inputs = tf_module.keras.Input(shape=(self.sequence_length, n_features))
        x = layers.LSTM(units_1, return_sequences=True, kernel_regularizer=regularizer)(
            inputs
        )
        x = layers.Dropout(self.dropout_rate)(x)
        x = layers.LSTM(units_2, kernel_regularizer=regularizer)(x)
        x = layers.Dropout(self.dropout_rate)(x)
        x = layers.Dense(32, activation="relu")(x)
        outputs = layers.Dense(1, activation="softplus")(x)
        model = tf_module.keras.Model(inputs, outputs)
        model.compile(
            optimizer=tf_module.keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss="huber",
            metrics=["mae"],
        )
        logger.info("VolatilityForecaster model built (n_features=%d).", n_features)
        return model

    def fit(
        self,
        df: pd.DataFrame,
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.15,
        verbose: int = 0,
    ) -> "VolatilityForecaster":
        if not 0.0 <= validation_split < 0.5:
            raise ValueError("validation_split must be in [0, 0.5).")
        if "close" not in df.columns:
            raise ValueError("DataFrame must contain a 'close' column.")
        tf_module = require_tensorflow("VolatilityForecaster")
        tf_module.keras.utils.set_random_seed(self.random_state)

        features_df = self._build_features(df)
        target = self._build_target(df).reindex(features_df.index)
        valid = target.notna()
        features_df, target = features_df[valid], target[valid]
        minimum_rows = self.sequence_length + 20
        if len(features_df) < minimum_rows:
            raise ValueError(
                f"Need at least {minimum_rows} usable rows to train, got {len(features_df)}."
            )

        n_train_rows = int(len(features_df) * (1.0 - validation_split))
        n_train_rows = max(n_train_rows, self.sequence_length + 10)
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.scaler.fit(features_df.iloc[:n_train_rows].values)
        scaled = self.scaler.transform(features_df.values)
        X, y = self._make_sequences(scaled, target.values)

        n_train_seq = n_train_rows - self.sequence_length + 1
        X_train, y_train = X[:n_train_seq], y[:n_train_seq]
        X_val, y_val = X[n_train_seq:], y[n_train_seq:]
        has_validation = len(X_val) > 0

        self.feature_names = list(features_df.columns)
        self.model = self._build_model(X.shape[2])
        monitor = "val_loss" if has_validation else "loss"
        callbacks = [
            tf_module.keras.callbacks.EarlyStopping(
                monitor=monitor, patience=8, restore_best_weights=True
            ),
            tf_module.keras.callbacks.ReduceLROnPlateau(
                monitor=monitor, factor=0.5, patience=4
            ),
        ]
        self.model.fit(
            X_train,
            y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_val, y_val) if has_validation else None,
            callbacks=callbacks,
            shuffle=False,
            verbose=verbose,
        )
        self._is_fitted = True
        logger.info("VolatilityForecaster training complete.")
        return self

    def _latest_window(self, df: pd.DataFrame) -> np.ndarray:
        features_df = self._build_features(df)
        missing = [c for c in self.feature_names if c not in features_df.columns]
        if missing:
            raise ValueError(
                f"Input data is missing features required by the model: {missing}"
            )
        features_df = features_df[self.feature_names]
        if len(features_df) < self.sequence_length:
            raise ValueError(
                f"Need at least {self.sequence_length} rows after feature "
                f"engineering, got {len(features_df)}."
            )
        recent = features_df.iloc[-self.sequence_length :]
        scaled = self.scaler.transform(recent.values)
        return scaled.reshape(1, self.sequence_length, -1)

    def predict(self, df: pd.DataFrame) -> Dict[str, Any]:
        if not self._is_fitted or self.model is None:
            raise RuntimeError("Model must be fitted before calling predict().")
        window = self._latest_window(df)
        samples = max(int(self.mc_samples), 1)
        batch = np.repeat(window, samples, axis=0)
        draws = np.asarray(self.model(batch, training=samples > 1)).reshape(-1)
        predicted = float(np.mean(draws))
        spread = float(np.std(draws)) if samples > 1 else 0.0
        lower, upper = (
            (float(np.percentile(draws, 5)), float(np.percentile(draws, 95)))
            if samples > 1
            else (predicted, predicted)
        )
        confidence = float(np.clip(1.0 - spread / max(predicted, 1e-6), 0.0, 1.0))
        close = pd.to_numeric(df["close"], errors="coerce")
        recent_realized = float(
            self._realized_vol(self._log_returns(close.iloc[-30:]), 14).iloc[-1]
        )
        return {
            "predicted_vol": round(predicted, 4),
            "predicted_vol_std": round(spread, 4),
            "confidence_interval": [round(lower, 4), round(upper, 4)],
            "vol_bucket": classify_volatility(predicted),
            "confidence": round(confidence, 4),
            "recent_realized_vol": round(recent_realized, 4),
            "forecast_horizon_days": self.forecast_horizon,
            "model": "lstm",
        }

    def classify_vol_regime(self, annualised_vol: float) -> str:
        return classify_volatility(annualised_vol)

    def save(self, directory: Union[str, Path]) -> Path:
        if not self._is_fitted or self.model is None:
            raise RuntimeError("Model must be fitted before saving.")
        state = {
            "config": {
                "sequence_length": self.sequence_length,
                "forecast_horizon": self.forecast_horizon,
                "lstm_units": list(self.lstm_units),
                "dropout_rate": self.dropout_rate,
                "learning_rate": self.learning_rate,
                "mc_samples": self.mc_samples,
                "periods_per_year": self.periods_per_year,
                "random_state": self.random_state,
            },
            "scaler": self.scaler,
            "feature_names": self.feature_names,
        }
        return save_artifact(directory, MODEL_TYPE, state, {"network": self.model})

    @classmethod
    def load(cls, directory: Union[str, Path]) -> "VolatilityForecaster":
        state, networks = load_artifact(directory, MODEL_TYPE)
        instance = cls(**state["config"])
        instance.scaler = state["scaler"]
        instance.feature_names = list(state["feature_names"])
        instance.model = networks["network"]
        instance._is_fitted = True
        return instance


__all__ = [
    "VolatilityForecaster",
    "ewma_volatility_forecast",
    "classify_volatility",
]

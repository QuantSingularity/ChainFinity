import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf
from sklearn.preprocessing import StandardScaler

from ...core.compat import require_tensorflow
from ...core.persistence import load_artifact, save_artifact
from ...preprocessing.ohlcv import ANNUALIZATION_FACTOR

logger = logging.getLogger(__name__)

MODEL_TYPE = "correlation_predictor"
ASSET_PREFIX = "asset_"
DATE_COLUMNS = ("date", "timestamp", "datetime", "time")


def _asset_columns(df: pd.DataFrame) -> List[str]:
    return sorted(c for c in df.columns if str(c).startswith(ASSET_PREFIX))


def _nearest_correlation(matrix: np.ndarray) -> np.ndarray:
    sym = (matrix + matrix.T) / 2.0
    np.fill_diagonal(sym, 1.0)
    values, vectors = np.linalg.eigh(sym)
    values = np.clip(values, 1e-8, None)
    repaired = (vectors * values) @ vectors.T
    scale = np.sqrt(np.diag(repaired))
    repaired = repaired / np.outer(scale, scale)
    repaired = np.clip((repaired + repaired.T) / 2.0, -1.0, 1.0)
    np.fill_diagonal(repaired, 1.0)
    return repaired


def shrunk_correlation(returns: pd.DataFrame) -> pd.DataFrame:
    clean = returns.replace([np.inf, -np.inf], np.nan).dropna()
    columns = list(returns.columns)
    if len(clean) < 3 or len(columns) < 2:
        return pd.DataFrame(np.eye(len(columns)), index=columns, columns=columns)
    covariance = LedoitWolf().fit(clean.values).covariance_
    std = np.sqrt(np.diag(covariance))
    std[std == 0] = 1.0
    corr = covariance / np.outer(std, std)
    corr = _nearest_correlation(corr)
    return pd.DataFrame(corr, index=columns, columns=columns)


def load_price_frame(path: Union[str, Path]) -> pd.DataFrame:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Price data file not found: {source}")
    df = pd.read_csv(source)
    for column in df.columns:
        if str(column).lower() in DATE_COLUMNS:
            df[column] = pd.to_datetime(df[column], errors="coerce")
            df = df.dropna(subset=[column]).set_index(column).sort_index()
            break
    return df


class CorrelationPredictor:
    def __init__(
        self,
        sequence_length: int = 30,
        target_window: int = 14,
        vol_window: int = 14,
        lstm_units: Tuple[int, int] = (128, 64),
        dropout_rate: float = 0.3,
        periods_per_year: int = ANNUALIZATION_FACTOR,
        random_state: int = 42,
    ) -> None:
        if sequence_length < 2 or target_window < 3 or vol_window < 2:
            raise ValueError(
                "sequence_length >= 2, target_window >= 3 and vol_window >= 2 are required."
            )
        self.sequence_length = sequence_length
        self.target_window = target_window
        self.vol_window = vol_window
        self.lstm_units = tuple(lstm_units)
        self.dropout_rate = dropout_rate
        self.periods_per_year = periods_per_year
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.model: Optional[Any] = None
        self.asset_columns: List[str] = []
        self.n_features: Optional[int] = None
        self._is_fitted = False

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    @property
    def n_assets(self) -> Optional[int]:
        return len(self.asset_columns) or None

    @property
    def asset_names(self) -> List[str]:
        return [c[len(ASSET_PREFIX) :] for c in self.asset_columns]

    def _validated_assets(self, df: pd.DataFrame) -> List[str]:
        assets = _asset_columns(df)
        if len(assets) < 2:
            raise ValueError(
                f"DataFrame must contain at least two columns starting with '{ASSET_PREFIX}'."
            )
        return assets

    def _returns(self, df: pd.DataFrame, assets: Sequence[str]) -> pd.DataFrame:
        prices = df[list(assets)].apply(pd.to_numeric, errors="coerce")
        prices = prices.where(prices > 0)
        return np.log(prices / prices.shift(1)).replace([np.inf, -np.inf], np.nan)

    def _features(
        self, df: pd.DataFrame, assets: Sequence[str]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        returns = self._returns(df, assets)
        vols = returns.rolling(self.vol_window).std() * np.sqrt(self.periods_per_year)
        features = pd.concat(
            [returns.add_suffix("__ret"), vols.add_suffix("__vol")], axis=1
        )
        features = features.dropna()
        return features, returns.loc[features.index]

    def _build_model(self, n_features: int, output_size: int) -> Any:
        tf_module = require_tensorflow("CorrelationPredictor")
        layers = tf_module.keras.layers
        units_1, units_2 = self.lstm_units
        inputs = tf_module.keras.Input(shape=(self.sequence_length, n_features))
        x = layers.LSTM(units_1, return_sequences=True)(inputs)
        x = layers.Dropout(self.dropout_rate)(x)
        x = layers.LSTM(units_2)(x)
        x = layers.Dropout(self.dropout_rate)(x)
        x = layers.Dense(32, activation="relu")(x)
        outputs = layers.Dense(output_size, activation="tanh")(x)
        model = tf_module.keras.Model(inputs, outputs)
        model.compile(optimizer="adam", loss="mse")
        logger.info(
            "CorrelationPredictor model built (features=%d, outputs=%d).",
            n_features,
            output_size,
        )
        return model

    def create_sequences(
        self,
        df: pd.DataFrame,
        fit_scaler: bool = False,
        scaler_rows: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        assets = self._validated_assets(df)
        features, returns = self._features(df, assets)
        n_assets = len(assets)
        rows, cols = np.triu_indices(n_assets, k=1)

        if fit_scaler:
            fit_rows = scaler_rows if scaler_rows is not None else len(features)
            self.scaler = StandardScaler().fit(features.iloc[:fit_rows].values)
        scaled = self.scaler.transform(features.values)
        returns_values = returns.values

        X, y = [], []
        last_end = len(features) - self.target_window - 1
        for end in range(self.sequence_length - 1, last_end + 1):
            future = returns_values[end + 1 : end + 1 + self.target_window]
            if len(future) < self.target_window:
                continue
            with np.errstate(invalid="ignore", divide="ignore"):
                corr = np.corrcoef(future, rowvar=False)
            corr = np.nan_to_num(corr, nan=0.0)
            X.append(scaled[end - self.sequence_length + 1 : end + 1])
            y.append(corr[rows, cols])
        if not X:
            return (
                np.empty((0, self.sequence_length, features.shape[1])),
                np.empty((0, len(rows))),
            )
        return np.array(X), np.array(y)

    def fit(
        self,
        df: pd.DataFrame,
        epochs: int = 100,
        batch_size: int = 32,
        validation_split: float = 0.2,
        verbose: int = 0,
    ) -> "CorrelationPredictor":
        if not 0.0 <= validation_split < 0.5:
            raise ValueError("validation_split must be in [0, 0.5).")
        assets = self._validated_assets(df)
        tf_module = require_tensorflow("CorrelationPredictor")
        tf_module.keras.utils.set_random_seed(self.random_state)

        features, _ = self._features(df, assets)
        scaler_rows = int(len(features) * (1.0 - validation_split))
        scaler_rows = max(scaler_rows, self.sequence_length)
        X, y = self.create_sequences(df, fit_scaler=True, scaler_rows=scaler_rows)
        if len(X) < 10:
            raise ValueError(
                f"Only {len(X)} training sequences could be built; provide more history."
            )

        self.asset_columns = assets
        self.n_features = X.shape[2]
        self.model = self._build_model(self.n_features, y.shape[1])

        n_train = max(int(len(X) * (1.0 - validation_split)), 1)
        X_train, y_train = X[:n_train], y[:n_train]
        X_val, y_val = X[n_train:], y[n_train:]
        has_validation = len(X_val) > 0
        monitor = "val_loss" if has_validation else "loss"
        callbacks = [
            tf_module.keras.callbacks.EarlyStopping(
                monitor=monitor, patience=10, restore_best_weights=True
            )
        ]
        logger.info("Training correlation model: X=%s y=%s", X.shape, y.shape)
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
        return self

    def train(
        self,
        data_path: Union[str, Path],
        epochs: int = 100,
        batch_size: int = 32,
        validation_split: float = 0.2,
        output_dir: Optional[Union[str, Path]] = None,
        verbose: int = 1,
    ) -> "CorrelationPredictor":
        df = load_price_frame(data_path)
        self.fit(
            df,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=verbose,
        )
        if output_dir is not None:
            self.save(output_dir)
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        if not self._is_fitted or self.model is None:
            raise RuntimeError("Model must be fitted before calling predict().")
        assets = _asset_columns(df)
        if assets != self.asset_columns:
            raise ValueError(
                f"Input assets {assets} do not match the trained assets {self.asset_columns}."
            )
        features, _ = self._features(df, assets)
        if len(features) < self.sequence_length:
            raise ValueError(
                f"Need at least {self.sequence_length + self.vol_window} price rows "
                f"for prediction, got {len(df)}."
            )
        window = self.scaler.transform(features.iloc[-self.sequence_length :].values)
        output = np.asarray(self.model(np.expand_dims(window, axis=0), training=False))[
            0
        ]
        n_assets = len(assets)
        matrix = np.eye(n_assets)
        rows, cols = np.triu_indices(n_assets, k=1)
        matrix[rows, cols] = output
        matrix[cols, rows] = output
        return _nearest_correlation(matrix)

    def predict_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        matrix = self.predict(df)
        names = self.asset_names
        return pd.DataFrame(matrix, index=names, columns=names)

    def save(self, directory: Union[str, Path]) -> Path:
        if not self._is_fitted or self.model is None:
            raise RuntimeError("Model must be fitted before saving.")
        state: Dict[str, Any] = {
            "config": {
                "sequence_length": self.sequence_length,
                "target_window": self.target_window,
                "vol_window": self.vol_window,
                "lstm_units": list(self.lstm_units),
                "dropout_rate": self.dropout_rate,
                "periods_per_year": self.periods_per_year,
                "random_state": self.random_state,
            },
            "scaler": self.scaler,
            "asset_columns": self.asset_columns,
            "n_features": self.n_features,
        }
        return save_artifact(directory, MODEL_TYPE, state, {"network": self.model})

    @classmethod
    def load(cls, directory: Union[str, Path]) -> "CorrelationPredictor":
        state, networks = load_artifact(directory, MODEL_TYPE)
        instance = cls(**state["config"])
        instance.scaler = state["scaler"]
        instance.asset_columns = list(state["asset_columns"])
        instance.n_features = state["n_features"]
        instance.model = networks["network"]
        instance._is_fitted = True
        return instance

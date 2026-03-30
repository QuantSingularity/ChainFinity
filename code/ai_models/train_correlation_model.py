import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CorrelationPredictor:
    """
    Predicts future asset correlation using an LSTM model.
    Features include price sequences and historical volatility.
    """

    def __init__(self, sequence_length: Any = 30, n_features: Any = 10) -> None:
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = self._build_model()

    def _build_model(self) -> Any:
        """Builds the LSTM model for correlation prediction."""
        model = tf.keras.Sequential(
            [
                tf.keras.layers.LSTM(
                    128,
                    return_sequences=True,
                    input_shape=(self.sequence_length, self.n_features),
                ),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.LSTM(64),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.Dense(32, activation="relu"),
                tf.keras.layers.Dense(
                    self.n_features * self.n_features, activation="tanh"
                ),
            ]
        )
        model.compile(optimizer="adam", loss="mse")
        logger.info("LSTM Model built successfully.")
        return model

    def _calculate_volatility(self, prices: pd.Series, window: Any = 14) -> pd.Series:
        """Calculates historical volatility (standard deviation of log returns)."""
        log_returns = np.log(prices / prices.shift(1))
        return log_returns.rolling(window=window).std() * np.sqrt(252)

    def create_sequences(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Creates time sequences for LSTM training.
        Input (X): sequence_length days of price and volatility data.
        Target (y): Flattened correlation matrix for the day immediately following the sequence.
        """
        data = df.copy()
        asset_cols = [col for col in data.columns if col.startswith("asset_")]
        if not asset_cols:
            raise ValueError(
                "DataFrame must contain columns starting with 'asset_' for price data."
            )
        for col in asset_cols:
            data[f"{col}_volatility"] = self._calculate_volatility(data[col])
        data.dropna(inplace=True)
        features = data[[col for col in data.columns if col not in asset_cols]]
        self.n_features = features.shape[1]
        scaled_features = self.scaler.fit_transform(features)
        X, y = ([], [])
        for i in range(self.sequence_length, len(data)):
            X.append(scaled_features[i - self.sequence_length : i])
            window_prices = data[asset_cols].iloc[i - self.sequence_length : i]
            window_returns = window_prices.pct_change().dropna()
            if window_returns.empty:
                continue
            corr_matrix = window_returns.corr().values
            y.append(corr_matrix.flatten())
        return (np.array(X), np.array(y))

    def train(
        self,
        data_path: str,
        epochs: Any = 100,
        batch_size: Any = 32,
        validation_split: Any = 0.2,
    ) -> Any:
        """Trains the LSTM model."""
        try:
            df = pd.read_csv(data_path)
        except FileNotFoundError:
            logger.error(f"Data file not found at {data_path}")
            logger.warning("Using dummy data for training demonstration.")
            dates = pd.date_range(start="2020-01-01", periods=200, freq="D")
            np.random.seed(42)
            df = pd.DataFrame(
                {
                    "Date": dates,
                    "asset_btc": np.cumsum(np.random.randn(200) * 0.01 + 100),
                    "asset_eth": np.cumsum(np.random.randn(200) * 0.01 + 50),
                    "asset_sol": np.cumsum(np.random.randn(200) * 0.01 + 20),
                }
            ).set_index("Date")
        if len(df) < self.sequence_length + 1:
            logger.error(
                f"Data has only {len(df)} rows, but requires at least {self.sequence_length + 1} for sequence creation."
            )
            return
        try:
            X, y = self.create_sequences(df)
        except ValueError as e:
            logger.error(f"Error creating sequences: {e}")
            return
        if X.shape[0] == 0:
            logger.error("No sequences were created. Check data and sequence length.")
            return
        output_size = y.shape[1]
        if self.model.output_shape[1] != output_size:
            logger.warning(
                f"Rebuilding model to match target output size: {output_size}"
            )
            self.model = self._build_model()
        logger.info(f"Training model with X shape: {X.shape}, y shape: {y.shape}")
        self.model.fit(
            X,
            y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=1,
        )
        self.model.save("correlation_model.h5")
        logger.info("Model trained and saved as correlation_model.h5")

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Predicts the correlation matrix for the next period.
        Input DataFrame should contain the latest 'sequence_length' days of data.
        """
        data = df.copy()
        asset_cols = [col for col in data.columns if col.startswith("asset_")]
        if not asset_cols:
            raise ValueError(
                "DataFrame must contain columns starting with 'asset_' for price data."
            )
        for col in asset_cols:
            data[f"{col}_volatility"] = self._calculate_volatility(data[col])
        data.dropna(inplace=True)
        if len(data) < self.sequence_length:
            raise ValueError(
                f"Input data must contain at least {self.sequence_length} rows for prediction."
            )
        features = data[[col for col in data.columns if col not in asset_cols]].tail(
            self.sequence_length
        )
        scaled_features = self.scaler.transform(features)
        X_pred = np.expand_dims(scaled_features, axis=0)
        flattened_corr = self.model.predict(X_pred)[0]
        n_assets = len(asset_cols)
        corr_matrix = flattened_corr.reshape(n_assets, n_assets)
        corr_matrix = (corr_matrix + corr_matrix.T) / 2
        np.fill_diagonal(corr_matrix, 1.0)
        return corr_matrix


if __name__ == "__main__":
    predictor = CorrelationPredictor()
    predictor.train("data.csv", epochs=10)
    dates = pd.date_range(start="2023-01-01", periods=30, freq="D")
    np.random.seed(10)
    df_pred = pd.DataFrame(
        {
            "Date": dates,
            "asset_btc": np.cumsum(np.random.randn(30) * 0.01 + 100),
            "asset_eth": np.cumsum(np.random.randn(30) * 0.01 + 50),
            "asset_sol": np.cumsum(np.random.randn(30) * 0.01 + 20),
        }
    ).set_index("Date")
    try:
        predicted_corr = predictor.predict(df_pred)
        logger.info("\nPredicted Correlation Matrix:")
        logger.info(predicted_corr)
    except Exception as e:
        logger.error(f"Prediction failed: {e}")

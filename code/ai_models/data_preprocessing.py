import numpy as np
import pandas as pd
from typing import Any


class DataProcessor:

    def clean_market_data(self, raw_data: Any) -> Any:
        df = pd.DataFrame(raw_data)
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(method="ffill").dropna()
        df = df[(df["volume"] > 0) & (df["close"] > 0)]
        return df

    def calculate_returns(self, df: Any) -> Any:
        df["log_return"] = np.log(df["close"] / df["close"].shift(1))
        df["volatility_30d"] = df["log_return"].rolling(30).std() * np.sqrt(365)
        return df.dropna()

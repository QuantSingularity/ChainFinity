import numpy as np
import pandas as pd
import pytest

from .factories import make_ohlcv


class TestDataPreprocessing:
    def test_validate_ohlcv_basic(self):
        from ai_models.preprocessing import validate_ohlcv

        df = make_ohlcv(50)
        clean = validate_ohlcv(df)
        assert "close" in clean.columns
        assert len(clean) == 50

    def test_validate_ohlcv_missing_close_raises(self):
        from ai_models.preprocessing import validate_ohlcv

        df = pd.DataFrame(
            {"open": [1, 2], "high": [1, 2], "low": [1, 2], "volume": [1, 2]}
        )
        with pytest.raises(ValueError, match="close"):
            validate_ohlcv(df)

    def test_validate_ohlcv_strict_missing_raises(self):
        from ai_models.preprocessing import validate_ohlcv

        df = pd.DataFrame({"close": [1.0, 2.0]})
        with pytest.raises(ValueError, match="Missing required"):
            validate_ohlcv(df, strict=True)

    def test_impute_ffill(self):
        from ai_models.preprocessing import impute_missing

        s = pd.DataFrame({"close": [1.0, np.nan, np.nan, 4.0]})
        result = impute_missing(s, strategy="ffill")
        assert result["close"].isna().sum() == 0

    def test_impute_linear(self):
        from ai_models.preprocessing import impute_missing

        s = pd.DataFrame({"close": [0.0, np.nan, 2.0, np.nan, 4.0, 5.0]})
        result = impute_missing(s, strategy="linear")
        assert result["close"].isna().sum() == 0
        assert abs(result["close"].iloc[1] - 1.0) < 1e-6

    def test_impute_median(self):
        from ai_models.preprocessing import impute_missing

        s = pd.DataFrame({"a": [1.0, np.nan, 3.0, 5.0]})
        result = impute_missing(s, strategy="median")
        assert result["a"].isna().sum() == 0

    def test_impute_constant(self):
        from ai_models.preprocessing import impute_missing

        s = pd.DataFrame({"a": [1.0, np.nan, 3.0]})
        result = impute_missing(s, strategy=0.0)
        assert result["a"].iloc[1] == 0.0

    def test_impute_unknown_raises(self):
        from ai_models.preprocessing import impute_missing

        with pytest.raises(ValueError):
            impute_missing(pd.DataFrame({"a": [1.0]}), strategy="unknown")

    def test_clip_outliers_iqr(self):
        from ai_models.preprocessing import clip_outliers_iqr

        df = make_ohlcv(100)
        df.loc[df.index[0], "close"] = 1e9
        clipped = clip_outliers_iqr(df, cols=["close"])
        assert clipped["close"].max() < 1e9

    def test_get_scaler_minmax(self):
        from ai_models.preprocessing import get_scaler

        s = get_scaler("minmax")
        assert hasattr(s, "fit_transform")

    def test_get_scaler_standard(self):
        from ai_models.preprocessing import get_scaler

        s = get_scaler("standard")
        assert hasattr(s, "fit_transform")

    def test_get_scaler_robust(self):
        from ai_models.preprocessing import get_scaler

        s = get_scaler("robust")
        assert hasattr(s, "fit_transform")

    def test_get_scaler_unknown_raises(self):
        from ai_models.preprocessing import get_scaler

        with pytest.raises(ValueError):
            get_scaler("nonexistent")

    def test_add_technical_features(self):
        from ai_models.preprocessing import add_technical_features

        df = make_ohlcv(100)
        result = add_technical_features(df)
        assert "feat_log_return" in result.columns
        assert "feat_rsi_14" in result.columns
        assert "feat_bb_width" in result.columns
        assert "feat_hl_range" in result.columns
        assert "feat_volume_ratio" in result.columns

    def test_build_sequences_shape(self):
        from ai_models.preprocessing import build_sequences

        features = np.random.rand(100, 5)
        targets = np.random.rand(100)
        X, y = build_sequences(features, targets, sequence_length=20)
        assert X.shape[1] == 20
        assert X.shape[2] == 5
        assert len(X) == len(y)

    def test_build_autoencoder_sequences_shape(self):
        from ai_models.preprocessing import build_autoencoder_sequences

        features = np.random.rand(80, 4)
        seqs = build_autoencoder_sequences(features, sequence_length=10)
        assert seqs.shape[1] == 10
        assert seqs.shape[2] == 4

    def test_time_split_proportions(self):
        from ai_models.preprocessing import time_split

        df = pd.DataFrame({"v": np.arange(100)})
        train, val, test = time_split(df, val_frac=0.1, test_frac=0.1)
        assert len(train) + len(val) + len(test) == 100
        assert len(test) >= 1
        assert len(val) >= 1

    def test_time_split_too_small_raises(self):
        from ai_models.preprocessing import time_split

        df = pd.DataFrame({"v": [1, 2]})
        with pytest.raises(ValueError):
            time_split(df, val_frac=0.5, test_frac=0.5)

    def test_align_multi_chain(self):
        from ai_models.preprocessing import align_multi_chain

        dfs = {
            "eth": make_ohlcv(60),
            "matic": make_ohlcv(60),
        }
        combined = align_multi_chain(dfs, freq="1D")
        assert "eth" in combined.columns
        assert "matic" in combined.columns

    def test_preprocess_ohlcv_pipeline(self):
        from ai_models.preprocessing import preprocess_ohlcv

        df = make_ohlcv(100)
        processed, scaler = preprocess_ohlcv(
            df, scaler_type="minmax", add_features=True
        )
        assert len(processed) > 0
        numeric = processed.select_dtypes(include=np.number)
        assert numeric.min().min() >= -1e-6
        assert numeric.max().max() <= 1 + 1e-6

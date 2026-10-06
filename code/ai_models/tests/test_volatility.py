import pytest

from .factories import make_ohlcv


class TestVolatilityForecaster:
    def test_log_returns(self):
        from ai_models.models.volatility import VolatilityForecaster

        df = make_ohlcv(60)
        vf = VolatilityForecaster()
        log_ret = vf._log_returns(df["close"])
        assert len(log_ret) == 60
        assert log_ret.isna().sum() == 1

    def test_realized_vol(self):
        from ai_models.models.volatility import VolatilityForecaster

        df = make_ohlcv(60)
        vf = VolatilityForecaster()
        lr = vf._log_returns(df["close"])
        rv = vf._realized_vol(lr, window=14)
        assert rv.dropna().gt(0).all()

    def test_parkinson_vol(self):
        from ai_models.models.volatility import VolatilityForecaster

        df = make_ohlcv(60)
        vf = VolatilityForecaster()
        pv = vf._parkinson_vol(df["high"], df["low"], window=7)
        assert pv.dropna().gt(0).all()

    def test_classify_vol_regime(self):
        from ai_models.models.volatility import VolatilityForecaster

        vf = VolatilityForecaster()
        assert vf.classify_vol_regime(0.10) == "low"
        assert vf.classify_vol_regime(0.45) == "medium"
        assert vf.classify_vol_regime(0.80) == "high"
        assert vf.classify_vol_regime(1.50) == "extreme"

    def test_predict_raises_before_fit(self):
        from ai_models.models.volatility import VolatilityForecaster

        vf = VolatilityForecaster(sequence_length=10)
        with pytest.raises(RuntimeError, match="fitted"):
            vf.predict(make_ohlcv(50))

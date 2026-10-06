import numpy as np
import pandas as pd
import pytest


class TestLiquidityCrisisModel:
    def _tvl(self, n: int = 200) -> pd.Series:
        rng = np.random.default_rng(11)
        values = 1e8 * np.cumprod(1 + rng.normal(0, 0.01, n))
        return pd.Series(
            values, index=pd.date_range("2023-01-01", periods=n, freq="1h")
        )

    def test_tvl_velocity_monitor(self):
        from ai_models.models.liquidity import TVLVelocityMonitor

        tvl = self._tvl(100)
        monitor = TVLVelocityMonitor(window=24)
        scores = monitor.score(tvl)
        assert scores.between(0, 1).all()

    def test_spread_model(self):
        from ai_models.models.liquidity import SpreadModel

        rng = np.random.default_rng(7)
        spread = pd.Series(
            rng.uniform(0.001, 0.01, 100),
            index=pd.date_range("2023-01-01", periods=100, freq="1h"),
        )
        model = SpreadModel()
        scores = model.score(spread)
        assert scores.between(0, 1).all()

    def test_depeg_detector_normal(self):
        from ai_models.models.liquidity import DepegDetector

        rng = np.random.default_rng(3)
        price = pd.Series(
            1.0 + rng.normal(0, 0.001, 100),
            index=pd.date_range("2023-01-01", periods=100, freq="1h"),
        )
        det = DepegDetector(peg_value=1.0)
        scores = det.score(price)
        assert scores.between(0, 1).all()
        assert scores.mean() < 0.3

    def test_depeg_detector_crisis(self):
        from ai_models.models.liquidity import DepegDetector

        price = pd.Series(
            [1.0] * 50 + [0.85] * 50,
            index=pd.date_range("2023-01-01", periods=100, freq="1h"),
        )
        det = DepegDetector(peg_value=1.0, warning_band=0.005)
        scores = det.score(price)
        assert scores.iloc[50:].mean() > scores.iloc[:30].mean()

    def test_contagion_scorer(self):
        from ai_models.models.liquidity import ContagionScorer

        rng = np.random.default_rng(22)
        ret_df = pd.DataFrame(
            rng.normal(0, 0.02, (100, 4)),
            columns=["proto_a", "proto_b", "proto_c", "proto_d"],
            index=pd.date_range("2023-01-01", periods=100, freq="1h"),
        )
        scorer = ContagionScorer(window=12)
        scores = scorer.score(ret_df)
        assert scores.between(0, 1).all()

    def test_contagion_scorer_single_column(self):
        from ai_models.models.liquidity import ContagionScorer

        rng = np.random.default_rng(1)
        ret_df = pd.DataFrame(
            {"only": rng.normal(0, 0.01, 50)},
            index=pd.date_range("2023-01-01", periods=50, freq="1h"),
        )
        scorer = ContagionScorer()
        scores = scorer.score(ret_df)
        assert (scores == 0.0).all()

    def test_liquidity_crisis_detector_analyze(self):
        from ai_models.models.liquidity import LiquidityCrisisDetector

        tvl = self._tvl(100)
        det = LiquidityCrisisDetector()
        result = det.analyze(tvl, protocol_id="test_proto")
        assert "overall_risk" in result.columns
        assert "alert_level" in result.columns
        assert result["overall_risk"].between(0, 1).all()

    def test_liquidity_crisis_detector_bad_weights(self):
        from ai_models.models.liquidity import LiquidityCrisisDetector

        with pytest.raises(ValueError, match="sum to 1"):
            LiquidityCrisisDetector(
                weights={
                    "tvl_velocity": 0.5,
                    "spread": 0.5,
                    "depeg": 0.5,
                    "contagion": 0.5,
                }
            )

    def test_get_alerts(self):
        from ai_models.models.liquidity import LiquidityCrisisDetector

        tvl = self._tvl(80)
        det = LiquidityCrisisDetector()
        alerts = det.get_alerts(tvl, protocol_id="proto_x", min_level="normal")
        assert isinstance(alerts, list)

    def test_latest_status(self):
        from ai_models.models.liquidity import LiquidityCrisisDetector

        tvl = self._tvl(50)
        det = LiquidityCrisisDetector()
        status = det.latest_status(tvl, protocol_id="proto_y")
        assert "overall_risk" in status
        assert "alert_level" in status
        assert 0 <= status["overall_risk"] <= 1

    def test_alert_to_dict(self):
        from ai_models.models.liquidity import LiquidityAlert

        alert = LiquidityAlert(
            timestamp="2024-01-01T00:00:00",
            protocol_id="aave",
            overall_risk=0.72,
            tvl_velocity_score=0.8,
            spread_score=0.6,
            depeg_score=0.1,
            contagion_score=0.5,
            alert_level="warning",
            recommended_actions=["reduce exposure"],
        )
        d = alert.to_dict()
        assert d["alert_level"] == "warning"
        assert "component_scores" in d

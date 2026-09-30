"""
Tests for ChainFinity AI models and data preprocessing pipeline.
All tests run without a GPU and without requiring real market data.
"""

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Helpers to generate synthetic data
# ---------------------------------------------------------------------------


def _make_ohlcv(n: int = 200, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100 * np.cumprod(1 + rng.normal(0, 0.02, n))
    high = close * (1 + rng.uniform(0, 0.02, n))
    low = close * (1 - rng.uniform(0, 0.02, n))
    return pd.DataFrame(
        {
            "open": close * (1 + rng.normal(0, 0.005, n)),
            "high": high,
            "low": low,
            "close": close,
            "volume": rng.uniform(1e6, 1e7, n),
        },
        index=pd.date_range("2023-01-01", periods=n, freq="1D"),
    )


def _make_wallet_df(n: int = 100, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    addrs = [f"0x{i:040x}" for i in range(n)]
    return pd.DataFrame(
        {
            "total_volume_usd_30d": rng.uniform(1e4, 1e8, n),
            "tx_count_30d": rng.integers(1, 500, n),
            "unique_protocols_30d": rng.integers(1, 20, n),
            "unique_chains": rng.integers(1, 8, n),
            "avg_hold_days": rng.uniform(0.5, 180, n),
            "pnl_30d_pct": rng.uniform(-0.5, 2.0, n),
            "pnl_90d_pct": rng.uniform(-0.8, 5.0, n),
            "win_rate": rng.uniform(0.2, 0.9, n),
            "max_single_trade_usd": rng.uniform(1e3, 5e6, n),
            "avg_trade_size_usd": rng.uniform(100, 5e5, n),
            "early_entry_ratio": rng.uniform(0, 1, n),
            "exit_timing_score": rng.uniform(0, 1, n),
            "bridge_frequency": rng.uniform(0, 1, n),
            "flash_loan_usage": rng.uniform(0, 0.3, n),
        },
        index=addrs,
    )


def _make_onchain_df(n: int = 150, seed: int = 99) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "flash_loan_volume_usd": rng.uniform(0, 5e5, n),
            "large_tx_count": rng.integers(0, 20, n),
            "unique_callers": rng.integers(5, 500, n),
            "reentrancy_depth_max": rng.integers(1, 10, n),
            "token_mint_rate": rng.uniform(0, 1, n),
            "price_impact_pct": rng.uniform(0, 0.1, n),
            "tvl_change_pct": rng.normal(0, 0.02, n),
            "gas_price_percentile": rng.uniform(0, 1, n),
            "failed_tx_ratio": rng.uniform(0, 0.3, n),
            "contract_interaction_entropy": rng.uniform(0.5, 1, n),
        },
        index=pd.date_range("2023-01-01", periods=n, freq="1h"),
    )


# ===========================================================================
# data_preprocessing tests
# ===========================================================================


class TestDataPreprocessing:
    def test_validate_ohlcv_basic(self):
        from data_preprocessing import validate_ohlcv

        df = _make_ohlcv(50)
        clean = validate_ohlcv(df)
        assert "close" in clean.columns
        assert len(clean) == 50

    def test_validate_ohlcv_missing_close_raises(self):
        from data_preprocessing import validate_ohlcv

        df = pd.DataFrame(
            {"open": [1, 2], "high": [1, 2], "low": [1, 2], "volume": [1, 2]}
        )
        with pytest.raises(ValueError, match="close"):
            validate_ohlcv(df)

    def test_validate_ohlcv_strict_missing_raises(self):
        from data_preprocessing import validate_ohlcv

        df = pd.DataFrame({"close": [1.0, 2.0]})
        with pytest.raises(ValueError, match="Missing required"):
            validate_ohlcv(df, strict=True)

    def test_impute_ffill(self):
        from data_preprocessing import impute_missing

        s = pd.DataFrame({"close": [1.0, np.nan, np.nan, 4.0]})
        result = impute_missing(s, strategy="ffill")
        assert result["close"].isna().sum() == 0

    def test_impute_linear(self):
        from data_preprocessing import impute_missing

        s = pd.DataFrame({"close": [0.0, np.nan, 2.0, np.nan, 4.0, 5.0]})
        result = impute_missing(s, strategy="linear")
        assert result["close"].isna().sum() == 0
        # Linear interpolation: between 0 and 2 → 1.0
        assert abs(result["close"].iloc[1] - 1.0) < 1e-6

    def test_impute_median(self):
        from data_preprocessing import impute_missing

        s = pd.DataFrame({"a": [1.0, np.nan, 3.0, 5.0]})
        result = impute_missing(s, strategy="median")
        assert result["a"].isna().sum() == 0

    def test_impute_constant(self):
        from data_preprocessing import impute_missing

        s = pd.DataFrame({"a": [1.0, np.nan, 3.0]})
        result = impute_missing(s, strategy=0.0)
        assert result["a"].iloc[1] == 0.0

    def test_impute_unknown_raises(self):
        from data_preprocessing import impute_missing

        with pytest.raises(ValueError):
            impute_missing(pd.DataFrame({"a": [1.0]}), strategy="unknown")

    def test_clip_outliers_iqr(self):
        from data_preprocessing import clip_outliers_iqr

        df = _make_ohlcv(100)
        df.loc[df.index[0], "close"] = 1e9  # inject extreme outlier
        clipped = clip_outliers_iqr(df, cols=["close"])
        assert clipped["close"].max() < 1e9

    def test_get_scaler_minmax(self):
        from data_preprocessing import get_scaler

        s = get_scaler("minmax")
        assert hasattr(s, "fit_transform")

    def test_get_scaler_standard(self):
        from data_preprocessing import get_scaler

        s = get_scaler("standard")
        assert hasattr(s, "fit_transform")

    def test_get_scaler_robust(self):
        from data_preprocessing import get_scaler

        s = get_scaler("robust")
        assert hasattr(s, "fit_transform")

    def test_get_scaler_unknown_raises(self):
        from data_preprocessing import get_scaler

        with pytest.raises(ValueError):
            get_scaler("nonexistent")

    def test_add_technical_features(self):
        from data_preprocessing import add_technical_features

        df = _make_ohlcv(100)
        result = add_technical_features(df)
        assert "feat_log_return" in result.columns
        assert "feat_rsi_14" in result.columns
        assert "feat_bb_width" in result.columns
        assert "feat_hl_range" in result.columns
        assert "feat_volume_ratio" in result.columns

    def test_build_sequences_shape(self):
        from data_preprocessing import build_sequences

        features = np.random.rand(100, 5)
        targets = np.random.rand(100)
        X, y = build_sequences(features, targets, sequence_length=20)
        assert X.shape[1] == 20
        assert X.shape[2] == 5
        assert len(X) == len(y)

    def test_build_autoencoder_sequences_shape(self):
        from data_preprocessing import build_autoencoder_sequences

        features = np.random.rand(80, 4)
        seqs = build_autoencoder_sequences(features, sequence_length=10)
        assert seqs.shape[1] == 10
        assert seqs.shape[2] == 4

    def test_time_split_proportions(self):
        from data_preprocessing import time_split

        df = pd.DataFrame({"v": np.arange(100)})
        train, val, test = time_split(df, val_frac=0.1, test_frac=0.1)
        assert len(train) + len(val) + len(test) == 100
        assert len(test) >= 1
        assert len(val) >= 1

    def test_time_split_too_small_raises(self):
        from data_preprocessing import time_split

        df = pd.DataFrame({"v": [1, 2]})
        with pytest.raises(ValueError):
            time_split(df, val_frac=0.5, test_frac=0.5)

    def test_align_multi_chain(self):
        from data_preprocessing import align_multi_chain

        dfs = {
            "eth": _make_ohlcv(60),
            "matic": _make_ohlcv(60),
        }
        combined = align_multi_chain(dfs, freq="1D")
        assert "eth" in combined.columns
        assert "matic" in combined.columns

    def test_preprocess_ohlcv_pipeline(self):
        from data_preprocessing import preprocess_ohlcv

        df = _make_ohlcv(100)
        processed, scaler = preprocess_ohlcv(
            df, scaler_type="minmax", add_features=True
        )
        assert len(processed) > 0
        # After minmax scaling, values should be in [0, 1]
        numeric = processed.select_dtypes(include=np.number)
        assert numeric.min().min() >= -1e-6
        assert numeric.max().max() <= 1 + 1e-6


# ===========================================================================
# exploit_detection_model tests
# ===========================================================================


class TestExploitDetectionModel:
    def test_engineer_features_shape(self):
        from exploit_detection_model import engineer_exploit_features

        df = _make_onchain_df(50)
        feat = engineer_exploit_features(df)
        assert len(feat) == 50
        assert feat.isna().sum().sum() == 0

    def test_exploit_detector_fit_predict(self):
        from exploit_detection_model import ExploitDetector

        df = _make_onchain_df(100)
        det = ExploitDetector(sequence_length=10)
        det.fit(df, epochs=2)  # minimal epochs for test speed
        scored = det.score(df)
        assert "risk_score" in scored.columns
        assert scored["risk_score"].between(0, 1).all()

    def test_exploit_detector_severity_labels(self):
        from exploit_detection_model import ExploitDetector

        df = _make_onchain_df(80)
        det = ExploitDetector(sequence_length=5)
        det.fit(df, epochs=1)
        scored = det.score(df)
        valid = {"low", "medium", "high", "critical"}
        assert set(scored["severity"].unique()).issubset(valid)

    def test_exploit_detector_alerts(self):
        from exploit_detection_model import ExploitDetector

        df = _make_onchain_df(80)
        det = ExploitDetector(sequence_length=5)
        det.fit(df, epochs=1)
        alerts = det.get_alerts(df, protocol_id="test_proto", threshold=0.0)
        # With threshold=0 all rows trigger; alerts should be a list
        assert isinstance(alerts, list)
        if alerts:
            assert hasattr(alerts[0], "risk_score")
            assert hasattr(alerts[0], "severity")

    def test_exploit_alert_to_dict(self):
        from exploit_detection_model import ExploitAlert

        alert = ExploitAlert(
            timestamp="2024-01-01",
            protocol_id="test",
            risk_score=0.75,
            isolation_score=0.6,
            autoencoder_score=0.85,
            triggered_features=["tvl_change_pct"],
            severity="high",
        )
        d = alert.to_dict()
        assert d["severity"] == "high"
        assert 0 <= d["risk_score"] <= 1

    def test_score_raises_before_fit(self):
        from exploit_detection_model import ExploitDetector

        det = ExploitDetector()
        with pytest.raises(RuntimeError, match="Fit"):
            det.score(_make_onchain_df(20))


# ===========================================================================
# smart_money_tracker tests
# ===========================================================================


class TestSmartMoneyTracker:
    def test_engineer_wallet_features(self):
        from smart_money_tracker import engineer_wallet_features

        wdf = _make_wallet_df(50)
        feat = engineer_wallet_features(wdf)
        assert len(feat) == 50
        assert feat.isna().sum().sum() == 0

    def test_fit_and_profile(self):
        from smart_money_tracker import SmartMoneyTracker

        wdf = _make_wallet_df(80)
        tracker = SmartMoneyTracker(n_clusters=3)
        tracker.fit(wdf)
        profiles = tracker.profile_wallets(wdf)
        assert len(profiles) == 80
        assert all(0 <= p.smart_money_score <= 100 for p in profiles)

    def test_get_smart_money_wallets(self):
        from smart_money_tracker import SmartMoneyTracker

        wdf = _make_wallet_df(60)
        tracker = SmartMoneyTracker(n_clusters=3)
        tracker.fit(wdf)
        top = tracker.get_smart_money_wallets(wdf, top_n=10)
        assert len(top) == 10
        scores = [p.smart_money_score for p in top]
        assert scores == sorted(scores, reverse=True)

    def test_generate_signals(self):
        from smart_money_tracker import SmartMoneyTracker

        rng = np.random.default_rng(5)
        wdf = _make_wallet_df(40)
        tracker = SmartMoneyTracker(n_clusters=3)
        tracker.fit(wdf)
        profiles = tracker.profile_wallets(wdf)

        # Build a small tx dataframe using known wallet addresses
        addrs = wdf.index.tolist()[:10]
        tx_df = pd.DataFrame(
            {
                "wallet_address": rng.choice(addrs, 30),
                "chain": rng.choice(["ethereum", "polygon"], 30),
                "protocol": rng.choice(["uniswap", "aave"], 30),
                "direction": rng.choice(["buy", "sell"], 30),
                "amount_usd": rng.uniform(5000, 500000, 30),
                "token_symbol": rng.choice(["ETH", "USDC"], 30),
                "timestamp": pd.date_range("2024-01-01", periods=30, freq="1h"),
            }
        )
        signals = tracker.generate_signals(tx_df, profiles, min_amount_usd=1000)
        assert isinstance(signals, list)

    def test_cross_chain_flow_summary(self):
        from smart_money_tracker import SmartMoneyTracker

        wdf = _make_wallet_df(40)
        tracker = SmartMoneyTracker(n_clusters=3)
        tracker.fit(wdf)
        profiles = tracker.profile_wallets(wdf)

        rng = np.random.default_rng(3)
        addrs = wdf.index.tolist()[:5]
        tx_df = pd.DataFrame(
            {
                "wallet_address": rng.choice(addrs, 20),
                "chain": rng.choice(["ethereum", "polygon"], 20),
                "token_symbol": rng.choice(["ETH", "USDC"], 20),
                "direction": rng.choice(["buy", "sell"], 20),
                "amount_usd": rng.uniform(1000, 100000, 20),
                "timestamp": pd.date_range("2024-01-01", periods=20, freq="1h"),
            }
        )
        summary = tracker.cross_chain_flow_summary(tx_df, profiles)
        assert isinstance(summary, pd.DataFrame)

    def test_wallet_profile_raises_before_fit(self):
        from smart_money_tracker import SmartMoneyTracker

        tracker = SmartMoneyTracker()
        with pytest.raises(RuntimeError, match="fit"):
            tracker.profile_wallets(_make_wallet_df(10))

    def test_wallet_profile_to_dict(self):
        from smart_money_tracker import WalletProfile

        p = WalletProfile(
            address="0xabc",
            cluster_id=1,
            cluster_label="smart_trader",
            smart_money_score=72.5,
            pnl_30d=0.15,
            pnl_90d=0.45,
            win_rate=0.65,
            avg_trade_size_usd=25000,
        )
        d = p.to_dict()
        assert d["cluster"] == "smart_trader"
        assert 0 <= d["smart_money_score"] <= 100


# ===========================================================================
# liquidity_crisis_model tests
# ===========================================================================


class TestLiquidityCrisisModel:
    def _tvl(self, n: int = 200) -> pd.Series:
        rng = np.random.default_rng(11)
        values = 1e8 * np.cumprod(1 + rng.normal(0, 0.01, n))
        return pd.Series(
            values, index=pd.date_range("2023-01-01", periods=n, freq="1h")
        )

    def test_tvl_velocity_monitor(self):
        from liquidity_crisis_model import TVLVelocityMonitor

        tvl = self._tvl(100)
        monitor = TVLVelocityMonitor(window=24)
        scores = monitor.score(tvl)
        assert scores.between(0, 1).all()

    def test_spread_model(self):
        from liquidity_crisis_model import SpreadModel

        rng = np.random.default_rng(7)
        spread = pd.Series(
            rng.uniform(0.001, 0.01, 100),
            index=pd.date_range("2023-01-01", periods=100, freq="1h"),
        )
        model = SpreadModel()
        scores = model.score(spread)
        assert scores.between(0, 1).all()

    def test_depeg_detector_normal(self):
        from liquidity_crisis_model import DepegDetector

        rng = np.random.default_rng(3)
        price = pd.Series(
            1.0 + rng.normal(0, 0.001, 100),
            index=pd.date_range("2023-01-01", periods=100, freq="1h"),
        )
        det = DepegDetector(peg_value=1.0)
        scores = det.score(price)
        assert scores.between(0, 1).all()
        # Near-peg prices should yield low scores
        assert scores.mean() < 0.3

    def test_depeg_detector_crisis(self):
        from liquidity_crisis_model import DepegDetector

        price = pd.Series(
            [1.0] * 50 + [0.85] * 50,
            index=pd.date_range("2023-01-01", periods=100, freq="1h"),
        )
        det = DepegDetector(peg_value=1.0, warning_band=0.005)
        scores = det.score(price)
        # Second half should show elevated scores
        assert scores.iloc[50:].mean() > scores.iloc[:30].mean()

    def test_contagion_scorer(self):
        from liquidity_crisis_model import ContagionScorer

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
        from liquidity_crisis_model import ContagionScorer

        rng = np.random.default_rng(1)
        ret_df = pd.DataFrame(
            {"only": rng.normal(0, 0.01, 50)},
            index=pd.date_range("2023-01-01", periods=50, freq="1h"),
        )
        scorer = ContagionScorer()
        scores = scorer.score(ret_df)
        assert (scores == 0.0).all()

    def test_liquidity_crisis_detector_analyze(self):
        from liquidity_crisis_model import LiquidityCrisisDetector

        tvl = self._tvl(100)
        det = LiquidityCrisisDetector()
        result = det.analyze(tvl, protocol_id="test_proto")
        assert "overall_risk" in result.columns
        assert "alert_level" in result.columns
        assert result["overall_risk"].between(0, 1).all()

    def test_liquidity_crisis_detector_bad_weights(self):
        from liquidity_crisis_model import LiquidityCrisisDetector

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
        from liquidity_crisis_model import LiquidityCrisisDetector

        tvl = self._tvl(80)
        det = LiquidityCrisisDetector()
        alerts = det.get_alerts(tvl, protocol_id="proto_x", min_level="normal")
        assert isinstance(alerts, list)

    def test_latest_status(self):
        from liquidity_crisis_model import LiquidityCrisisDetector

        tvl = self._tvl(50)
        det = LiquidityCrisisDetector()
        status = det.latest_status(tvl, protocol_id="proto_y")
        assert "overall_risk" in status
        assert "alert_level" in status
        assert 0 <= status["overall_risk"] <= 1

    def test_alert_to_dict(self):
        from liquidity_crisis_model import LiquidityAlert

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


# ===========================================================================
# volatility_forecaster tests (lightweight - no TF training)
# ===========================================================================


class TestVolatilityForecaster:
    def test_log_returns(self):
        from volatility_forecaster import VolatilityForecaster

        df = _make_ohlcv(60)
        vf = VolatilityForecaster()
        log_ret = vf._log_returns(df["close"])
        assert len(log_ret) == 60
        assert log_ret.isna().sum() == 1  # first row is NaN

    def test_realized_vol(self):
        from volatility_forecaster import VolatilityForecaster

        df = _make_ohlcv(60)
        vf = VolatilityForecaster()
        lr = vf._log_returns(df["close"])
        rv = vf._realized_vol(lr, window=14)
        # After 14 values there should be non-NaN entries
        assert rv.dropna().gt(0).all()

    def test_parkinson_vol(self):
        from volatility_forecaster import VolatilityForecaster

        df = _make_ohlcv(60)
        vf = VolatilityForecaster()
        pv = vf._parkinson_vol(df["high"], df["low"], window=7)
        assert pv.dropna().gt(0).all()

    def test_classify_vol_regime(self):
        from volatility_forecaster import VolatilityForecaster

        vf = VolatilityForecaster()
        assert vf.classify_vol_regime(0.10) == "low"
        assert vf.classify_vol_regime(0.45) == "medium"
        assert vf.classify_vol_regime(0.80) == "high"
        assert vf.classify_vol_regime(1.50) == "extreme"

    def test_predict_raises_before_fit(self):
        from volatility_forecaster import VolatilityForecaster

        vf = VolatilityForecaster(sequence_length=10)
        with pytest.raises(RuntimeError, match="fitted"):
            vf.predict(_make_ohlcv(50))

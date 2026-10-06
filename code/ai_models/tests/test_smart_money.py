import numpy as np
import pandas as pd
import pytest

from .factories import make_wallet_df


class TestSmartMoneyTracker:
    def test_engineer_wallet_features(self):
        from ai_models.models.smart_money import engineer_wallet_features

        wdf = make_wallet_df(50)
        feat = engineer_wallet_features(wdf)
        assert len(feat) == 50
        assert feat.isna().sum().sum() == 0

    def test_fit_and_profile(self):
        from ai_models.models.smart_money import SmartMoneyTracker

        wdf = make_wallet_df(80)
        tracker = SmartMoneyTracker(n_clusters=3)
        tracker.fit(wdf)
        profiles = tracker.profile_wallets(wdf)
        assert len(profiles) == 80
        assert all(0 <= p.smart_money_score <= 100 for p in profiles)

    def test_get_smart_money_wallets(self):
        from ai_models.models.smart_money import SmartMoneyTracker

        wdf = make_wallet_df(60)
        tracker = SmartMoneyTracker(n_clusters=3)
        tracker.fit(wdf)
        top = tracker.get_smart_money_wallets(wdf, top_n=10)
        assert len(top) == 10
        scores = [p.smart_money_score for p in top]
        assert scores == sorted(scores, reverse=True)

    def test_generate_signals(self):
        from ai_models.models.smart_money import SmartMoneyTracker

        rng = np.random.default_rng(5)
        wdf = make_wallet_df(40)
        tracker = SmartMoneyTracker(n_clusters=3)
        tracker.fit(wdf)
        profiles = tracker.profile_wallets(wdf)

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
        from ai_models.models.smart_money import SmartMoneyTracker

        wdf = make_wallet_df(40)
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
        from ai_models.models.smart_money import SmartMoneyTracker

        tracker = SmartMoneyTracker()
        with pytest.raises(RuntimeError, match="fit"):
            tracker.profile_wallets(make_wallet_df(10))

    def test_wallet_profile_to_dict(self):
        from ai_models.models.smart_money import WalletProfile

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

import numpy as np
import pytest
from ai_models.core.persistence import (
    ArtifactError,
    artifact_exists,
    load_artifact,
    save_artifact,
)
from ai_models.models.exploit import ExploitDetector
from ai_models.models.smart_money import SmartMoneyTracker
from ai_models.models.volatility import VolatilityForecaster

from .factories import make_ohlcv, make_onchain_df, make_wallet_df


class TestArtifactFormat:
    def test_round_trip(self, tmp_path):
        save_artifact(tmp_path / "m", "demo", {"a": 1})
        assert artifact_exists(tmp_path / "m")
        state, networks = load_artifact(tmp_path / "m", "demo")
        assert state == {"a": 1}
        assert networks == {}

    def test_tampered_artifact_is_rejected(self, tmp_path):
        save_artifact(tmp_path / "m", "demo", {"a": 1})
        (tmp_path / "m" / "state.joblib").write_bytes(b"corrupt")
        with pytest.raises(ArtifactError):
            load_artifact(tmp_path / "m", "demo")

    def test_wrong_model_type_is_rejected(self, tmp_path):
        save_artifact(tmp_path / "m", "demo", {"a": 1})
        with pytest.raises(ArtifactError):
            load_artifact(tmp_path / "m", "other")

    def test_missing_artifact(self, tmp_path):
        assert not artifact_exists(tmp_path / "none")
        with pytest.raises(ArtifactError):
            load_artifact(tmp_path / "none", "demo")


class TestModelRoundTrips:
    def test_smart_money(self, tmp_path):
        wallets = make_wallet_df(60)
        tracker = SmartMoneyTracker(n_clusters=3).fit(wallets)
        tracker.save(tmp_path)
        restored = SmartMoneyTracker.load(tmp_path)
        original = [p.cluster_label for p in tracker.profile_wallets(wallets)]
        assert [p.cluster_label for p in restored.profile_wallets(wallets)] == original

    def test_exploit_without_autoencoder(self, tmp_path):
        data = make_onchain_df(120)
        detector = ExploitDetector(use_autoencoder=False).fit(data)
        detector.save(tmp_path)
        restored = ExploitDetector.load(tmp_path)
        assert np.allclose(
            restored.score(data)["risk_score"], detector.score(data)["risk_score"]
        )

    def test_unfitted_models_refuse_to_save(self, tmp_path):
        with pytest.raises(RuntimeError):
            VolatilityForecaster().save(tmp_path)
        with pytest.raises(RuntimeError):
            SmartMoneyTracker().save(tmp_path)

    def test_volatility_round_trip(self, tmp_path):
        pytest.importorskip("tensorflow")
        data = make_ohlcv(160)
        model = VolatilityForecaster(
            sequence_length=15, forecast_horizon=5, lstm_units=(8, 4), mc_samples=1
        ).fit(data, epochs=1)
        model.save(tmp_path)
        restored = VolatilityForecaster.load(tmp_path)
        assert restored.predict(data)["predicted_vol"] == pytest.approx(
            model.predict(data)["predicted_vol"], abs=1e-4
        )

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
import pytest_asyncio
from config.settings import settings
from models.portfolio import Portfolio, PortfolioAsset
from models.risk import RiskAssessment
from schemas.risk import RiskAssessmentResponse
from services.ai import AIModelService, frame_from_records, reset_ai_service
from services.risk.risk_service import RiskService

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")


def _daily_frames(symbols, n=200, seed=5):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2025-01-01", periods=n, freq="D", tz="UTC")
    base = rng.normal(0, 0.02, n)
    frames = {}
    for i, symbol in enumerate(symbols):
        returns = 0.6 * base + rng.normal(0, 0.015, n)
        close = 100 * np.cumprod(1 + returns) * (1 + i)
        frames[symbol] = pd.DataFrame(
            {
                "open": close,
                "high": close * 1.01,
                "low": close * 0.99,
                "close": close,
                "volume": np.full(n, 1e6),
            },
            index=idx,
        )
    return frames


def _price_points(n=120, seed=1, start=100.0):
    rng = np.random.default_rng(seed)
    close = start * np.cumprod(1 + rng.normal(0, 0.02, n))
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return [
        {"timestamp": (base + timedelta(days=i)).isoformat(), "close": float(c)}
        for i, c in enumerate(close)
    ]


@pytest.fixture
def ai_service(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "AI_ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    reset_ai_service()
    service = AIModelService()
    yield service
    reset_ai_service()


class TestAIModelService:
    def test_status_reports_fallback_without_artifacts(self, ai_service):
        status = ai_service.status()
        assert status["enabled"] is True
        assert status["package_available"] is True
        assert status["models"]["volatility"]["mode"] == "fallback"
        assert status["models"]["liquidity"]["mode"] == "rule_based"

    def test_load_all_without_artifacts(self, ai_service):
        results = ai_service.load_all()
        assert set(results.values()) == {"no_artifact"}

    async def test_volatility_fallback(self, ai_service):
        frame = frame_from_records(_price_points(), "timestamp")
        result = await ai_service.forecast_volatility(frame)
        assert result["model"] == "ewma_fallback"
        assert result["predicted_vol"] > 0

    async def test_volatility_rejects_short_history(self, ai_service):
        from exceptions.base_exceptions import ValidationException

        frame = frame_from_records(_price_points(n=5), "timestamp")
        with pytest.raises(ValidationException):
            await ai_service.forecast_volatility(frame)

    async def test_correlation_fallback(self, ai_service):
        from services.ai.market_inputs import align_close_prices

        prices = align_close_prices(_daily_frames(["BTC", "ETH", "SOL"]))
        result = await ai_service.predict_correlation(prices)
        assert result["assets"] == ["BTC", "ETH", "SOL"]
        matrix = np.array(result["matrix"])
        assert np.allclose(np.diag(matrix), 1.0)
        assert np.allclose(matrix, matrix.T)
        assert np.linalg.eigvalsh(matrix).min() > 0

    async def test_exploit_unsupervised_flags_spike(self, ai_service):
        rng = np.random.default_rng(0)
        idx = pd.date_range("2025-01-01", periods=80, freq="h", tz="UTC")
        data = pd.DataFrame(
            {
                "flash_loan_volume_usd": rng.uniform(0, 1e5, 80),
                "large_tx_count": rng.integers(0, 10, 80),
                "tvl_change_pct": rng.normal(0, 0.01, 80),
            },
            index=idx,
        )
        data.iloc[-1] = [5e7, 400, -0.7]
        result = await ai_service.detect_exploits(data, protocol_id="pool-1")
        assert result["mode"] == "unsupervised_batch"
        assert result["latest_risk_score"] > 0.5
        assert result["alerts"]

    async def test_exploit_requires_enough_rows(self, ai_service):
        from exceptions.base_exceptions import ValidationException

        data = pd.DataFrame(
            {"flash_loan_volume_usd": [1.0] * 5},
            index=pd.date_range("2025-01-01", periods=5, freq="h"),
        )
        with pytest.raises(ValidationException):
            await ai_service.detect_exploits(data)

    async def test_liquidity_detects_drain_and_depeg(self, ai_service):
        idx = pd.date_range("2025-01-01", periods=60, freq="h", tz="UTC")
        tvl = pd.Series(
            np.concatenate([np.full(40, 1e8), np.linspace(1e8, 3e7, 20)]), index=idx
        )
        peg = pd.Series(
            np.concatenate([np.full(40, 1.0), np.linspace(1.0, 0.9, 20)]), index=idx
        )
        result = await ai_service.assess_liquidity(tvl, price=peg, protocol_id="stable")
        assert result["status"]["alert_level"] in ("warning", "critical")
        assert result["alerts"]

    async def test_smart_money_fits_on_request(self, ai_service):
        rng = np.random.default_rng(2)
        wallets = pd.DataFrame(
            {
                "win_rate": rng.uniform(0.2, 0.9, 30),
                "total_volume_usd_30d": rng.uniform(1e4, 1e8, 30),
                "pnl_90d_pct": rng.uniform(-0.5, 3, 30),
            },
            index=[f"0x{i}" for i in range(30)],
        )
        txs = pd.DataFrame(
            {
                "wallet_address": ["0x1", "0x2"],
                "amount_usd": [50000.0, 60000.0],
                "chain": ["eth", "eth"],
                "token_symbol": ["ETH", "ETH"],
                "direction": ["buy", "sell"],
            }
        )
        result = await ai_service.analyze_smart_money(wallets, txs, top_n=5)
        assert result["mode"] == "fitted_on_request"
        assert len(result["top_wallets"]) == 5

    def test_training_job_persists_and_loads_artifact(self, ai_service):
        import time

        rng = np.random.default_rng(4)
        idx = pd.date_range("2025-01-01", periods=60, freq="h", tz="UTC")
        data = pd.DataFrame(
            {
                "flash_loan_volume_usd": rng.uniform(0, 1e5, 60),
                "large_tx_count": rng.integers(0, 10, 60),
                "tvl_change_pct": rng.normal(0, 0.01, 60),
            },
            index=idx,
        )
        job = ai_service.start_training(
            "exploit",
            data,
            {"epochs": 1, "sequence_length": 6, "use_autoencoder": False},
        )
        for _ in range(600):
            job = ai_service.get_job(job["job_id"])
            if job["status"] in ("done", "failed"):
                break
            time.sleep(0.5)
        assert job["status"] == "done", job.get("error")
        assert ai_service.status()["models"]["exploit"]["mode"] == "trained"
        assert str(ai_service.artifacts_dir) in job["result"]["artifact"]

        fresh = AIModelService()
        assert fresh.load_all()["exploit"] == "loaded"
        assert fresh.get_model("exploit") is not None

    def test_training_job_keeps_artifact_path_fixed_at_start(
        self, ai_service, tmp_path, monkeypatch
    ):
        import time

        rng = np.random.default_rng(8)
        idx = pd.date_range("2025-01-01", periods=60, freq="h", tz="UTC")
        data = pd.DataFrame(
            {
                "flash_loan_volume_usd": rng.uniform(0, 1e5, 60),
                "tvl_change_pct": rng.normal(0, 0.01, 60),
            },
            index=idx,
        )
        original = ai_service.artifacts_dir
        job = ai_service.start_training("exploit", data, {"use_autoencoder": False})
        monkeypatch.setattr(settings, "AI_ARTIFACTS_DIR", str(tmp_path / "elsewhere"))
        for _ in range(600):
            job = ai_service.get_job(job["job_id"])
            if job["status"] in ("done", "failed"):
                break
            time.sleep(0.1)
        assert job["status"] == "done", job.get("error")
        assert job["result"]["artifact"].startswith(str(original))
        assert not (tmp_path / "elsewhere").exists()

    def test_training_rejects_unknown_model(self, ai_service):
        from exceptions.base_exceptions import ResourceNotFoundException

        with pytest.raises(ResourceNotFoundException):
            ai_service.start_training("nope", pd.DataFrame({"a": [1]}))

    def test_disabled_service_raises(self, ai_service, monkeypatch):
        from services.ai import AIModelsUnavailable

        monkeypatch.setattr(settings, "AI_MODELS_ENABLED", False)
        with pytest.raises(AIModelsUnavailable):
            ai_service.reload()


class TestAIEndpoints:
    PREFIX = "/api/v1/ai"

    @pytest.mark.asyncio
    async def test_requires_authentication(self, async_client):
        response = await async_client.get(f"{self.PREFIX}/status")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_status_and_volatility(
        self, async_client, auth_headers, ai_service, monkeypatch
    ):
        import services.ai.ai_service as module

        monkeypatch.setattr(module, "_ai_service", ai_service)
        status = await async_client.get(f"{self.PREFIX}/status", headers=auth_headers)
        assert status.status_code == 200
        assert status.json()["models"]["volatility"]["mode"] == "fallback"

        response = await async_client.post(
            f"{self.PREFIX}/volatility",
            json={"prices": _price_points(), "horizon_days": 7},
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["model"] == "ewma_fallback"
        assert body["vol_bucket"] in ("low", "medium", "high", "extreme")

    @pytest.mark.asyncio
    async def test_correlation_endpoint(
        self, async_client, auth_headers, ai_service, monkeypatch
    ):
        import services.ai.ai_service as module

        monkeypatch.setattr(module, "_ai_service", ai_service)
        payload = {
            "prices": {
                "BTC": _price_points(seed=1),
                "ETH": _price_points(seed=2),
            }
        }
        response = await async_client.post(
            f"{self.PREFIX}/correlation", json=payload, headers=auth_headers
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["assets"] == ["BTC", "ETH"]
        assert body["matrix"][0][0] == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_validation_errors(
        self, async_client, auth_headers, ai_service, monkeypatch
    ):
        import services.ai.ai_service as module

        monkeypatch.setattr(module, "_ai_service", ai_service)
        response = await async_client.post(
            f"{self.PREFIX}/volatility", json={}, headers=auth_headers
        )
        assert response.status_code == 422
        response = await async_client.post(
            f"{self.PREFIX}/volatility",
            json={"prices": _price_points(n=5)},
            headers=auth_headers,
        )
        assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_market_data_unavailable_returns_503(
        self, async_client, auth_headers, ai_service, monkeypatch
    ):
        import services.ai.ai_service as module
        from services.market.market_data_service import MarketDataService

        monkeypatch.setattr(module, "_ai_service", ai_service)

        async def empty(*args, **kwargs):
            return []

        with patch.object(MarketDataService, "get_historical_data", empty):
            response = await async_client.post(
                f"{self.PREFIX}/volatility",
                json={"symbol": "BTC"},
                headers=auth_headers,
            )
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_training_requires_admin(
        self, async_client, auth_headers, ai_service, monkeypatch
    ):
        import services.ai.ai_service as module

        monkeypatch.setattr(module, "_ai_service", ai_service)
        records = [
            {"timestamp": f"2025-01-{d:02d}T00:00:00Z", "close": 1.0 + d}
            for d in range(1, 20)
        ]
        response = await async_client.post(
            f"{self.PREFIX}/models/volatility/train",
            json={"records": records},
            headers=auth_headers,
        )
        assert response.status_code == 403


@pytest_asyncio.fixture
async def seeded_portfolio(db_session, test_user):
    portfolio = Portfolio(
        user_id=test_user.id, name="Main", total_value_usd=Decimal("10000")
    )
    db_session.add(portfolio)
    await db_session.flush()
    for symbol, value, qty in [("BTC", 6000, 0.1), ("ETH", 3000, 1), ("SOL", 1000, 10)]:
        db_session.add(
            PortfolioAsset(
                portfolio_id=portfolio.id,
                asset_symbol=symbol,
                quantity=Decimal(str(qty)),
                current_value_usd=Decimal(str(value)),
                current_price=Decimal(str(value / qty)),
            )
        )
    await db_session.commit()
    return portfolio


async def _fake_history(symbols, days=None, market_data=None):
    frames = _daily_frames(["BTC", "ETH", "SOL"])
    return {s: frames[s] for s in symbols if s in frames}


class TestRiskServiceAIIntegration:
    @pytest.mark.asyncio
    async def test_assessment_uses_ai_and_persists(
        self, db_session, test_user, seeded_portfolio, ai_service
    ):
        with patch("services.risk.risk_service.fetch_price_history", _fake_history):
            service = RiskService(db_session, ai_service=ai_service)
            assessment = await service.assess_portfolio_risk(
                seeded_portfolio.id, test_user.id
            )
        assert isinstance(assessment, RiskAssessment)
        response = RiskAssessmentResponse.from_orm_assessment(assessment)
        assert 0 <= float(response.risk_score) <= 100
        assert response.ai_insights["volatility_forecast"]["model"] == "ewma_fallback"
        assert response.ai_insights["correlation_model"] == "ledoit_wolf_shrinkage"
        assert set(response.correlation_matrix) == {"BTC", "ETH", "SOL"}
        assert {t["scenario_name"] for t in response.stress_tests} >= {
            "Market Crash",
            "Crypto Winter",
        }
        assert response.assessment_date.tzinfo is not None

    @pytest.mark.asyncio
    async def test_reassessment_supersedes_previous(
        self, db_session, test_user, seeded_portfolio, ai_service
    ):
        from sqlalchemy import select

        with patch("services.risk.risk_service.fetch_price_history", _fake_history):
            service = RiskService(db_session, ai_service=ai_service)
            await service.assess_portfolio_risk(seeded_portfolio.id, test_user.id)
            await service.assess_portfolio_risk(seeded_portfolio.id, test_user.id)
        rows = (await db_session.execute(select(RiskAssessment))).scalars().all()
        assert len(rows) == 2
        assert sum(1 for r in rows if r.is_current) == 1

    @pytest.mark.asyncio
    async def test_missing_market_data_raises_domain_error(
        self, db_session, test_user, seeded_portfolio, ai_service
    ):
        from services.ai import AIModelsUnavailable

        async def none(symbols, days=None, market_data=None):
            raise AIModelsUnavailable("Insufficient market history")

        with patch("services.risk.risk_service.fetch_price_history", none):
            service = RiskService(db_session, ai_service=ai_service)
            with pytest.raises(AIModelsUnavailable):
                await service.assess_portfolio_risk(seeded_portfolio.id, test_user.id)

    @pytest.mark.asyncio
    async def test_monitoring_flags_concentration(
        self, db_session, test_user, seeded_portfolio, ai_service
    ):
        with patch("services.risk.risk_service.fetch_price_history", _fake_history):
            service = RiskService(db_session, ai_service=ai_service)
            report = await service.monitor_portfolio_risk(
                seeded_portfolio.id, test_user.id
            )
        assert any(
            a["type"] == "concentration_limit" and a["asset"] == "BTC"
            for a in report["alerts"]
        )
        assert "ai_insights" in report

    @pytest.mark.asyncio
    async def test_stress_shocks_match_symbols(
        self, db_session, test_user, seeded_portfolio, ai_service
    ):
        service = RiskService(db_session, ai_service=ai_service)
        portfolio = await service._get_portfolio_with_assets(
            seeded_portfolio.id, test_user.id
        )
        results = await service._perform_stress_tests(portfolio)
        crash = next(r for r in results if r["scenario_name"] == "Market Crash")
        assert crash["asset_impacts"]["BTC"]["shock_percentage"] == -50.0
        assert crash["asset_impacts"]["SOL"]["shock_percentage"] == -60.0
        assert crash["potential_loss_percent"] == pytest.approx(54.0)

    @pytest.mark.asyncio
    async def test_invalid_ids_return_placeholder(self, db_session, ai_service):
        service = RiskService(db_session, ai_service=ai_service)
        result = await service.assess_portfolio_risk("not-a-uuid", "also-bad")
        assert isinstance(result, dict) and result["risk_level"] == "unknown"

    def test_domain_exceptions_instantiate(self):
        from exceptions.base_exceptions import (
            BusinessLogicException,
            ValidationException,
        )

        assert BusinessLogicException("x").error_code == "BUSINESS_LOGIC"
        assert ValidationException("x", field="f").details["field"] == "f"

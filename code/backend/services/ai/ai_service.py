import asyncio
import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from config.settings import settings
from exceptions.base_exceptions import (
    BusinessLogicException,
    ResourceNotFoundException,
    ValidationException,
)

from .bootstrap import BACKEND_ROOT, ensure_ai_models_importable

logger = logging.getLogger(__name__)

MODEL_NAMES = ("volatility", "correlation", "exploit", "smart_money")
STATELESS_MODELS = ("liquidity",)
MAX_JOB_HISTORY = 100


class AIModelsUnavailable(BusinessLogicException):
    http_status = 503

    def __init__(self, message: str = "AI models are not available") -> None:
        super().__init__(message, error_code="AI_MODELS_UNAVAILABLE")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def frame_from_records(
    records: List[Dict[str, Any]],
    index_field: Optional[str] = None,
    name: str = "data",
    max_rows: Optional[int] = None,
) -> pd.DataFrame:
    limit = max_rows or settings.ai.AI_MAX_INPUT_ROWS
    if not records:
        raise ValidationException(f"{name} must contain at least one record")
    if len(records) > limit:
        raise ValidationException(f"{name} exceeds the maximum of {limit} rows")
    df = pd.DataFrame.from_records(records)
    if index_field:
        if index_field not in df.columns:
            raise ValidationException(f"{name} records must include '{index_field}'")
        if index_field == "timestamp":
            df[index_field] = pd.to_datetime(df[index_field], errors="coerce", utc=True)
            df = df.dropna(subset=[index_field])
            if df.empty:
                raise ValidationException(f"{name} has no valid timestamps")
        df = df.set_index(index_field).sort_index()
    return df


class AIModelService:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._models: Dict[str, Any] = {}
        self._model_meta: Dict[str, Dict[str, Any]] = {}
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._executor: Optional[ThreadPoolExecutor] = None
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._semaphore_loop: Optional[asyncio.AbstractEventLoop] = None
        self._package_ok: Optional[bool] = None
        self._liquidity: Any = None
        self._artifacts_dir: Optional[Path] = None

    @property
    def enabled(self) -> bool:
        return bool(settings.ai.AI_MODELS_ENABLED)

    @property
    def artifacts_dir(self) -> Path:
        configured = Path(settings.ai.AI_ARTIFACTS_DIR)
        resolved = configured if configured.is_absolute() else BACKEND_ROOT / configured
        if self._artifacts_dir != resolved:
            self._artifacts_dir = resolved
        return resolved

    def artifact_path(self, name: str) -> Path:
        self._require_package()
        from ai_models.core.registry import ARTIFACT_DIRS

        if name not in ARTIFACT_DIRS:
            raise ResourceNotFoundException(
                f"Unknown AI model: {name}", resource_type="AI model", resource_id=name
            )
        return self.artifacts_dir / ARTIFACT_DIRS[name]

    def _package(self) -> bool:
        if self._package_ok is None:
            self._package_ok = ensure_ai_models_importable(settings.ai.AI_MODELS_DIR)
            if not self._package_ok:
                logger.warning("ai_models package could not be imported")
        return self._package_ok

    def _require_package(self) -> None:
        if not self.enabled:
            raise AIModelsUnavailable("AI models are disabled by configuration")
        if not self._package():
            raise AIModelsUnavailable("The ai_models package could not be imported")

    def _get_executor(self) -> ThreadPoolExecutor:
        if self._executor is None:
            self._executor = ThreadPoolExecutor(
                max_workers=settings.ai.AI_MAX_CONCURRENT_JOBS,
                thread_name_prefix="chainfinity-ai",
            )
        return self._executor

    def _get_semaphore(self) -> asyncio.Semaphore:
        loop = asyncio.get_running_loop()
        if self._semaphore is None or self._semaphore_loop is not loop:
            self._semaphore = asyncio.Semaphore(settings.ai.AI_MAX_CONCURRENT_JOBS)
            self._semaphore_loop = loop
        return self._semaphore

    async def _run(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_running_loop()
        async with self._get_semaphore():
            future = loop.run_in_executor(
                self._get_executor(), lambda: fn(*args, **kwargs)
            )
            try:
                return await asyncio.wait_for(
                    future, timeout=settings.ai.AI_INFERENCE_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                raise BusinessLogicException(
                    "AI inference timed out; try again with less data"
                )

    async def shutdown(self) -> None:
        executor, self._executor = self._executor, None
        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=True)

    def _model_classes(self) -> Dict[str, Any]:
        from ai_models.models.correlation import CorrelationPredictor
        from ai_models.models.exploit import ExploitDetector
        from ai_models.models.smart_money import SmartMoneyTracker
        from ai_models.models.volatility import VolatilityForecaster

        return {
            "volatility": VolatilityForecaster,
            "correlation": CorrelationPredictor,
            "exploit": ExploitDetector,
            "smart_money": SmartMoneyTracker,
        }

    def _load_one(self, name: str) -> bool:
        from ai_models.core.persistence import artifact_exists

        path = self.artifact_path(name)
        if not artifact_exists(path):
            return False
        model = self._model_classes()[name].load(path)
        with self._lock:
            self._models[name] = model
            self._model_meta[name] = {
                "source": "artifact",
                "loaded_at": _utcnow(),
                "path": str(path),
            }
        logger.info("Loaded AI model '%s' from %s", name, path)
        return True

    def load_all(self) -> Dict[str, str]:
        results: Dict[str, str] = {}
        if not self.enabled or not self._package():
            return {name: "unavailable" for name in MODEL_NAMES}
        for name in MODEL_NAMES:
            try:
                results[name] = "loaded" if self._load_one(name) else "no_artifact"
            except Exception as exc:
                logger.error("Failed to load AI model '%s': %s", name, exc)
                results[name] = f"error: {exc}"
        return results

    async def startup(self) -> Dict[str, str]:
        if not settings.ai.AI_AUTOLOAD_ON_STARTUP:
            return {}
        return await asyncio.get_running_loop().run_in_executor(None, self.load_all)

    def get_model(self, name: str) -> Any:
        with self._lock:
            return self._models.get(name)

    def set_model(self, name: str, model: Any, source: str = "runtime") -> None:
        with self._lock:
            self._models[name] = model
            self._model_meta[name] = {
                "source": source,
                "loaded_at": _utcnow(),
                "path": None,
            }

    def status(self) -> Dict[str, Any]:
        package_ok = self.enabled and self._package()
        tf_available = False
        if package_ok:
            from ai_models.core.compat import TF_AVAILABLE

            tf_available = bool(TF_AVAILABLE)
        models: Dict[str, Any] = {}
        for name in MODEL_NAMES:
            with self._lock:
                loaded = name in self._models
                meta = dict(self._model_meta.get(name, {}))
            fallback = {
                "volatility": "ewma_volatility",
                "correlation": "ledoit_wolf_shrinkage",
                "exploit": "isolation_forest_on_request",
                "smart_money": "kmeans_on_request",
            }[name]
            models[name] = {
                "loaded": loaded,
                "mode": "trained" if loaded else "fallback",
                "fallback": None if loaded else fallback,
                "source": meta.get("source"),
                "loaded_at": meta.get("loaded_at"),
            }
        models["liquidity"] = {
            "loaded": package_ok,
            "mode": "rule_based" if package_ok else "unavailable",
            "fallback": None,
            "source": "builtin",
            "loaded_at": None,
        }
        return {
            "enabled": self.enabled,
            "package_available": bool(package_ok),
            "tensorflow_available": tf_available,
            "models": models,
        }

    def _stateless_liquidity(self) -> Any:
        if self._liquidity is None:
            from ai_models.models.liquidity import LiquidityCrisisDetector

            self._liquidity = LiquidityCrisisDetector()
        return self._liquidity

    async def forecast_volatility(
        self, prices: pd.DataFrame, horizon: Optional[int] = None
    ) -> Dict[str, Any]:
        self._require_package()
        from ai_models.models.volatility import ewma_volatility_forecast

        model = self.get_model("volatility")

        def work() -> Dict[str, Any]:
            if model is not None:
                try:
                    return model.predict(prices)
                except ValueError as exc:
                    logger.info("LSTM volatility unavailable (%s); using EWMA", exc)
            return ewma_volatility_forecast(prices, forecast_horizon=horizon or 7)

        try:
            return await self._run(work)
        except ValueError as exc:
            raise ValidationException(str(exc))

    async def predict_correlation(self, prices: pd.DataFrame) -> Dict[str, Any]:
        self._require_package()
        from ai_models.models.correlation import shrunk_correlation

        model = self.get_model("correlation")
        asset_cols = sorted(c for c in prices.columns if str(c).startswith("asset_"))

        def work() -> Dict[str, Any]:
            if (
                model is not None
                and getattr(model, "asset_columns", None) == asset_cols
            ):
                try:
                    frame = model.predict_frame(prices)
                    return {"matrix": frame, "model": "lstm"}
                except ValueError as exc:
                    logger.info(
                        "LSTM correlation unavailable (%s); using shrinkage", exc
                    )
            returns = np.log(prices[asset_cols].astype(float)).diff().dropna()
            names = [c[len("asset_") :] for c in asset_cols]
            frame = shrunk_correlation(returns)
            frame.index = names
            frame.columns = names
            return {"matrix": frame, "model": "ledoit_wolf_shrinkage"}

        if len(asset_cols) < 2:
            raise ValidationException("At least two asset price columns are required")
        try:
            result = await self._run(work)
        except ValueError as exc:
            raise ValidationException(str(exc))
        frame = result["matrix"]
        return {
            "assets": [str(c).upper() for c in frame.columns],
            "matrix": frame.round(6).values.tolist(),
            "model": result["model"],
        }

    async def detect_exploits(
        self,
        observations: pd.DataFrame,
        protocol_id: str = "unknown",
        threshold: float = 0.40,
    ) -> Dict[str, Any]:
        self._require_package()
        from ai_models.models.exploit import ExploitDetector

        trained = self.get_model("exploit")

        def work() -> Dict[str, Any]:
            detector = trained
            mode = "trained"
            if detector is None:
                if len(observations) < 30:
                    raise ValueError(
                        "At least 30 observations are required when no trained exploit "
                        "model is loaded"
                    )
                detector = ExploitDetector(use_autoencoder=False).fit(observations)
                mode = "unsupervised_batch"
            scored = detector.score(observations)
            alerts = detector.get_alerts(
                observations, protocol_id=protocol_id, threshold=threshold
            )
            return {
                "mode": mode,
                "observations": int(len(scored)),
                "max_risk_score": round(float(scored["risk_score"].max()), 4),
                "latest_risk_score": round(float(scored["risk_score"].iloc[-1]), 4),
                "latest_severity": str(scored["severity"].iloc[-1]),
                "alerts": [a.to_dict() for a in alerts],
            }

        try:
            return await self._run(work)
        except ValueError as exc:
            raise ValidationException(str(exc))

    async def assess_liquidity(
        self,
        tvl: pd.Series,
        spread: Optional[pd.Series] = None,
        price: Optional[pd.Series] = None,
        protocol_returns: Optional[pd.DataFrame] = None,
        protocol_id: str = "unknown",
        min_level: str = "watch",
        include_alerts: bool = True,
    ) -> Dict[str, Any]:
        self._require_package()
        detector = self._stateless_liquidity()

        def work() -> Dict[str, Any]:
            status = detector.latest_status(
                tvl, spread, price, protocol_returns, protocol_id
            )
            alerts: List[Dict[str, Any]] = []
            if include_alerts:
                alerts = [
                    a.to_dict()
                    for a in detector.get_alerts(
                        tvl, spread, price, protocol_returns, protocol_id, min_level
                    )
                ]
            return {"status": status, "alerts": alerts}

        try:
            return await self._run(work)
        except ValueError as exc:
            raise ValidationException(str(exc))

    async def analyze_smart_money(
        self,
        wallets: pd.DataFrame,
        transactions: Optional[pd.DataFrame] = None,
        top_n: int = 50,
        min_amount_usd: float = 10_000,
        transfers: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        self._require_package()
        from ai_models.models.smart_money import (
            SmartMoneyTracker,
            compute_wallet_centrality,
        )

        trained = self.get_model("smart_money")

        def work() -> Dict[str, Any]:
            tracker = trained
            mode = "trained"
            if tracker is None:
                clusters = min(5, len(wallets))
                if clusters < 2:
                    raise ValueError("At least two wallets are required")
                tracker = SmartMoneyTracker(n_clusters=clusters).fit(wallets)
                mode = "fitted_on_request"
            centrality = (
                compute_wallet_centrality(transfers)
                if transfers is not None and not transfers.empty
                else None
            )
            profiles = tracker.profile_wallets(wallets, centrality=centrality)
            ranked = sorted(profiles, key=lambda p: p.smart_money_score, reverse=True)
            result: Dict[str, Any] = {
                "mode": mode,
                "wallets_analyzed": len(profiles),
                "top_wallets": [p.to_dict() for p in ranked[:top_n]],
                "signals": [],
                "flows": [],
            }
            if transactions is not None and not transactions.empty:
                signals = tracker.generate_signals(
                    transactions, profiles, min_amount_usd=min_amount_usd
                )
                result["signals"] = [s.to_dict() for s in signals[:200]]
                flows = tracker.cross_chain_flow_summary(transactions, profiles)
                result["flows"] = flows.round(2).to_dict(orient="records")
            return result

        try:
            return await self._run(work)
        except ValueError as exc:
            raise ValidationException(str(exc))
        except KeyError as exc:
            raise ValidationException(f"Missing required column: {exc}")

    def _register_job(self, model: str) -> str:
        job_id = str(uuid.uuid4())
        with self._lock:
            active = [
                j for j in self._jobs.values() if j["status"] in ("queued", "running")
            ]
            if any(j["model"] == model for j in active):
                raise BusinessLogicException(
                    f"A training job for '{model}' is already in progress"
                )
            self._jobs[job_id] = {
                "job_id": job_id,
                "model": model,
                "status": "queued",
                "created_at": _utcnow(),
                "finished_at": None,
                "error": None,
                "result": None,
            }
            if len(self._jobs) > MAX_JOB_HISTORY:
                finished = sorted(
                    (
                        j
                        for j in self._jobs.values()
                        if j["status"] in ("done", "failed")
                    ),
                    key=lambda j: j["created_at"],
                )
                for stale in finished[: len(self._jobs) - MAX_JOB_HISTORY]:
                    self._jobs.pop(stale["job_id"], None)
        return job_id

    def _update_job(self, job_id: str, **fields: Any) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(fields)

    def get_job(self, job_id: str) -> Dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise ResourceNotFoundException(
                    "Training job not found",
                    resource_type="training job",
                    resource_id=job_id,
                )
            return dict(job)

    def list_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            jobs = sorted(
                self._jobs.values(), key=lambda j: j["created_at"], reverse=True
            )
            return [dict(j) for j in jobs[:limit]]

    def _train_blocking(
        self, name: str, data: pd.DataFrame, params: Dict[str, Any], target: Path
    ) -> Dict[str, Any]:
        classes = self._model_classes()
        epochs = int(params.get("epochs", 30))
        if name == "volatility":
            model = classes[name](
                sequence_length=int(params.get("sequence_length", 30)),
                forecast_horizon=int(params.get("forecast_horizon", 7)),
            )
            model.fit(data, epochs=epochs)
        elif name == "correlation":
            model = classes[name](
                sequence_length=int(params.get("sequence_length", 30)),
                target_window=int(params.get("target_window", 14)),
            )
            model.fit(data, epochs=epochs)
        elif name == "exploit":
            model = classes[name](
                sequence_length=int(params.get("sequence_length", 24)),
                contamination=float(params.get("contamination", 0.05)),
                use_autoencoder=bool(params.get("use_autoencoder", True)),
            )
            model.fit(data, epochs=epochs)
        else:
            model = classes[name](n_clusters=int(params.get("n_clusters", 5)))
            model.fit(data)
        model.save(target)
        with self._lock:
            self._models[name] = model
            self._model_meta[name] = {
                "source": "artifact",
                "loaded_at": _utcnow(),
                "path": str(target),
            }
        return {"artifact": str(target), "rows": int(len(data))}

    def start_training(
        self, name: str, data: pd.DataFrame, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        self._require_package()
        if name not in MODEL_NAMES:
            raise ResourceNotFoundException(
                f"Unknown AI model: {name}", resource_type="AI model", resource_id=name
            )
        if name in ("volatility", "correlation", "exploit"):
            from ai_models.core.compat import TF_AVAILABLE

            if not TF_AVAILABLE and name != "exploit":
                raise AIModelsUnavailable(
                    "TensorFlow is not installed; install requirements-ml.txt to train this model"
                )
        target = self.artifact_path(name)
        job_id = self._register_job(name)
        params = dict(params or {})

        def runner() -> None:
            self._update_job(job_id, status="running")
            try:
                result = self._train_blocking(name, data, params, target)
                self._update_job(
                    job_id, status="done", result=result, finished_at=_utcnow()
                )
            except Exception as exc:
                logger.error("Training job %s failed: %s", job_id, exc, exc_info=True)
                self._update_job(
                    job_id, status="failed", error=str(exc), finished_at=_utcnow()
                )

        threading.Thread(target=runner, name=f"ai-train-{name}", daemon=True).start()
        return self.get_job(job_id)

    def reload(self, name: Optional[str] = None) -> Dict[str, str]:
        self._require_package()
        names: Tuple[str, ...] = (name,) if name else MODEL_NAMES
        results: Dict[str, str] = {}
        for item in names:
            if item not in MODEL_NAMES:
                raise ResourceNotFoundException(
                    f"Unknown AI model: {item}",
                    resource_type="AI model",
                    resource_id=item,
                )
            try:
                results[item] = "loaded" if self._load_one(item) else "no_artifact"
            except Exception as exc:
                results[item] = f"error: {exc}"
        return results


_ai_service: Optional[AIModelService] = None


def get_ai_service() -> AIModelService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIModelService()
    return _ai_service


def reset_ai_service() -> None:
    global _ai_service
    _ai_service = None

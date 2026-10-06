import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List
from uuid import UUID

import pandas as pd
from app.api.dependencies import get_current_user, require_admin
from config.database import get_async_session
from exceptions.base_exceptions import ResourceNotFoundException, ValidationException
from fastapi import APIRouter, Depends, Query
from models.portfolio import Portfolio
from models.user import User
from schemas.ai import (
    AIStatusResponse,
    CorrelationRequest,
    CorrelationResponse,
    ExploitRequest,
    ExploitResponse,
    LiquidityRequest,
    LiquidityResponse,
    PortfolioAIInsights,
    ReloadResponse,
    SmartMoneyRequest,
    SmartMoneyResponse,
    TrainingJob,
    TrainRequest,
    VolatilityRequest,
    VolatilityResponse,
)
from services.ai import AIModelService, frame_from_records, get_ai_service
from services.ai.market_inputs import (
    align_close_prices,
    fetch_price_history,
    normalize_symbol,
)
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)
router = APIRouter()


def _service() -> AIModelService:
    return get_ai_service()


def _price_frame(points: List[Any], name: str) -> pd.DataFrame:
    records = [p.model_dump() for p in points]
    return frame_from_records(records, index_field="timestamp", name=name)


def _series(points: List[Any], name: str) -> pd.Series:
    frame = frame_from_records(
        [p.model_dump() for p in points], index_field="timestamp", name=name
    )
    return frame["value"].astype(float)


@router.get("/status", response_model=AIStatusResponse)
async def ai_status(
    current_user: User = Depends(get_current_user),
    service: AIModelService = Depends(_service),
) -> Any:
    return service.status()


@router.post("/volatility", response_model=VolatilityResponse)
async def forecast_volatility(
    payload: VolatilityRequest,
    current_user: User = Depends(get_current_user),
    service: AIModelService = Depends(_service),
) -> Any:
    symbol = normalize_symbol(payload.symbol) if payload.symbol else None
    if payload.prices:
        frame = _price_frame(payload.prices, "prices")
    else:
        history = await fetch_price_history([symbol])
        frame = history[symbol]
    result = await service.forecast_volatility(frame, horizon=payload.horizon_days)
    return {"symbol": symbol, **result}


@router.post("/correlation", response_model=CorrelationResponse)
async def predict_correlation(
    payload: CorrelationRequest,
    current_user: User = Depends(get_current_user),
    service: AIModelService = Depends(_service),
) -> Any:
    if payload.prices:
        frames = {
            normalize_symbol(sym): _price_frame(points, f"prices[{sym}]")
            for sym, points in payload.prices.items()
        }
    else:
        frames = await fetch_price_history(payload.symbols)
    prices = align_close_prices(frames)
    if prices.shape[1] < 2:
        raise ValidationException("At least two assets with price history are required")
    if len(prices) < 20:
        raise ValidationException(
            "At least 20 overlapping daily observations are required"
        )
    return await service.predict_correlation(prices)


@router.post("/exploit-detection", response_model=ExploitResponse)
async def detect_exploits(
    payload: ExploitRequest,
    current_user: User = Depends(get_current_user),
    service: AIModelService = Depends(_service),
) -> Any:
    frame = frame_from_records(
        [o.model_dump() for o in payload.observations],
        index_field="timestamp",
        name="observations",
    )
    result = await service.detect_exploits(
        frame, protocol_id=payload.protocol_id, threshold=payload.threshold
    )
    return {"protocol_id": payload.protocol_id, **result}


@router.post("/liquidity", response_model=LiquidityResponse)
async def assess_liquidity(
    payload: LiquidityRequest,
    current_user: User = Depends(get_current_user),
    service: AIModelService = Depends(_service),
) -> Any:
    tvl = _series(payload.tvl, "tvl")
    spread = _series(payload.spread, "spread") if payload.spread else None
    price = _series(payload.peg_price, "peg_price") if payload.peg_price else None
    returns = None
    if payload.protocol_returns:
        returns = pd.DataFrame(
            {
                name: _series(points, f"protocol_returns[{name}]")
                for name, points in payload.protocol_returns.items()
            }
        )
    service_instance = service
    if payload.peg_value != 1.0:
        from ai_models.models.liquidity import LiquidityCrisisDetector

        detector = LiquidityCrisisDetector(peg_value=payload.peg_value)
        service_instance = AIModelService()
        service_instance._liquidity = detector
    return await service_instance.assess_liquidity(
        tvl,
        spread,
        price,
        returns,
        protocol_id=payload.protocol_id,
        min_level=payload.min_level,
        include_alerts=payload.include_alerts,
    )


@router.post("/smart-money", response_model=SmartMoneyResponse)
async def analyze_smart_money(
    payload: SmartMoneyRequest,
    current_user: User = Depends(get_current_user),
    service: AIModelService = Depends(_service),
) -> Any:
    wallets = frame_from_records(
        [w.model_dump() for w in payload.wallets], index_field="address", name="wallets"
    )
    transactions = (
        frame_from_records(
            [t.model_dump() for t in payload.transactions], name="transactions"
        )
        if payload.transactions
        else None
    )
    transfers = (
        frame_from_records(
            [t.model_dump() for t in payload.transfers], name="transfers"
        )
        if payload.transfers
        else None
    )
    return await service.analyze_smart_money(
        wallets,
        transactions,
        top_n=payload.top_n,
        min_amount_usd=payload.min_amount_usd,
        transfers=transfers,
    )


@router.get("/portfolio/{portfolio_id}/insights", response_model=PortfolioAIInsights)
async def portfolio_insights(
    portfolio_id: UUID,
    horizon_days: int = Query(7, ge=2, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    service: AIModelService = Depends(_service),
) -> Any:
    stmt = (
        select(Portfolio)
        .options(selectinload(Portfolio.assets))
        .where(
            and_(
                Portfolio.id == portfolio_id,
                Portfolio.user_id == current_user.id,
                Portfolio.is_deleted == False,
            )
        )
    )
    portfolio = (await db.execute(stmt)).scalar_one_or_none()
    if portfolio is None:
        raise ResourceNotFoundException(
            "Portfolio not found",
            resource_type="portfolio",
            resource_id=str(portfolio_id),
        )
    held: Dict[str, Decimal] = {}
    for asset in portfolio.assets:
        value = asset.current_value_usd or Decimal("0")
        if asset.asset_symbol and value > 0:
            symbol = normalize_symbol(asset.asset_symbol)
            held[symbol] = held.get(symbol, Decimal("0")) + value
    if not held:
        raise ValidationException("Portfolio has no priced assets to analyze")

    ranked = sorted(held, key=lambda s: held[s], reverse=True)
    from config.settings import settings

    ranked = ranked[: settings.ai.AI_MAX_ASSETS]
    warnings: List[str] = []
    frames: Dict[str, pd.DataFrame] = {}
    history = await fetch_price_history(ranked)
    frames.update(history)
    for missing in [s for s in ranked if s not in frames]:
        warnings.append(f"No market history available for {missing}")

    volatility: Dict[str, Any] = {}
    for symbol, frame in frames.items():
        try:
            result = await service.forecast_volatility(frame, horizon=horizon_days)
            volatility[symbol] = {"symbol": symbol, **result}
        except Exception as exc:
            warnings.append(f"Volatility forecast failed for {symbol}: {exc}")

    correlation = None
    if len(frames) >= 2:
        prices = align_close_prices(frames)
        if prices.shape[1] >= 2 and len(prices) >= 20:
            correlation = await service.predict_correlation(prices)
        else:
            warnings.append("Not enough overlapping history to estimate correlations")
    else:
        warnings.append("At least two priced assets are needed for correlations")

    return {
        "portfolio_id": portfolio_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "assets": list(frames.keys()),
        "correlation": correlation,
        "volatility": volatility,
        "warnings": warnings,
    }


@router.post("/models/{model_name}/train", response_model=TrainingJob, status_code=202)
async def train_model(
    model_name: str,
    payload: TrainRequest,
    admin: User = Depends(require_admin),
    service: AIModelService = Depends(_service),
) -> Any:
    index_field = payload.index_field if model_name != "smart_money" else "address"
    frame = frame_from_records(payload.records, index_field=index_field, name="records")
    job = service.start_training(model_name, frame, payload.params)
    logger.info("Admin %s started training for %s", admin.id, model_name)
    return job


@router.get("/jobs", response_model=List[TrainingJob])
async def list_jobs(
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    service: AIModelService = Depends(_service),
) -> Any:
    return service.list_jobs(limit)


@router.get("/jobs/{job_id}", response_model=TrainingJob)
async def get_job(
    job_id: UUID,
    admin: User = Depends(require_admin),
    service: AIModelService = Depends(_service),
) -> Any:
    return service.get_job(str(job_id))


@router.post("/models/reload", response_model=ReloadResponse)
async def reload_models(
    model_name: str = Query(None),
    admin: User = Depends(require_admin),
    service: AIModelService = Depends(_service),
) -> Any:
    return {"results": service.reload(model_name)}

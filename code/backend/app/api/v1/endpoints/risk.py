import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.api.dependencies import get_current_user
from config.database import get_async_session
from exceptions.base_exceptions import BaseChainFinityException
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.portfolio import Portfolio
from models.risk import AlertRule, AlertType, RiskAssessment
from models.user import User
from schemas.risk import AlertRuleCreate, RiskAssessmentResponse
from services.risk.risk_service import RiskService, _to_jsonable
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()


def _not_found(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


def _internal(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
    )


@router.get("/assessments", response_model=List[RiskAssessmentResponse])
async def list_risk_assessments(
    portfolio_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    try:
        query = select(RiskAssessment).where(RiskAssessment.user_id == current_user.id)
        if portfolio_id:
            query = query.where(RiskAssessment.portfolio_id == portfolio_id)
        query = (
            query.order_by(desc(RiskAssessment.created_at)).limit(limit).offset(offset)
        )
        result = await db.execute(query)
        return [
            RiskAssessmentResponse.from_orm_assessment(a)
            for a in result.scalars().all()
        ]
    except Exception as e:
        logger.error(f"Error listing risk assessments: {e}")
        raise _internal("Failed to retrieve risk assessments")


@router.get("/assessments/{assessment_id}", response_model=RiskAssessmentResponse)
async def get_risk_assessment(
    assessment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    try:
        query = select(RiskAssessment).where(
            and_(
                RiskAssessment.id == assessment_id,
                RiskAssessment.user_id == current_user.id,
            )
        )
        result = await db.execute(query)
        assessment = result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting risk assessment: {e}")
        raise _internal("Failed to retrieve risk assessment")
    if not assessment:
        raise _not_found("Risk assessment not found")
    return RiskAssessmentResponse.from_orm_assessment(assessment)


@router.post("/assess/{portfolio_id}", response_model=RiskAssessmentResponse)
async def assess_portfolio_risk(
    portfolio_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    try:
        result = await RiskService(db).assess_portfolio_risk(
            portfolio_id=portfolio_id, user_id=current_user.id
        )
    except (HTTPException, BaseChainFinityException):
        raise
    except Exception as e:
        logger.error(f"Error assessing portfolio risk: {e}")
        raise _internal("Failed to assess portfolio risk")
    if isinstance(result, dict):
        raise _not_found("Portfolio not found")
    return RiskAssessmentResponse.from_orm_assessment(result)


@router.get("/metrics/{portfolio_id}", response_model=dict)
async def get_portfolio_risk_metrics(
    portfolio_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    try:
        metrics = await RiskService(db).calculate_risk_metrics(
            portfolio_id=portfolio_id, user_id=current_user.id
        )
    except (HTTPException, BaseChainFinityException):
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio risk metrics: {e}")
        raise _internal("Failed to retrieve risk metrics")
    if metrics is None:
        raise _not_found("Portfolio not found")
    return {
        "portfolio_id": str(portfolio_id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "var_1d": str(metrics.var_1d),
            "var_5d": str(metrics.var_5d),
            "var_30d": str(metrics.var_30d),
            "expected_shortfall": str(metrics.expected_shortfall),
            "sharpe_ratio": str(metrics.sharpe_ratio),
            "sortino_ratio": str(metrics.sortino_ratio),
            "max_drawdown": str(metrics.max_drawdown),
            "beta": str(metrics.beta),
            "alpha": str(metrics.alpha),
            "volatility": str(metrics.volatility),
            "concentration_risk": str(metrics.concentration_risk),
            "liquidity_risk": str(metrics.liquidity_risk),
            "overall_risk_score": str(metrics.overall_risk_score),
            "risk_grade": metrics.risk_grade,
        },
        "correlation_matrix": metrics.correlation_matrix,
        "ai_insights": _to_jsonable(metrics.ai_insights),
        "data_points": metrics.data_points,
    }


@router.get("/monitor/{portfolio_id}", response_model=dict)
async def monitor_portfolio(
    portfolio_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    try:
        return await RiskService(db).monitor_portfolio_risk(
            portfolio_id, current_user.id
        )
    except (HTTPException, BaseChainFinityException):
        raise
    except ValueError:
        raise _not_found("Portfolio not found")
    except Exception as e:
        logger.error(f"Error monitoring portfolio risk: {e}")
        raise _internal("Failed to monitor portfolio risk")


@router.post("/stress-test/{portfolio_id}", response_model=dict)
async def stress_test_portfolio(
    portfolio_id: UUID,
    scenario: Optional[str] = Query("Market Crash"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    try:
        results = await RiskService(db).perform_stress_test(
            portfolio_id=portfolio_id, user_id=current_user.id, scenario_name=scenario
        )
    except (HTTPException, BaseChainFinityException):
        raise
    except Exception as e:
        logger.error(f"Error performing stress test: {e}")
        raise _internal("Failed to perform stress test")
    if not results.get("results"):
        raise _not_found("Portfolio not found")
    return {
        "portfolio_id": str(portfolio_id),
        "scenario": scenario,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }


def _serialize_rule(rule: AlertRule) -> Dict[str, Any]:
    return {
        "id": str(rule.id),
        "portfolio_id": str(rule.portfolio_id) if rule.portfolio_id else None,
        "rule_name": rule.rule_name,
        "rule_type": rule.rule_type or "unknown",
        "threshold_value": (
            str(rule.threshold_value) if rule.threshold_value is not None else "0"
        ),
        "is_active": rule.is_active,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
    }


@router.get("/alerts", response_model=List[dict])
async def list_risk_alerts(
    portfolio_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    try:
        query = select(AlertRule).where(AlertRule.user_id == current_user.id)
        if portfolio_id:
            query = query.where(AlertRule.portfolio_id == portfolio_id)
        query = query.order_by(desc(AlertRule.created_at)).limit(limit).offset(offset)
        result = await db.execute(query)
        return [_serialize_rule(r) for r in result.scalars().all()]
    except Exception as e:
        logger.error(f"Error listing risk alerts: {e}")
        raise _internal("Failed to retrieve risk alerts")


@router.post("/alerts", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_risk_alert(
    payload: AlertRuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    owned = await db.execute(
        select(Portfolio.id).where(
            and_(
                Portfolio.id == payload.portfolio_id,
                Portfolio.user_id == current_user.id,
                Portfolio.is_deleted == False,
            )
        )
    )
    if owned.scalar_one_or_none() is None:
        raise _not_found("Portfolio not found")
    requested = payload.rule_type.strip().upper()
    rule_type = (
        AlertType[requested] if requested in AlertType.__members__ else AlertType.CUSTOM
    )
    try:
        rule = AlertRule(
            user_id=current_user.id,
            portfolio_id=payload.portfolio_id,
            rule_name=payload.rule_name,
            rule_type=rule_type.value,
            threshold_value=payload.threshold_value,
            is_active=True,
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return _serialize_rule(rule)
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating risk alert: {e}")
        raise _internal("Failed to create risk alert")

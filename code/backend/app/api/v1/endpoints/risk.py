"""
Risk management endpoints
"""

import logging
from datetime import datetime, timezone
from typing import Any, List, Optional
from uuid import UUID

from app.api.dependencies import get_current_user
from config.database import get_async_session
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.risk import AlertRule, RiskAssessment
from models.user import User
from schemas.risk import RiskAssessmentResponse
from services.risk.risk_service import RiskService
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/assessments", response_model=List[RiskAssessmentResponse])
async def list_risk_assessments(
    portfolio_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get risk assessments for user's portfolios
    """
    try:
        query = select(RiskAssessment).where(RiskAssessment.user_id == current_user.id)

        if portfolio_id:
            query = query.where(RiskAssessment.portfolio_id == portfolio_id)

        query = (
            query.order_by(desc(RiskAssessment.created_at)).limit(limit).offset(offset)
        )

        result = await db.execute(query)
        assessments = result.scalars().all()

        return assessments

    except Exception as e:
        logger.error(f"Error listing risk assessments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve risk assessments",
        )


@router.get("/assessments/{assessment_id}", response_model=RiskAssessmentResponse)
async def get_risk_assessment(
    assessment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get specific risk assessment
    """
    try:
        query = select(RiskAssessment).where(
            and_(
                RiskAssessment.id == assessment_id,
                RiskAssessment.user_id == current_user.id,
            )
        )
        result = await db.execute(query)
        assessment = result.scalar_one_or_none()

        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Risk assessment not found",
            )

        return assessment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve risk assessment",
        )


@router.post("/assess/{portfolio_id}", response_model=RiskAssessmentResponse)
async def assess_portfolio_risk(
    portfolio_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Perform risk assessment on a portfolio
    """
    try:
        risk_service = RiskService(db)

        assessment = await risk_service.assess_portfolio_risk(
            portfolio_id=portfolio_id, user_id=current_user.id
        )

        return assessment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assessing portfolio risk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assess portfolio risk",
        )


@router.get("/metrics/{portfolio_id}", response_model=dict)
async def get_portfolio_risk_metrics(
    portfolio_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get detailed risk metrics for a portfolio
    """
    try:
        risk_service = RiskService(db)

        metrics = await risk_service.calculate_risk_metrics(
            portfolio_id=portfolio_id, user_id=current_user.id
        )

        return {
            "portfolio_id": str(portfolio_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {
                "var_1d": str(metrics.var_1d) if metrics else "0",
                "var_5d": str(metrics.var_5d) if metrics else "0",
                "var_30d": str(metrics.var_30d) if metrics else "0",
                "sharpe_ratio": str(metrics.sharpe_ratio) if metrics else "0",
                "sortino_ratio": str(metrics.sortino_ratio) if metrics else "0",
                "max_drawdown": str(metrics.max_drawdown) if metrics else "0",
                "volatility": str(metrics.volatility) if metrics else "0",
                "overall_risk_score": (
                    str(metrics.overall_risk_score) if metrics else "0"
                ),
                "risk_grade": metrics.risk_grade if metrics else "N/A",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio risk metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve risk metrics",
        )


@router.post("/stress-test/{portfolio_id}", response_model=dict)
async def stress_test_portfolio(
    portfolio_id: UUID,
    scenario: Optional[str] = Query("Market Crash"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Perform stress test on portfolio
    """
    try:
        risk_service = RiskService(db)

        results = await risk_service.perform_stress_test(
            portfolio_id=portfolio_id, user_id=current_user.id, scenario_name=scenario
        )

        return {
            "portfolio_id": str(portfolio_id),
            "scenario": scenario,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing stress test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform stress test",
        )


@router.get("/alerts", response_model=List[dict])
async def list_risk_alerts(
    portfolio_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get risk alerts for user
    """
    try:
        query = select(AlertRule).where(AlertRule.user_id == current_user.id)

        if portfolio_id:
            query = query.where(AlertRule.portfolio_id == portfolio_id)

        query = query.order_by(desc(AlertRule.created_at)).limit(limit).offset(offset)

        result = await db.execute(query)
        alerts = result.scalars().all()

        return [
            {
                "id": str(alert.id),
                "rule_name": alert.rule_name,
                "rule_type": alert.rule_type.value if alert.rule_type else "unknown",
                "threshold_value": (
                    str(alert.threshold_value) if alert.threshold_value else "0"
                ),
                "is_active": alert.is_active,
                "created_at": (
                    alert.created_at.isoformat() if alert.created_at else None
                ),
            }
            for alert in alerts
        ]

    except Exception as e:
        logger.error(f"Error listing risk alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve risk alerts",
        )


@router.post("/alerts", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_risk_alert(
    portfolio_id: UUID,
    rule_name: str,
    rule_type: str,
    threshold_value: float,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Create a new risk alert rule
    """
    try:
        from models.risk import AlertType

        alert = AlertRule(
            user_id=current_user.id,
            portfolio_id=portfolio_id,
            rule_name=rule_name,
            rule_type=(
                AlertType[rule_type.upper()]
                if hasattr(AlertType, rule_type.upper())
                else AlertType.CUSTOM
            ),
            threshold_value=threshold_value,
            is_active=True,
        )

        db.add(alert)
        await db.commit()
        await db.refresh(alert)

        return {
            "id": str(alert.id),
            "rule_name": alert.rule_name,
            "rule_type": alert.rule_type.value,
            "threshold_value": str(alert.threshold_value),
            "is_active": alert.is_active,
            "created_at": alert.created_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error creating risk alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create risk alert",
        )

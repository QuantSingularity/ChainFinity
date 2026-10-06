from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field
from schemas.base import BaseSchema


class RiskAssessmentResponse(BaseSchema):
    id: UUID
    portfolio_id: Optional[UUID] = None
    risk_score: Decimal
    risk_level: str
    risk_grade: Optional[str] = None
    assessment_type: Optional[str] = None
    assessment_method: Optional[str] = None
    model_version: Optional[str] = None
    assessment_date: datetime
    valid_until: Optional[datetime] = None
    created_at: datetime
    action_required: bool = False
    market_risk_score: Optional[Decimal] = None
    credit_risk_score: Optional[Decimal] = None
    liquidity_risk_score: Optional[Decimal] = None
    operational_risk_score: Optional[Decimal] = None
    recommendations: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    correlation_matrix: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    stress_tests: List[Dict[str, Any]] = Field(default_factory=list)
    ai_insights: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_orm_assessment(cls, assessment: Any) -> "RiskAssessmentResponse":
        results = assessment.assessment_results or {}
        level = getattr(assessment.risk_level, "value", assessment.risk_level)
        return cls(
            id=assessment.id,
            portfolio_id=assessment.portfolio_id,
            risk_score=assessment.overall_risk_score,
            risk_level=str(level),
            risk_grade=results.get("risk_grade"),
            assessment_type=assessment.assessment_type,
            assessment_method=assessment.assessment_method,
            model_version=assessment.model_version,
            assessment_date=assessment.valid_from or assessment.created_at,
            valid_until=assessment.valid_until,
            created_at=assessment.created_at,
            action_required=bool(assessment.action_required),
            market_risk_score=assessment.market_risk_score,
            credit_risk_score=assessment.credit_risk_score,
            liquidity_risk_score=assessment.liquidity_risk_score,
            operational_risk_score=assessment.operational_risk_score,
            recommendations=list(assessment.recommendations or []),
            metrics=results.get("metrics", {}),
            correlation_matrix=results.get("correlation_matrix", {}),
            stress_tests=results.get("stress_tests", []),
            ai_insights=results.get("ai_insights", {}),
        )


class RiskMetricsResponse(BaseSchema):
    id: UUID
    metric_type: str
    value: Decimal
    created_at: datetime


class AlertResponse(BaseSchema):
    id: UUID
    alert_type: str
    severity: str
    message: str
    is_active: bool
    created_at: datetime


class AlertRuleCreate(BaseSchema):
    portfolio_id: UUID
    rule_name: str = Field(min_length=1, max_length=100)
    rule_type: str = Field(default="custom", max_length=50)
    threshold_value: float
    model_config = {**BaseSchema.model_config, "extra": "forbid"}

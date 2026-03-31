"""
Risk management database models
Risk assessment, monitoring, and alerting
"""

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import AuditMixin, BaseModel, TimestampMixin


class RiskType(enum.Enum):
    """Risk type enumeration"""

    MARKET_RISK = "market_risk"
    CREDIT_RISK = "credit_risk"
    LIQUIDITY_RISK = "liquidity_risk"
    OPERATIONAL_RISK = "operational_risk"
    COMPLIANCE_RISK = "compliance_risk"
    CONCENTRATION_RISK = "concentration_risk"
    COUNTERPARTY_RISK = "counterparty_risk"
    SMART_CONTRACT_RISK = "smart_contract_risk"


class RiskLevel(enum.Enum):
    """Risk level enumeration"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertSeverity(enum.Enum):
    """Alert severity enumeration"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(enum.Enum):
    """Alert status enumeration"""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class RiskAssessment(BaseModel, TimestampMixin, AuditMixin):
    """
    Risk assessments for users, portfolios, and transactions
    """

    __tablename__ = "risk_assessments"

    # Assessment Subject
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    portfolio_id = Column(
        UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=True, index=True
    )
    transaction_id = Column(
        UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True, index=True
    )

    # Assessment Details
    assessment_type = Column(String(50), nullable=False, index=True)
    risk_type = Column(Enum(RiskType), nullable=False, index=True)
    risk_level = Column(Enum(RiskLevel), nullable=False, index=True)

    # Risk Scores
    overall_risk_score = Column(Numeric(5, 2), nullable=False)  # 0-100
    market_risk_score = Column(Numeric(5, 2), nullable=True)
    credit_risk_score = Column(Numeric(5, 2), nullable=True)
    liquidity_risk_score = Column(Numeric(5, 2), nullable=True)
    operational_risk_score = Column(Numeric(5, 2), nullable=True)

    # Assessment Method
    assessment_method = Column(String(50), nullable=False)  # manual, automated, hybrid
    model_version = Column(String(20), nullable=True)

    # Assessment Data
    risk_factors = Column(JSON, nullable=False)
    assessment_parameters = Column(JSON, nullable=True)
    assessment_results = Column(JSON, nullable=False)

    # Validity
    valid_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_until = Column(DateTime, nullable=True, index=True)
    is_current = Column(Boolean, default=True, nullable=False, index=True)

    # Review Information
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    # Recommendations
    recommendations = Column(JSON, nullable=True)
    action_required = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User")
    portfolio = relationship("Portfolio")
    transaction = relationship("Transaction")

    # Indexes
    __table_args__ = (
        Index("idx_risk_user_type", "user_id", "risk_type"),
        Index("idx_risk_level_current", "risk_level", "is_current"),
        Index("idx_risk_validity", "valid_from", "valid_until"),
        Index("idx_risk_score", "overall_risk_score"),
    )

    def is_valid(self) -> bool:
        """Check if risk assessment is still valid"""
        return self.is_current and (
            self.valid_until is None or self.valid_until > datetime.utcnow()
        )

    def is_high_risk(self) -> bool:
        """Check if assessment indicates high risk"""
        return self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

    def expire(self) -> None:
        """Mark assessment as expired"""
        self.is_current = False
        self.valid_until = datetime.utcnow()


class RiskMetrics(BaseModel, TimestampMixin):
    """
    Risk metrics and calculations
    """

    __tablename__ = "risk_metrics"

    # Metric Subject
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    portfolio_id = Column(
        UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=True, index=True
    )

    # Metric Details
    metric_name = Column(String(100), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)
    metric_category = Column(String(50), nullable=False, index=True)

    # Metric Values
    value = Column(Numeric(20, 8), nullable=False)
    normalized_value = Column(Numeric(5, 2), nullable=True)  # 0-100 normalized score

    # Calculation Details
    calculation_method = Column(String(100), nullable=False)
    calculation_parameters = Column(JSON, nullable=True)
    data_points_used = Column(Integer, nullable=True)

    # Time Period
    period_start = Column(DateTime, nullable=True, index=True)
    period_end = Column(DateTime, nullable=True, index=True)
    calculation_date = Column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Benchmarks and Thresholds
    benchmark_value = Column(Numeric(20, 8), nullable=True)
    warning_threshold = Column(Numeric(20, 8), nullable=True)
    critical_threshold = Column(Numeric(20, 8), nullable=True)

    # Status
    is_current = Column(Boolean, default=True, nullable=False, index=True)
    threshold_breached = Column(Boolean, default=False, nullable=False, index=True)

    # Metadata
    extra_metadata = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User")
    portfolio = relationship("Portfolio")

    # Indexes
    __table_args__ = (
        Index("idx_metrics_user_metric", "user_id", "metric_name"),
        Index("idx_metrics_portfolio_metric", "portfolio_id", "metric_name"),
        Index("idx_metrics_calculation_date", "calculation_date", "is_current"),
        Index("idx_metrics_threshold_breach", "threshold_breached", "metric_type"),
    )

    def check_thresholds(self) -> bool:
        """Check if metric value breaches thresholds"""
        if self.critical_threshold and self.value >= self.critical_threshold:
            self.threshold_breached = True
            return True
        elif self.warning_threshold and self.value >= self.warning_threshold:
            self.threshold_breached = True
            return True

        self.threshold_breached = False
        return False

    def get_risk_level(self) -> RiskLevel:
        """Get risk level based on thresholds"""
        if self.critical_threshold and self.value >= self.critical_threshold:
            return RiskLevel.CRITICAL
        elif self.warning_threshold and self.value >= self.warning_threshold:
            return RiskLevel.HIGH
        elif self.normalized_value and self.normalized_value > 70:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW


class AlertRule(BaseModel, TimestampMixin, AuditMixin):
    """
    Configurable alert rules for risk monitoring
    """

    __tablename__ = "alert_rules"

    # Rule Details
    rule_name = Column(String(100), unique=True, nullable=False, index=True)
    rule_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Rule Configuration
    conditions = Column(JSON, nullable=False)
    thresholds = Column(JSON, nullable=False)
    parameters = Column(JSON, nullable=True)

    # Alert Settings
    severity = Column(
        Enum(AlertSeverity), default=AlertSeverity.WARNING, nullable=False
    )
    notification_channels = Column(JSON, nullable=True)  # email, sms, webhook, etc.

    # Execution
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    execution_frequency = Column(String(20), default="realtime", nullable=False)
    last_executed = Column(DateTime, nullable=True)
    next_execution = Column(DateTime, nullable=True)

    # Statistics
    total_executions = Column(Integer, default=0, nullable=False)
    total_alerts_generated = Column(Integer, default=0, nullable=False)
    false_positive_count = Column(Integer, default=0, nullable=False)

    # Metadata
    tags = Column(JSON, nullable=True)
    extra_metadata = Column(JSON, nullable=True)

    def is_due_for_execution(self) -> bool:
        """Check if rule is due for execution"""
        return self.is_active and (
            self.next_execution is None or self.next_execution <= datetime.utcnow()
        )

    def record_execution(self, alerts_generated: int = 0) -> None:
        """Record rule execution"""
        self.last_executed = datetime.utcnow()
        self.total_executions += 1
        self.total_alerts_generated += alerts_generated

    def calculate_false_positive_rate(self) -> float:
        """Calculate false positive rate"""
        if self.total_alerts_generated == 0:
            return 0.0
        return (self.false_positive_count / self.total_alerts_generated) * 100


class RiskAlert(BaseModel, TimestampMixin, AuditMixin):
    """
    Risk alerts generated by monitoring rules
    """

    __tablename__ = "risk_alerts"

    # Alert Source
    alert_rule_id = Column(
        UUID(as_uuid=True), ForeignKey("alert_rules.id"), nullable=False, index=True
    )

    # Alert Subject
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    portfolio_id = Column(
        UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=True, index=True
    )
    transaction_id = Column(
        UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True, index=True
    )

    # Alert Details
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(Enum(AlertSeverity), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    # Alert Data
    trigger_conditions = Column(JSON, nullable=False)
    alert_data = Column(JSON, nullable=False)
    risk_score = Column(Numeric(5, 2), nullable=True)

    # Status and Resolution
    status = Column(
        Enum(AlertStatus), default=AlertStatus.OPEN, nullable=False, index=True
    )
    assigned_to = Column(UUID(as_uuid=True), nullable=True, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Escalation
    escalation_level = Column(Integer, default=0, nullable=False)
    escalated_at = Column(DateTime, nullable=True)
    escalation_reason = Column(Text, nullable=True)

    # Notification
    notifications_sent = Column(JSON, nullable=True)
    last_notification_sent = Column(DateTime, nullable=True)

    # Relationships
    alert_rule = relationship("AlertRule")
    user = relationship("User")
    portfolio = relationship("Portfolio")
    transaction = relationship("Transaction")

    # Indexes
    __table_args__ = (
        Index("idx_alert_rule_status", "alert_rule_id", "status"),
        Index("idx_alert_user_severity", "user_id", "severity"),
        Index("idx_alert_created_status", "created_at", "status"),
        Index("idx_alert_assigned_status", "assigned_to", "status"),
    )

    def is_open(self) -> bool:
        """Check if alert is still open"""
        return self.status in [
            AlertStatus.OPEN,
            AlertStatus.ACKNOWLEDGED,
            AlertStatus.INVESTIGATING,
        ]

    def acknowledge(self, acknowledged_by: str) -> None:
        """Acknowledge the alert"""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()
        self.assigned_to = acknowledged_by

    def resolve(
        self, resolved_by: str, notes: str = None, is_false_positive: bool = False
    ) -> None:
        """Resolve the alert"""
        self.status = (
            AlertStatus.FALSE_POSITIVE if is_false_positive else AlertStatus.RESOLVED
        )
        self.resolved_at = datetime.utcnow()
        self.updated_by = resolved_by
        if notes:
            self.resolution_notes = notes

    def escalate(self, reason: str = None) -> None:
        """Escalate the alert"""
        self.escalation_level += 1
        self.escalated_at = datetime.utcnow()
        if reason:
            self.escalation_reason = reason


class RiskLimit(BaseModel, TimestampMixin, AuditMixin):
    """
    Risk limits and position limits
    """

    __tablename__ = "risk_limits"

    # Limit Subject
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    portfolio_id = Column(
        UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=True, index=True
    )

    # Limit Details
    limit_type = Column(String(50), nullable=False, index=True)
    limit_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Limit Values
    limit_value = Column(Numeric(20, 8), nullable=False)
    current_value = Column(Numeric(20, 8), default=0, nullable=False)
    utilization_percentage = Column(Numeric(5, 2), default=0, nullable=False)

    # Thresholds
    warning_threshold = Column(Numeric(5, 2), default=80, nullable=False)  # 80%
    breach_threshold = Column(Numeric(5, 2), default=100, nullable=False)  # 100%

    # Time Period
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly, absolute
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_breached = Column(Boolean, default=False, nullable=False, index=True)
    breach_count = Column(Integer, default=0, nullable=False)
    last_breach_date = Column(DateTime, nullable=True)

    # Actions
    breach_actions = Column(JSON, nullable=True)  # Actions to take on breach
    auto_enforce = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User")
    portfolio = relationship("Portfolio")

    # Indexes
    __table_args__ = (
        Index("idx_limit_user_type", "user_id", "limit_type"),
        Index("idx_limit_portfolio_type", "portfolio_id", "limit_type"),
        Index("idx_limit_breach_status", "is_breached", "is_active"),
        Index("idx_limit_utilization", "utilization_percentage"),
    )

    def update_utilization(self, current_value: float) -> None:
        """Update current utilization"""
        self.current_value = current_value
        if self.limit_value > 0:
            self.utilization_percentage = (current_value / self.limit_value) * 100

        # Check for breach
        if self.utilization_percentage >= self.breach_threshold:
            if not self.is_breached:
                self.is_breached = True
                self.breach_count += 1
                self.last_breach_date = datetime.utcnow()
        else:
            self.is_breached = False

    def is_warning_level(self) -> bool:
        """Check if utilization is at warning level"""
        return self.utilization_percentage >= self.warning_threshold

    def get_available_limit(self) -> float:
        """Get available limit amount"""
        return max(0, float(self.limit_value - self.current_value))

"""
Compliance and regulatory database models
AML, audit trails, and regulatory reporting
"""

import enum
from datetime import datetime
from typing import Any

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


class AuditEventType(enum.Enum):
    """Audit event type enumeration"""

    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTRATION = "user_registration"
    USER_UPDATE = "user_update"
    PASSWORD_CHANGE = "password_change"
    TRANSACTION_CREATE = "transaction_create"
    TRANSACTION_UPDATE = "transaction_update"
    PORTFOLIO_CREATE = "portfolio_create"
    PORTFOLIO_UPDATE = "portfolio_update"
    KYC_SUBMISSION = "kyc_submission"
    KYC_APPROVAL = "kyc_approval"
    KYC_REJECTION = "kyc_rejection"
    COMPLIANCE_CHECK = "compliance_check"
    RISK_ASSESSMENT = "risk_assessment"
    ALERT_GENERATED = "alert_generated"
    ALERT_RESOLVED = "alert_resolved"
    ADMIN_ACTION = "admin_action"
    SYSTEM_EVENT = "system_event"


class ComplianceStatus(enum.Enum):
    """Compliance check status"""

    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"
    EXEMPTED = "exempted"


class ReportType(enum.Enum):
    """Regulatory report type"""

    SAR = "sar"  # Suspicious Activity Report
    CTR = "ctr"  # Currency Transaction Report
    FBAR = "fbar"  # Foreign Bank Account Report
    FATCA = "fatca"  # Foreign Account Tax Compliance Act
    CRS = "crs"  # Common Reporting Standard
    CUSTOM = "custom"


class ReportStatus(enum.Enum):
    """Report status enumeration"""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    REJECTED = "rejected"


class AuditLog(BaseModel, TimestampMixin):
    """
    Comprehensive audit log for all system activities
    """

    __tablename__ = "audit_logs"

    # Event Details
    event_type = Column(Enum(AuditEventType), nullable=False, index=True)
    event_name = Column(String(100), nullable=False, index=True)
    event_description = Column(Text, nullable=True)

    # User and Session
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    session_id = Column(String(255), nullable=True, index=True)

    # Request Details
    ip_address = Column(String(45), nullable=True, index=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    request_method = Column(String(10), nullable=True)
    request_url = Column(Text, nullable=True)
    request_headers = Column(JSON, nullable=True)

    # Response Details
    response_status = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    # Entity Information
    entity_type = Column(String(50), nullable=True, index=True)
    entity_id = Column(String(255), nullable=True, index=True)

    # Change Details
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    changes = Column(JSON, nullable=True)

    # Risk and Compliance
    risk_score = Column(Numeric(5, 2), nullable=True)
    is_suspicious = Column(Boolean, default=False, nullable=False, index=True)
    compliance_flags = Column(JSON, nullable=True)

    # Additional Context
    extra_metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    # Indexes
    __table_args__ = (
        Index("idx_audit_user_event", "user_id", "event_type"),
        Index("idx_audit_timestamp_event", "created_at", "event_type"),
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_ip_timestamp", "ip_address", "created_at"),
        Index("idx_audit_suspicious", "is_suspicious", "created_at"),
    )

    def add_change(self, field: str, old_value: Any, new_value: Any) -> None:
        """Add a field change to the audit log"""
        if self.changes is None:
            self.changes = {}
        self.changes[field] = {
            "old": old_value,
            "new": new_value,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the audit log"""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value


class ComplianceCheck(BaseModel, TimestampMixin, AuditMixin):
    """
    Compliance checks and their results
    """

    __tablename__ = "compliance_checks"

    # Check Details
    check_type = Column(String(50), nullable=False, index=True)
    check_name = Column(String(100), nullable=False)
    check_description = Column(Text, nullable=True)

    # Subject of Check
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    transaction_id = Column(
        UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True, index=True
    )
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(255), nullable=True)

    # Check Results
    status = Column(Enum(ComplianceStatus), nullable=False, index=True)
    score = Column(Numeric(5, 2), nullable=True)  # 0-100 compliance score

    # Check Data
    check_parameters = Column(JSON, nullable=True)
    check_results = Column(JSON, nullable=False)
    evidence = Column(JSON, nullable=True)

    # Review Information
    requires_manual_review = Column(Boolean, default=False, nullable=False, index=True)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    # Expiry and Validity
    valid_until = Column(DateTime, nullable=True, index=True)
    is_expired = Column(Boolean, default=False, nullable=False)

    # External References
    external_reference_id = Column(String(255), nullable=True)
    provider = Column(String(50), nullable=True)

    # Relationships
    user = relationship("User")
    transaction = relationship("Transaction")

    # Indexes
    __table_args__ = (
        Index("idx_compliance_user_type", "user_id", "check_type"),
        Index("idx_compliance_status_review", "status", "requires_manual_review"),
        Index("idx_compliance_expiry", "valid_until", "is_expired"),
    )

    def is_valid(self) -> bool:
        """Check if compliance check is still valid"""
        return (
            not self.is_expired
            and (self.valid_until is None or self.valid_until > datetime.utcnow())
            and self.status in [ComplianceStatus.PASSED, ComplianceStatus.EXEMPTED]
        )

    def mark_expired(self) -> None:
        """Mark compliance check as expired"""
        self.is_expired = True

    def approve_review(self, reviewer_id: str, notes: str = None) -> None:
        """Approve manual review"""
        self.status = ComplianceStatus.PASSED
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.utcnow()
        if notes:
            self.review_notes = notes

    def reject_review(self, reviewer_id: str, notes: str = None) -> None:
        """Reject manual review"""
        self.status = ComplianceStatus.FAILED
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.utcnow()
        if notes:
            self.review_notes = notes


class RegulatoryReport(BaseModel, TimestampMixin, AuditMixin):
    """
    Regulatory reports and filings
    """

    __tablename__ = "regulatory_reports"

    # Report Details
    report_type = Column(Enum(ReportType), nullable=False, index=True)
    report_name = Column(String(100), nullable=False)
    report_description = Column(Text, nullable=True)

    # Reporting Period
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)

    # Status and Workflow
    status = Column(
        Enum(ReportStatus), default=ReportStatus.DRAFT, nullable=False, index=True
    )

    # Report Content
    report_data = Column(JSON, nullable=False)
    summary_statistics = Column(JSON, nullable=True)

    # Generation Details
    generated_by = Column(UUID(as_uuid=True), nullable=True)
    generated_at = Column(DateTime, nullable=True)
    generation_parameters = Column(JSON, nullable=True)

    # Review and Approval
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approval_notes = Column(Text, nullable=True)

    # Submission Details
    submitted_by = Column(UUID(as_uuid=True), nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    submission_reference = Column(String(255), nullable=True)
    submission_response = Column(JSON, nullable=True)

    # File Information
    file_path = Column(String(500), nullable=True)
    file_hash = Column(String(64), nullable=True)  # SHA-256 hash
    file_size = Column(Integer, nullable=True)

    # Regulatory Authority
    regulatory_authority = Column(String(100), nullable=True)
    jurisdiction = Column(String(50), nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_report_type_period", "report_type", "period_start", "period_end"),
        Index("idx_report_status_type", "status", "report_type"),
        Index("idx_report_submission", "submitted_at", "submission_reference"),
    )

    def can_be_submitted(self) -> bool:
        """Check if report can be submitted"""
        return self.status == ReportStatus.APPROVED

    def submit_report(self, submitted_by: str, reference: str = None) -> None:
        """Mark report as submitted"""
        self.status = ReportStatus.SUBMITTED
        self.submitted_by = submitted_by
        self.submitted_at = datetime.utcnow()
        if reference:
            self.submission_reference = reference


class SuspiciousActivityReport(BaseModel, TimestampMixin, AuditMixin):
    """
    Suspicious Activity Reports (SARs)
    """

    __tablename__ = "suspicious_activity_reports"

    # Report Identification
    sar_number = Column(String(50), unique=True, nullable=False, index=True)

    # Subject Information
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    transaction_ids = Column(JSON, nullable=True)  # List of related transaction IDs

    # Suspicious Activity Details
    activity_type = Column(String(100), nullable=False, index=True)
    activity_description = Column(Text, nullable=False)
    suspicious_indicators = Column(JSON, nullable=False)

    # Financial Information
    total_amount = Column(Numeric(20, 8), nullable=True)
    currency = Column(String(3), nullable=True)

    # Timeline
    activity_start_date = Column(DateTime, nullable=False, index=True)
    activity_end_date = Column(DateTime, nullable=True)
    detection_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Filing Information
    filing_required = Column(Boolean, default=True, nullable=False)
    filing_deadline = Column(DateTime, nullable=True)
    filed_at = Column(DateTime, nullable=True)
    filing_reference = Column(String(255), nullable=True)

    # Investigation
    investigated_by = Column(UUID(as_uuid=True), nullable=True)
    investigation_notes = Column(Text, nullable=True)
    investigation_completed = Column(Boolean, default=False, nullable=False)

    # Status
    status = Column(String(20), default="open", nullable=False, index=True)
    resolution = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User")

    # Indexes
    __table_args__ = (
        Index("idx_sar_user_activity", "user_id", "activity_type"),
        Index("idx_sar_detection_filing", "detection_date", "filing_deadline"),
        Index("idx_sar_status_amount", "status", "total_amount"),
    )

    def is_filing_overdue(self) -> bool:
        """Check if SAR filing is overdue"""
        return (
            self.filing_required
            and not self.filed_at
            and self.filing_deadline
            and self.filing_deadline < datetime.utcnow()
        )

    def file_report(self, reference: str = None) -> None:
        """Mark SAR as filed"""
        self.filed_at = datetime.utcnow()
        if reference:
            self.filing_reference = reference


class ComplianceRule(BaseModel, TimestampMixin, AuditMixin):
    """
    Configurable compliance rules and thresholds
    """

    __tablename__ = "compliance_rules"

    # Rule Details
    rule_name = Column(String(100), unique=True, nullable=False, index=True)
    rule_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Rule Configuration
    rule_parameters = Column(JSON, nullable=False)
    thresholds = Column(JSON, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    severity = Column(String(20), default="medium", nullable=False)

    # Execution
    execution_frequency = Column(String(20), default="realtime", nullable=False)
    last_executed = Column(DateTime, nullable=True)
    next_execution = Column(DateTime, nullable=True)

    # Metadata
    tags = Column(JSON, nullable=True)
    extra_metadata = Column(JSON, nullable=True)

    def is_due_for_execution(self) -> bool:
        """Check if rule is due for execution"""
        return (
            self.is_active
            and self.next_execution
            and self.next_execution <= datetime.utcnow()
        )

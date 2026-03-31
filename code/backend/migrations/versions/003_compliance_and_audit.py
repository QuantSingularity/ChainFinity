from typing import Any

"""Compliance and audit tables

Revision ID: 003
Revises: 002
Create Date: 2025-01-08 12:00:00.000000

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> Any:
    op.create_table(
        "audit_logs",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("session_id", sa.String(255), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("old_values", sa.JSON(), nullable=True),
        sa.Column("new_values", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(255), nullable=True),
        sa.Column("endpoint", sa.String(500), nullable=True),
        sa.Column("method", sa.String(10), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "severity",
            sa.Enum("low", "medium", "high", "critical", name="severitylevel"),
            nullable=False,
            default="low",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
    )
    op.create_index("idx_audit_log_user_id", "audit_logs", ["user_id"])
    op.create_index("idx_audit_log_action", "audit_logs", ["action"])
    op.create_index(
        "idx_audit_log_resource", "audit_logs", ["resource_type", "resource_id"]
    )
    op.create_index("idx_audit_log_created", "audit_logs", ["created_at"])
    op.create_index("idx_audit_log_severity", "audit_logs", ["severity"])
    op.create_index("idx_audit_log_session", "audit_logs", ["session_id"])
    op.create_table(
        "compliance_checks",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "transaction_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("transactions.id"),
            nullable=True,
        ),
        sa.Column(
            "check_type",
            sa.Enum(
                "kyc",
                "aml",
                "sanctions",
                "pep",
                "transaction_monitoring",
                "risk_assessment",
                name="compliancechecktype",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "in_progress",
                "passed",
                "failed",
                "manual_review",
                name="compliancecheckstatus",
            ),
            nullable=False,
            default="pending",
        ),
        sa.Column("provider", sa.String(100), nullable=True),
        sa.Column("provider_reference_id", sa.String(255), nullable=True),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "risk_level",
            sa.Enum("low", "medium", "high", "critical", name="risklevel"),
            nullable=True,
        ),
        sa.Column("findings", sa.JSON(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column("checked_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("idx_compliance_check_user_id", "compliance_checks", ["user_id"])
    op.create_index(
        "idx_compliance_check_transaction_id", "compliance_checks", ["transaction_id"]
    )
    op.create_index("idx_compliance_check_type", "compliance_checks", ["check_type"])
    op.create_index("idx_compliance_check_status", "compliance_checks", ["status"])
    op.create_index(
        "idx_compliance_check_risk_level", "compliance_checks", ["risk_level"]
    )
    op.create_index("idx_compliance_check_created", "compliance_checks", ["created_at"])
    op.create_table(
        "suspicious_activities",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "transaction_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("transactions.id"),
            nullable=True,
        ),
        sa.Column(
            "activity_type",
            sa.Enum(
                "unusual_volume",
                "rapid_transactions",
                "high_risk_address",
                "sanctions_match",
                "pattern_anomaly",
                "velocity_check",
                name="suspiciousactivitytype",
            ),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.Enum("low", "medium", "high", "critical", name="severitylevel"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "open",
                "investigating",
                "resolved",
                "false_positive",
                "escalated",
                name="suspiciousactivitystatus",
            ),
            nullable=False,
            default="open",
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("indicators", sa.JSON(), nullable=True),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("amount_usd", sa.Numeric(20, 8), nullable=True),
        sa.Column("frequency_count", sa.Integer(), nullable=True),
        sa.Column("time_window_hours", sa.Integer(), nullable=True),
        sa.Column("detected_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=True),
        sa.Column("investigated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("investigated_at", sa.DateTime(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("sar_filed", sa.Boolean(), nullable=False, default=False),
        sa.Column("sar_filed_at", sa.DateTime(), nullable=True),
        sa.Column("sar_reference", sa.String(255), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_suspicious_activity_user_id", "suspicious_activities", ["user_id"]
    )
    op.create_index(
        "idx_suspicious_activity_transaction_id",
        "suspicious_activities",
        ["transaction_id"],
    )
    op.create_index(
        "idx_suspicious_activity_type", "suspicious_activities", ["activity_type"]
    )
    op.create_index(
        "idx_suspicious_activity_severity", "suspicious_activities", ["severity"]
    )
    op.create_index(
        "idx_suspicious_activity_status", "suspicious_activities", ["status"]
    )
    op.create_index(
        "idx_suspicious_activity_detected", "suspicious_activities", ["detected_at"]
    )
    op.create_index(
        "idx_suspicious_activity_assigned", "suspicious_activities", ["assigned_to"]
    )
    op.create_table(
        "regulatory_reports",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column(
            "report_type",
            sa.Enum(
                "sar",
                "ctr",
                "fbar",
                "form_8300",
                "suspicious_activity",
                "transaction_summary",
                name="regulatoryreporttype",
            ),
            nullable=False,
        ),
        sa.Column("report_period_start", sa.DateTime(), nullable=False),
        sa.Column("report_period_end", sa.DateTime(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "pending_review",
                "approved",
                "submitted",
                "rejected",
                name="regulatoryreportstatus",
            ),
            nullable=False,
            default="draft",
        ),
        sa.Column("jurisdiction", sa.String(10), nullable=False),
        sa.Column("regulatory_body", sa.String(100), nullable=False),
        sa.Column("reference_number", sa.String(255), nullable=True),
        sa.Column("submission_deadline", sa.DateTime(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("file_hash", sa.String(64), nullable=True),
        sa.Column("record_count", sa.Integer(), nullable=True),
        sa.Column("total_amount_usd", sa.Numeric(20, 8), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("idx_regulatory_report_type", "regulatory_reports", ["report_type"])
    op.create_index("idx_regulatory_report_status", "regulatory_reports", ["status"])
    op.create_index(
        "idx_regulatory_report_period",
        "regulatory_reports",
        ["report_period_start", "report_period_end"],
    )
    op.create_index(
        "idx_regulatory_report_jurisdiction", "regulatory_reports", ["jurisdiction"]
    )
    op.create_index(
        "idx_regulatory_report_deadline", "regulatory_reports", ["submission_deadline"]
    )
    op.create_index(
        "idx_regulatory_report_created", "regulatory_reports", ["created_at"]
    )
    op.create_table(
        "risk_assessments",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "portfolio_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("portfolios.id"),
            nullable=True,
        ),
        sa.Column(
            "transaction_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("transactions.id"),
            nullable=True,
        ),
        sa.Column(
            "assessment_type",
            sa.Enum(
                "user_onboarding",
                "periodic_review",
                "transaction_based",
                "portfolio_analysis",
                "ad_hoc",
                name="riskassessmenttype",
            ),
            nullable=False,
        ),
        sa.Column(
            "risk_level",
            sa.Enum("low", "medium", "high", "critical", name="risklevel"),
            nullable=False,
        ),
        sa.Column("overall_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("credit_risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("market_risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("operational_risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("liquidity_risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("compliance_risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("concentration_risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("risk_factors", sa.JSON(), nullable=True),
        sa.Column("mitigation_measures", sa.JSON(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column("assessment_method", sa.String(100), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("confidence_level", sa.Numeric(5, 2), nullable=True),
        sa.Column("assessed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assessed_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("valid_until", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("idx_risk_assessment_user_id", "risk_assessments", ["user_id"])
    op.create_index(
        "idx_risk_assessment_portfolio_id", "risk_assessments", ["portfolio_id"]
    )
    op.create_index(
        "idx_risk_assessment_transaction_id", "risk_assessments", ["transaction_id"]
    )
    op.create_index("idx_risk_assessment_type", "risk_assessments", ["assessment_type"])
    op.create_index(
        "idx_risk_assessment_risk_level", "risk_assessments", ["risk_level"]
    )
    op.create_index("idx_risk_assessment_assessed", "risk_assessments", ["assessed_at"])
    op.create_index("idx_risk_assessment_valid", "risk_assessments", ["valid_until"])


def downgrade() -> Any:
    op.drop_table("risk_assessments")
    op.drop_table("regulatory_reports")
    op.drop_table("suspicious_activities")
    op.drop_table("compliance_checks")
    op.drop_table("audit_logs")
    op.execute("DROP TYPE IF EXISTS severitylevel")
    op.execute("DROP TYPE IF EXISTS compliancechecktype")
    op.execute("DROP TYPE IF EXISTS compliancecheckstatus")
    op.execute("DROP TYPE IF EXISTS suspiciousactivitytype")
    op.execute("DROP TYPE IF EXISTS suspiciousactivitystatus")
    op.execute("DROP TYPE IF EXISTS regulatoryreporttype")
    op.execute("DROP TYPE IF EXISTS regulatoryreportstatus")
    op.execute("DROP TYPE IF EXISTS riskassessmenttype")

from typing import Any

"""Initial schema migration

Revision ID: 001
Revises:
Create Date: 2025-01-08 12:00:00.000000

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> Any:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.create_table(
        "users",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("email_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("email_verified_at", sa.DateTime(), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "password_changed_at", sa.DateTime(), nullable=False, default=sa.func.now()
        ),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, default=0),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, default=False),
        sa.Column("mfa_secret", sa.String(255), nullable=True),
        sa.Column("backup_codes", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "active",
                "suspended",
                "deactivated",
                "banned",
                name="userstatus",
            ),
            nullable=False,
            default="pending",
        ),
        sa.Column("status_reason", sa.Text(), nullable=True),
        sa.Column(
            "status_changed_at", sa.DateTime(), nullable=False, default=sa.func.now()
        ),
        sa.Column("primary_wallet_address", sa.String(42), nullable=True),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(), nullable=True),
        sa.Column("login_count", sa.Integer(), nullable=False, default=0),
        sa.Column("terms_accepted_at", sa.DateTime(), nullable=True),
        sa.Column("privacy_accepted_at", sa.DateTime(), nullable=True),
        sa.Column("marketing_consent", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
    )
    op.create_index("idx_user_email", "users", ["email"])
    op.create_index("idx_user_email_status", "users", ["email", "status"])
    op.create_index(
        "idx_user_wallet_status", "users", ["primary_wallet_address", "status"]
    )
    op.create_index("idx_user_created_status", "users", ["created_at", "status"])
    op.create_index("idx_user_status", "users", ["status"])
    op.create_table(
        "user_profiles",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("middle_name", sa.String(100), nullable=True),
        sa.Column("date_of_birth", sa.DateTime(), nullable=True),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("phone_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("phone_verified_at", sa.DateTime(), nullable=True),
        sa.Column("address_line1", sa.String(255), nullable=True),
        sa.Column("address_line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state_province", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("country", sa.String(2), nullable=True),
        sa.Column("occupation", sa.String(100), nullable=True),
        sa.Column("employer", sa.String(255), nullable=True),
        sa.Column("annual_income_range", sa.String(50), nullable=True),
        sa.Column("net_worth_range", sa.String(50), nullable=True),
        sa.Column("investment_experience_years", sa.Integer(), nullable=True),
        sa.Column("crypto_experience_years", sa.Integer(), nullable=True),
        sa.Column(
            "risk_tolerance",
            sa.Enum("low", "medium", "high", "critical", name="risklevel"),
            nullable=True,
        ),
        sa.Column("preferred_language", sa.String(5), nullable=False, default="en"),
        sa.Column("preferred_currency", sa.String(3), nullable=False, default="USD"),
        sa.Column("timezone", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
    )
    op.create_index("idx_user_profile_user_id", "user_profiles", ["user_id"])
    op.create_table(
        "user_kyc",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "not_started",
                "in_progress",
                "pending_review",
                "approved",
                "rejected",
                "expired",
                name="kycstatus",
            ),
            nullable=False,
            default="not_started",
        ),
        sa.Column("status_reason", sa.Text(), nullable=True),
        sa.Column(
            "status_changed_at", sa.DateTime(), nullable=False, default=sa.func.now()
        ),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("provider_reference_id", sa.String(255), nullable=True),
        sa.Column("document_type", sa.String(50), nullable=True),
        sa.Column("document_number", sa.String(100), nullable=True),
        sa.Column("document_country", sa.String(2), nullable=True),
        sa.Column("document_expiry_date", sa.DateTime(), nullable=True),
        sa.Column("document_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("document_verified_at", sa.DateTime(), nullable=True),
        sa.Column("identity_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("identity_verified_at", sa.DateTime(), nullable=True),
        sa.Column("identity_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("address_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("address_verified_at", sa.DateTime(), nullable=True),
        sa.Column("biometric_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("biometric_verified_at", sa.DateTime(), nullable=True),
        sa.Column("sanctions_checked", sa.Boolean(), nullable=False, default=False),
        sa.Column("sanctions_checked_at", sa.DateTime(), nullable=True),
        sa.Column("sanctions_match", sa.Boolean(), nullable=False, default=False),
        sa.Column("pep_checked", sa.Boolean(), nullable=False, default=False),
        sa.Column("pep_checked_at", sa.DateTime(), nullable=True),
        sa.Column("pep_match", sa.Boolean(), nullable=False, default=False),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("renewal_required", sa.Boolean(), nullable=False, default=False),
        sa.Column("verification_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
    )
    op.create_index("idx_user_kyc_user_id", "user_kyc", ["user_id"])
    op.create_index("idx_user_kyc_status", "user_kyc", ["status"])
    op.create_table(
        "user_risk_profiles",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "risk_level",
            sa.Enum("low", "medium", "high", "critical", name="risklevel"),
            nullable=False,
            default="medium",
        ),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("risk_factors", sa.JSON(), nullable=True),
        sa.Column(
            "assessment_date", sa.DateTime(), nullable=False, default=sa.func.now()
        ),
        sa.Column("assessment_method", sa.String(50), nullable=True),
        sa.Column("assessed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("daily_transaction_limit", sa.Numeric(20, 8), nullable=True),
        sa.Column("monthly_transaction_limit", sa.Numeric(20, 8), nullable=True),
        sa.Column("max_position_size", sa.Numeric(20, 8), nullable=True),
        sa.Column("enhanced_monitoring", sa.Boolean(), nullable=False, default=False),
        sa.Column("monitoring_reason", sa.Text(), nullable=True),
        sa.Column("monitoring_start_date", sa.DateTime(), nullable=True),
        sa.Column("monitoring_end_date", sa.DateTime(), nullable=True),
        sa.Column("next_review_date", sa.DateTime(), nullable=True),
        sa.Column("review_frequency_days", sa.Integer(), nullable=False, default=365),
        sa.Column("volatility_tolerance", sa.Numeric(5, 2), nullable=True),
        sa.Column("max_drawdown_tolerance", sa.Numeric(5, 2), nullable=True),
        sa.Column("liquidity_requirement", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
    )
    op.create_index("idx_user_risk_profile_user_id", "user_risk_profiles", ["user_id"])
    op.create_index(
        "idx_user_risk_profile_risk_level", "user_risk_profiles", ["risk_level"]
    )


def downgrade() -> Any:
    op.drop_table("user_risk_profiles")
    op.drop_table("user_kyc")
    op.drop_table("user_profiles")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userstatus")
    op.execute("DROP TYPE IF EXISTS kycstatus")
    op.execute("DROP TYPE IF EXISTS risklevel")

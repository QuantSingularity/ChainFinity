"""
User-related database models
Enhanced user management with KYC, risk profiling, and compliance
"""

import enum
from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Enum, ForeignKey,
                        Index, Integer, Numeric, String, Text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import (AuditMixin, BaseModel, EncryptedMixin, SoftDeleteMixin,
                   TimestampMixin)


class UserStatus(enum.Enum):
    """User account status enumeration"""

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"
    BANNED = "banned"


class KYCStatus(enum.Enum):
    """KYC verification status enumeration"""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RiskLevel(enum.Enum):
    """Risk level enumeration"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class User(BaseModel, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    Enhanced user model with comprehensive user management
    """

    __tablename__ = "users"

    # Basic Information
    email = Column(String(255), unique=True, nullable=False, index=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)

    # Authentication
    hashed_password = Column(String(255), nullable=False)
    password_changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)

    # Multi-Factor Authentication
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)  # TOTP secret
    backup_codes = Column(JSON, nullable=True)  # Backup codes for MFA

    # Account Status
    status = Column(
        Enum(UserStatus), default=UserStatus.PENDING, nullable=False, index=True
    )
    status_reason = Column(Text, nullable=True)
    status_changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Blockchain
    primary_wallet_address = Column(String(42), nullable=True, index=True)

    # Activity Tracking
    last_login_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0, nullable=False)

    # Terms and Privacy
    terms_accepted_at = Column(DateTime, nullable=True)
    privacy_accepted_at = Column(DateTime, nullable=True)
    marketing_consent = Column(Boolean, default=False, nullable=False)

    # Relationships
    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    kyc = relationship(
        "UserKYC", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    risk_profile = relationship(
        "UserRiskProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    portfolios = relationship(
        "Portfolio", back_populates="user", cascade="all, delete-orphan"
    )
    transactions = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "AuditLog", back_populates="user", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_user_email_status", "email", "status"),
        Index("idx_user_wallet_status", "primary_wallet_address", "status"),
        Index("idx_user_created_status", "created_at", "status"),
    )

    def is_active(self) -> bool:
        """Check if user account is active"""
        return self.status == UserStatus.ACTIVE and not self.is_deleted

    def is_locked(self) -> bool:
        """Check if user account is locked"""
        return self.locked_until and self.locked_until > datetime.utcnow()

    def can_login(self) -> bool:
        """Check if user can login"""
        return self.is_active() and not self.is_locked() and self.email_verified

    def increment_failed_login(self) -> None:
        """Increment failed login attempts"""
        self.failed_login_attempts += 1
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)

    def reset_failed_login(self) -> None:
        """Reset failed login attempts"""
        self.failed_login_attempts = 0
        self.locked_until = None

    def record_login(self) -> None:
        """Record successful login"""
        self.last_login_at = datetime.utcnow()
        self.last_activity_at = datetime.utcnow()
        self.login_count += 1
        self.reset_failed_login()


class UserProfile(BaseModel, TimestampMixin, AuditMixin, EncryptedMixin):
    """
    User profile with personal information
    """

    __tablename__ = "user_profiles"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Personal Information (encrypted)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    middle_name = Column(String(100), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)

    # Contact Information (encrypted)
    phone_number = Column(String(20), nullable=True)
    phone_verified = Column(Boolean, default=False, nullable=False)
    phone_verified_at = Column(DateTime, nullable=True)

    # Address Information (encrypted)
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state_province = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(2), nullable=True)  # ISO 3166-1 alpha-2

    # Professional Information
    occupation = Column(String(100), nullable=True)
    employer = Column(String(255), nullable=True)
    annual_income_range = Column(String(50), nullable=True)
    net_worth_range = Column(String(50), nullable=True)

    # Investment Experience
    investment_experience_years = Column(Integer, nullable=True)
    crypto_experience_years = Column(Integer, nullable=True)
    risk_tolerance = Column(Enum(RiskLevel), nullable=True)

    # Preferences
    preferred_language = Column(String(5), default="en", nullable=False)
    preferred_currency = Column(String(3), default="USD", nullable=False)
    timezone = Column(String(50), nullable=True)

    # Relationships
    user = relationship("User", back_populates="profile")


class UserKYC(BaseModel, TimestampMixin, AuditMixin, EncryptedMixin):
    """
    KYC (Know Your Customer) verification data
    """

    __tablename__ = "user_kyc"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # KYC Status
    status = Column(
        Enum(KYCStatus), default=KYCStatus.NOT_STARTED, nullable=False, index=True
    )
    status_reason = Column(Text, nullable=True)
    status_changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Verification Provider
    provider = Column(String(50), nullable=True)  # jumio, onfido, etc.
    provider_reference_id = Column(String(255), nullable=True)

    # Document Verification
    document_type = Column(String(50), nullable=True)  # passport, drivers_license, etc.
    document_number = Column(String(100), nullable=True)
    document_country = Column(String(2), nullable=True)
    document_expiry_date = Column(DateTime, nullable=True)
    document_verified = Column(Boolean, default=False, nullable=False)
    document_verified_at = Column(DateTime, nullable=True)

    # Identity Verification
    identity_verified = Column(Boolean, default=False, nullable=False)
    identity_verified_at = Column(DateTime, nullable=True)
    identity_score = Column(Numeric(5, 2), nullable=True)  # 0-100 confidence score

    # Address Verification
    address_verified = Column(Boolean, default=False, nullable=False)
    address_verified_at = Column(DateTime, nullable=True)

    # Biometric Verification
    biometric_verified = Column(Boolean, default=False, nullable=False)
    biometric_verified_at = Column(DateTime, nullable=True)

    # Sanctions and PEP Screening
    sanctions_checked = Column(Boolean, default=False, nullable=False)
    sanctions_checked_at = Column(DateTime, nullable=True)
    sanctions_match = Column(Boolean, default=False, nullable=False)
    pep_checked = Column(Boolean, default=False, nullable=False)
    pep_checked_at = Column(DateTime, nullable=True)
    pep_match = Column(Boolean, default=False, nullable=False)

    # Review Information
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    # Expiry and Renewal
    expires_at = Column(DateTime, nullable=True)
    renewal_required = Column(Boolean, default=False, nullable=False)

    # Verification Data (encrypted JSON)
    verification_data = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="kyc")

    def is_verified(self) -> bool:
        """Check if KYC is fully verified"""
        return (
            self.status == KYCStatus.APPROVED
            and self.identity_verified
            and self.document_verified
            and not self.sanctions_match
            and (self.expires_at is None or self.expires_at > datetime.utcnow())
        )

    def is_expired(self) -> bool:
        """Check if KYC verification is expired"""
        return self.expires_at and self.expires_at <= datetime.utcnow()

    def needs_renewal(self) -> bool:
        """Check if KYC needs renewal"""
        return self.renewal_required or self.is_expired()


class UserRiskProfile(BaseModel, TimestampMixin, AuditMixin):
    """
    User risk assessment and profile
    """

    __tablename__ = "user_risk_profiles"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Risk Assessment
    risk_level = Column(
        Enum(RiskLevel), default=RiskLevel.MEDIUM, nullable=False, index=True
    )
    risk_score = Column(Numeric(5, 2), nullable=True)  # 0-100 risk score
    risk_factors = Column(JSON, nullable=True)  # List of risk factors

    # Assessment Details
    assessment_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    assessment_method = Column(String(50), nullable=True)  # manual, automated, hybrid
    assessed_by = Column(UUID(as_uuid=True), nullable=True)

    # Risk Limits
    daily_transaction_limit = Column(Numeric(20, 8), nullable=True)
    monthly_transaction_limit = Column(Numeric(20, 8), nullable=True)
    max_position_size = Column(Numeric(20, 8), nullable=True)

    # Monitoring
    enhanced_monitoring = Column(Boolean, default=False, nullable=False)
    monitoring_reason = Column(Text, nullable=True)
    monitoring_start_date = Column(DateTime, nullable=True)
    monitoring_end_date = Column(DateTime, nullable=True)

    # Review Schedule
    next_review_date = Column(DateTime, nullable=True)
    review_frequency_days = Column(
        Integer, default=365, nullable=False
    )  # Annual by default

    # Risk Metrics
    volatility_tolerance = Column(Numeric(5, 2), nullable=True)
    max_drawdown_tolerance = Column(Numeric(5, 2), nullable=True)
    liquidity_requirement = Column(String(20), nullable=True)  # high, medium, low

    # Relationships
    user = relationship("User", back_populates="risk_profile")

    def is_high_risk(self) -> bool:
        """Check if user is high risk"""
        return self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

    def needs_enhanced_monitoring(self) -> bool:
        """Check if user needs enhanced monitoring"""
        return (
            self.enhanced_monitoring
            or self.is_high_risk()
            or (
                self.monitoring_end_date
                and self.monitoring_end_date > datetime.utcnow()
            )
        )

    def is_due_for_review(self) -> bool:
        """Check if risk profile is due for review"""
        return self.next_review_date and self.next_review_date <= datetime.utcnow()

    def update_risk_level(self, new_level: RiskLevel, reason: str = None) -> None:
        """Update risk level with audit trail"""
        self.risk_level = new_level
        self.assessment_date = datetime.utcnow()
        if reason:
            if not self.risk_factors:
                self.risk_factors = []
            self.risk_factors.append(
                {
                    "date": datetime.utcnow().isoformat(),
                    "reason": reason,
                    "level": new_level.value,
                }
            )

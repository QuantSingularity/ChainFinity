"""
Transaction-related database models
Enhanced transaction tracking with compliance and monitoring
"""

import enum
from datetime import datetime
from decimal import Decimal

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


class TransactionType(enum.Enum):
    """Transaction type enumeration"""

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    SWAP = "swap"
    STAKE = "stake"
    UNSTAKE = "unstake"
    REWARD = "reward"
    FEE = "fee"
    LIQUIDATION = "liquidation"
    GOVERNANCE = "governance"


class TransactionStatus(enum.Enum):
    """Transaction status enumeration"""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class TransactionDirection(enum.Enum):
    """Transaction direction enumeration"""

    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"


class RiskLevel(enum.Enum):
    """Risk level enumeration"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Transaction(BaseModel, TimestampMixin, AuditMixin):
    """
    Transaction model with compliance and monitoring
    """

    __tablename__ = "transactions"

    # User Association
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Blockchain Information
    tx_hash = Column(
        String(66), nullable=True, unique=True, index=True
    )  # Ethereum tx hash
    block_number = Column(Integer, nullable=True, index=True)
    block_hash = Column(String(66), nullable=True)
    transaction_index = Column(Integer, nullable=True)
    network = Column(String(50), nullable=False, default="ethereum", index=True)

    # Transaction Details
    transaction_type = Column(Enum(TransactionType), nullable=False, index=True)
    status = Column(
        Enum(TransactionStatus),
        default=TransactionStatus.PENDING,
        nullable=False,
        index=True,
    )
    direction = Column(Enum(TransactionDirection), nullable=False, index=True)

    # Addresses
    from_address = Column(String(42), nullable=True, index=True)
    to_address = Column(String(42), nullable=True, index=True)
    contract_address = Column(String(42), nullable=True, index=True)

    # Asset Information
    asset_symbol = Column(String(20), nullable=False, index=True)
    asset_name = Column(String(100), nullable=True)
    asset_decimals = Column(Integer, default=18, nullable=False)

    # Amount and Value
    amount = Column(Numeric(36, 18), nullable=False)  # Raw amount in smallest unit
    amount_usd = Column(
        Numeric(20, 8), nullable=True
    )  # USD value at time of transaction
    gas_used = Column(Integer, nullable=True)
    gas_price = Column(Numeric(20, 0), nullable=True)  # Wei
    gas_fee = Column(Numeric(36, 18), nullable=True)  # ETH
    gas_fee_usd = Column(Numeric(20, 8), nullable=True)

    # Timing
    timestamp = Column(DateTime, nullable=False, index=True)
    confirmed_at = Column(DateTime, nullable=True)

    # Risk and Compliance
    risk_level = Column(
        Enum(RiskLevel), default=RiskLevel.LOW, nullable=False, index=True
    )
    risk_score = Column(Numeric(5, 2), nullable=True)  # 0-100
    is_suspicious = Column(Boolean, default=False, nullable=False, index=True)
    compliance_checked = Column(Boolean, default=False, nullable=False)
    compliance_status = Column(String(50), nullable=True)

    # AML Screening
    aml_checked = Column(Boolean, default=False, nullable=False)
    aml_risk_score = Column(Numeric(5, 2), nullable=True)
    sanctions_checked = Column(Boolean, default=False, nullable=False)
    sanctions_match = Column(Boolean, default=False, nullable=False)

    # Additional Data
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    extra_metadata = Column(JSON, nullable=True)

    # External References
    external_id = Column(String(255), nullable=True, index=True)
    reference_id = Column(String(255), nullable=True, index=True)

    # Relationships
    user = relationship("User", back_populates="transactions")

    # Indexes
    __table_args__ = (
        Index("idx_tx_user_type_status", "user_id", "transaction_type", "status"),
        Index("idx_tx_timestamp_status", "timestamp", "status"),
        Index("idx_tx_amount_usd", "amount_usd"),
        Index("idx_tx_risk_suspicious", "risk_level", "is_suspicious"),
        Index("idx_tx_network_block", "network", "block_number"),
        Index("idx_tx_addresses", "from_address", "to_address"),
    )

    def is_confirmed(self) -> bool:
        """Check if transaction is confirmed"""
        return self.status == TransactionStatus.CONFIRMED

    def is_high_value(self, threshold: Decimal = Decimal("10000")) -> bool:
        """Check if transaction is high value"""
        return self.amount_usd and self.amount_usd >= threshold

    def is_high_risk(self) -> bool:
        """Check if transaction is high risk"""
        return (
            self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
            or self.is_suspicious
            or self.sanctions_match
        )

    def calculate_risk_score(self) -> float:
        """Calculate transaction risk score"""
        score = 0.0

        # Amount-based risk
        if self.amount_usd:
            if self.amount_usd >= 100000:
                score += 30
            elif self.amount_usd >= 50000:
                score += 20
            elif self.amount_usd >= 10000:
                score += 10

        # Address-based risk
        if self.sanctions_match:
            score += 50

        # Pattern-based risk
        if self.is_suspicious:
            score += 25

        # Time-based risk (late night transactions)
        if self.timestamp.hour < 6 or self.timestamp.hour > 22:
            score += 5

        return min(score, 100.0)

    def add_tag(self, tag: str) -> None:
        """Add a tag to the transaction"""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the transaction"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)


class TransactionAlert(BaseModel, TimestampMixin, AuditMixin):
    """
    Transaction alerts for suspicious activity monitoring
    """

    __tablename__ = "transaction_alerts"

    transaction_id = Column(
        UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Alert Details
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(Enum(RiskLevel), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Status
    status = Column(
        String(20), default="open", nullable=False, index=True
    )  # open, investigating, resolved, false_positive
    assigned_to = Column(UUID(as_uuid=True), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Alert Data
    alert_data = Column(JSON, nullable=True)
    threshold_values = Column(JSON, nullable=True)

    # Relationships
    transaction = relationship("Transaction")
    user = relationship("User")

    def is_open(self) -> bool:
        """Check if alert is still open"""
        return self.status == "open"

    def resolve(self, notes: str = None, resolved_by: str = None) -> None:
        """Resolve the alert"""
        self.status = "resolved"
        self.resolved_at = datetime.utcnow()
        if notes:
            self.resolution_notes = notes
        if resolved_by:
            self.updated_by = resolved_by


class TransactionPattern(BaseModel, TimestampMixin):
    """
    Transaction patterns for ML-based fraud detection
    """

    __tablename__ = "transaction_patterns"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Pattern Details
    pattern_type = Column(String(50), nullable=False, index=True)
    pattern_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Pattern Data
    pattern_data = Column(JSON, nullable=False)
    confidence_score = Column(Numeric(5, 2), nullable=False)

    # Detection
    first_detected = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_detected = Column(DateTime, default=datetime.utcnow, nullable=False)
    detection_count = Column(Integer, default=1, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_suspicious = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User")

    def update_detection(self) -> None:
        """Update pattern detection timestamp and count"""
        self.last_detected = datetime.utcnow()
        self.detection_count += 1


class TransactionBatch(BaseModel, TimestampMixin, AuditMixin):
    """
    Transaction batches for bulk processing
    """

    __tablename__ = "transaction_batches"

    # Batch Details
    batch_name = Column(String(100), nullable=False)
    batch_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Processing Status
    status = Column(String(20), default="pending", nullable=False, index=True)
    total_transactions = Column(Integer, default=0, nullable=False)
    processed_transactions = Column(Integer, default=0, nullable=False)
    failed_transactions = Column(Integer, default=0, nullable=False)

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Results
    processing_results = Column(JSON, nullable=True)
    error_log = Column(JSON, nullable=True)

    def start_processing(self) -> None:
        """Start batch processing"""
        self.status = "processing"
        self.started_at = datetime.utcnow()

    def complete_processing(self) -> None:
        """Complete batch processing"""
        self.status = "completed"
        self.completed_at = datetime.utcnow()

    def fail_processing(self, error: str) -> None:
        """Mark batch processing as failed"""
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        if self.error_log is None:
            self.error_log = []
        self.error_log.append(
            {"timestamp": datetime.utcnow().isoformat(), "error": error}
        )

"""
Blockchain-related database models
Network management, smart contracts, and events
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


class NetworkStatus(enum.Enum):
    """Blockchain network status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"


class ContractType(enum.Enum):
    """Smart contract type"""

    ERC20 = "erc20"
    ERC721 = "erc721"
    ERC1155 = "erc1155"
    GOVERNANCE = "governance"
    VAULT = "vault"
    STAKING = "staking"
    DEX = "dex"
    LENDING = "lending"
    CUSTOM = "custom"


class EventType(enum.Enum):
    """Contract event type"""

    TRANSFER = "transfer"
    APPROVAL = "approval"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    STAKE = "stake"
    UNSTAKE = "unstake"
    REWARD = "reward"
    GOVERNANCE_VOTE = "governance_vote"
    PROPOSAL_CREATED = "proposal_created"
    CUSTOM = "custom"


class BlockchainNetwork(BaseModel, TimestampMixin, AuditMixin):
    """
    Supported blockchain networks
    """

    __tablename__ = "blockchain_networks"

    # Network Details
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Network Configuration
    chain_id = Column(Integer, unique=True, nullable=False, index=True)
    network_type = Column(String(20), nullable=False)  # mainnet, testnet

    # RPC Configuration
    rpc_url = Column(String(500), nullable=False)
    websocket_url = Column(String(500), nullable=True)
    backup_rpc_urls = Column(JSON, nullable=True)

    # Explorer Configuration
    explorer_url = Column(String(500), nullable=True)
    explorer_api_url = Column(String(500), nullable=True)
    explorer_api_key = Column(String(255), nullable=True)

    # Network Properties
    native_currency_symbol = Column(String(10), nullable=False)
    native_currency_decimals = Column(Integer, default=18, nullable=False)
    block_time_seconds = Column(Integer, nullable=True)

    # Gas Configuration
    gas_price_oracle_url = Column(String(500), nullable=True)
    default_gas_price = Column(Numeric(20, 0), nullable=True)  # Wei
    max_gas_price = Column(Numeric(20, 0), nullable=True)  # Wei

    # Status and Monitoring
    status = Column(
        Enum(NetworkStatus), default=NetworkStatus.ACTIVE, nullable=False, index=True
    )
    is_supported = Column(Boolean, default=True, nullable=False)
    last_block_number = Column(Integer, nullable=True)
    last_block_timestamp = Column(DateTime, nullable=True)

    # Performance Metrics
    avg_response_time_ms = Column(Integer, nullable=True)
    success_rate = Column(Numeric(5, 2), nullable=True)  # 0-100
    last_health_check = Column(DateTime, nullable=True)

    # Configuration
    confirmation_blocks = Column(Integer, default=12, nullable=False)
    max_reorg_depth = Column(Integer, default=100, nullable=False)

    # Metadata
    contract_metadata = Column(JSON, nullable=True)

    # Relationships
    contracts = relationship(
        "SmartContract", back_populates="network", cascade="all, delete-orphan"
    )

    def is_healthy(self) -> bool:
        """Check if network is healthy"""
        return (
            self.status == NetworkStatus.ACTIVE
            and self.is_supported
            and (self.success_rate is None or self.success_rate >= 95)
        )

    def update_health_metrics(self, response_time: int, success: bool) -> None:
        """Update network health metrics"""
        self.last_health_check = datetime.utcnow()

        # Update average response time (simple moving average)
        if self.avg_response_time_ms is None:
            self.avg_response_time_ms = response_time
        else:
            self.avg_response_time_ms = int(
                (self.avg_response_time_ms * 0.9) + (response_time * 0.1)
            )

        # Update success rate (simple moving average)
        success_value = 100 if success else 0
        if self.success_rate is None:
            self.success_rate = success_value
        else:
            self.success_rate = (self.success_rate * 0.95) + (success_value * 0.05)


class SmartContract(BaseModel, TimestampMixin, AuditMixin):
    """
    Smart contracts and their metadata
    """

    __tablename__ = "smart_contracts"

    network_id = Column(
        UUID(as_uuid=True),
        ForeignKey("blockchain_networks.id"),
        nullable=False,
        index=True,
    )

    # Contract Details
    address = Column(String(42), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=True)
    contract_type = Column(Enum(ContractType), nullable=False, index=True)

    # Contract Metadata
    description = Column(Text, nullable=True)
    version = Column(String(20), nullable=True)
    compiler_version = Column(String(50), nullable=True)

    # ABI and Bytecode
    abi = Column(JSON, nullable=True)
    bytecode = Column(Text, nullable=True)
    source_code = Column(Text, nullable=True)

    # Verification
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    verification_source = Column(String(50), nullable=True)  # etherscan, sourcify, etc.
    verified_at = Column(DateTime, nullable=True)

    # Token Information (for token contracts)
    decimals = Column(Integer, nullable=True)
    total_supply = Column(Numeric(36, 18), nullable=True)

    # Status and Monitoring
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_monitored = Column(Boolean, default=False, nullable=False)
    last_activity_block = Column(Integer, nullable=True)
    last_activity_timestamp = Column(DateTime, nullable=True)

    # Security
    is_proxy = Column(Boolean, default=False, nullable=False)
    implementation_address = Column(String(42), nullable=True)
    proxy_type = Column(String(50), nullable=True)

    # Risk Assessment
    risk_score = Column(Numeric(5, 2), nullable=True)  # 0-100
    security_audit_status = Column(String(50), nullable=True)
    audit_reports = Column(JSON, nullable=True)

    # Usage Statistics
    transaction_count = Column(Integer, default=0, nullable=False)
    unique_users = Column(Integer, default=0, nullable=False)
    total_volume = Column(Numeric(36, 18), default=0, nullable=False)

    # Metadata
    tags = Column(JSON, nullable=True)
    contract_metadata = Column(JSON, nullable=True)

    # Relationships
    network = relationship("BlockchainNetwork", back_populates="contracts")
    events = relationship(
        "ContractEvent", back_populates="contract", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        Index("idx_contract_network_address", "network_id", "address"),
        Index("idx_contract_type_active", "contract_type", "is_active"),
        Index("idx_contract_verified_monitored", "is_verified", "is_monitored"),
    )

    def get_full_address(self) -> str:
        """Get network-prefixed address"""
        return f"{self.network.name}:{self.address}"

    def is_token_contract(self) -> bool:
        """Check if contract is a token contract"""
        return self.contract_type in [
            ContractType.ERC20,
            ContractType.ERC721,
            ContractType.ERC1155,
        ]

    def update_activity(self, block_number: int, timestamp: datetime) -> None:
        """Update contract activity"""
        self.last_activity_block = block_number
        self.last_activity_timestamp = timestamp
        self.transaction_count += 1


class ContractEvent(BaseModel, TimestampMixin):
    """
    Smart contract events and logs
    """

    __tablename__ = "contract_events"

    contract_id = Column(
        UUID(as_uuid=True), ForeignKey("smart_contracts.id"), nullable=False, index=True
    )

    # Event Details
    event_name = Column(String(100), nullable=False, index=True)
    event_type = Column(Enum(EventType), nullable=False, index=True)
    event_signature = Column(String(66), nullable=False)  # Event signature hash

    # Blockchain Details
    transaction_hash = Column(String(66), nullable=False, index=True)
    block_number = Column(Integer, nullable=False, index=True)
    block_hash = Column(String(66), nullable=False)
    log_index = Column(Integer, nullable=False)
    transaction_index = Column(Integer, nullable=False)

    # Event Data
    topics = Column(JSON, nullable=False)  # Event topics
    data = Column(Text, nullable=False)  # Event data
    decoded_data = Column(JSON, nullable=True)  # Decoded event parameters

    # Addresses
    from_address = Column(String(42), nullable=True, index=True)
    to_address = Column(String(42), nullable=True, index=True)

    # Values
    value = Column(Numeric(36, 18), nullable=True)
    token_id = Column(String(100), nullable=True)  # For NFTs

    # Timestamp
    block_timestamp = Column(DateTime, nullable=False, index=True)

    # Processing Status
    is_processed = Column(Boolean, default=False, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    processing_error = Column(Text, nullable=True)

    # Metadata
    contract_metadata = Column(JSON, nullable=True)

    # Relationships
    contract = relationship("SmartContract", back_populates="events")

    # Constraints
    __table_args__ = (
        Index("idx_event_contract_name", "contract_id", "event_name"),
        Index("idx_event_block_log", "block_number", "log_index"),
        Index("idx_event_tx_hash", "transaction_hash"),
        Index("idx_event_addresses", "from_address", "to_address"),
        Index("idx_event_timestamp_processed", "block_timestamp", "is_processed"),
    )

    def mark_processed(self) -> None:
        """Mark event as processed"""
        self.is_processed = True
        self.processed_at = datetime.utcnow()

    def mark_processing_error(self, error: str) -> None:
        """Mark event processing error"""
        self.processing_error = error
        self.processed_at = datetime.utcnow()


class BlockchainSync(BaseModel, TimestampMixin):
    """
    Blockchain synchronization status
    """

    __tablename__ = "blockchain_sync"

    network_id = Column(
        UUID(as_uuid=True),
        ForeignKey("blockchain_networks.id"),
        nullable=False,
        index=True,
    )

    # Sync Details
    sync_type = Column(
        String(50), nullable=False, index=True
    )  # blocks, events, transactions

    # Block Range
    start_block = Column(Integer, nullable=False)
    end_block = Column(Integer, nullable=True)
    current_block = Column(Integer, nullable=False)

    # Progress
    total_blocks = Column(Integer, nullable=True)
    processed_blocks = Column(Integer, default=0, nullable=False)
    progress_percentage = Column(Numeric(5, 2), default=0, nullable=False)

    # Status
    status = Column(
        String(20), default="running", nullable=False, index=True
    )  # running, completed, failed, paused

    # Timing
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    estimated_completion = Column(DateTime, nullable=True)

    # Performance
    blocks_per_second = Column(Numeric(10, 2), nullable=True)
    avg_block_time_ms = Column(Integer, nullable=True)

    # Error Handling
    error_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    last_error_at = Column(DateTime, nullable=True)

    # Metadata
    contract_metadata = Column(JSON, nullable=True)

    # Relationships
    network = relationship("BlockchainNetwork")

    def update_progress(self, current_block: int) -> None:
        """Update sync progress"""
        self.current_block = current_block
        self.processed_blocks = current_block - self.start_block

        if self.total_blocks and self.total_blocks > 0:
            self.progress_percentage = (self.processed_blocks / self.total_blocks) * 100

        # Calculate blocks per second
        elapsed_seconds = (datetime.utcnow() - self.started_at).total_seconds()
        if elapsed_seconds > 0:
            self.blocks_per_second = self.processed_blocks / elapsed_seconds

    def complete_sync(self) -> None:
        """Mark sync as completed"""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100

    def fail_sync(self, error: str) -> None:
        """Mark sync as failed"""
        self.status = "failed"
        self.last_error = error
        self.last_error_at = datetime.utcnow()
        self.error_count += 1


class GasTracker(BaseModel, TimestampMixin):
    """
    Gas price tracking and analytics
    """

    __tablename__ = "gas_tracker"

    network_id = Column(
        UUID(as_uuid=True),
        ForeignKey("blockchain_networks.id"),
        nullable=False,
        index=True,
    )

    # Gas Prices (in Wei)
    slow_gas_price = Column(Numeric(20, 0), nullable=False)
    standard_gas_price = Column(Numeric(20, 0), nullable=False)
    fast_gas_price = Column(Numeric(20, 0), nullable=False)
    instant_gas_price = Column(Numeric(20, 0), nullable=False)

    # Base Fee (EIP-1559)
    base_fee = Column(Numeric(20, 0), nullable=True)
    priority_fee = Column(Numeric(20, 0), nullable=True)

    # Block Information
    block_number = Column(Integer, nullable=False, index=True)
    block_utilization = Column(Numeric(5, 2), nullable=True)  # 0-100%

    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Source
    data_source = Column(String(50), nullable=False)  # ethgasstation, blocknative, etc.

    # Relationships
    network = relationship("BlockchainNetwork")

    # Constraints
    __table_args__ = (
        Index("idx_gas_network_timestamp", "network_id", "timestamp"),
        Index("idx_gas_block_number", "block_number"),
    )

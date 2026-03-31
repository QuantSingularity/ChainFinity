"""
Portfolio-related database models
Multi-asset portfolio management with risk tracking
"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Dict

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import AuditMixin, BaseModel, TimestampMixin


class PortfolioType(enum.Enum):
    """Portfolio type enumeration"""

    MAIN = "main"
    TRADING = "trading"
    SAVINGS = "savings"
    STAKING = "staking"
    DEFI = "defi"
    NFT = "nft"


class AssetType(enum.Enum):
    """Asset type enumeration"""

    CRYPTOCURRENCY = "cryptocurrency"
    TOKEN = "token"
    NFT = "nft"
    LP_TOKEN = "lp_token"
    STAKED_ASSET = "staked_asset"
    DERIVATIVE = "derivative"


class AllocationStrategy(enum.Enum):
    """Portfolio allocation strategy"""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"


class RebalanceFrequency(enum.Enum):
    """Rebalancing frequency"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    MANUAL = "manual"


class Portfolio(BaseModel, TimestampMixin, AuditMixin):
    """
    User portfolio with multi-asset support
    """

    __tablename__ = "portfolios"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Portfolio Details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    portfolio_type = Column(
        Enum(PortfolioType), default=PortfolioType.MAIN, nullable=False, index=True
    )

    # Wallet Association
    wallet_address = Column(String(42), nullable=True, index=True)
    network = Column(String(50), default="ethereum", nullable=False, index=True)

    # Portfolio Settings
    is_active = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    auto_rebalance = Column(Boolean, default=False, nullable=False)
    rebalance_frequency = Column(
        Enum(RebalanceFrequency), default=RebalanceFrequency.MANUAL, nullable=False
    )

    # Allocation Strategy
    allocation_strategy = Column(
        Enum(AllocationStrategy), default=AllocationStrategy.CUSTOM, nullable=False
    )
    target_allocations = Column(JSON, nullable=True)  # Target allocation percentages

    # Portfolio Metrics
    total_value_usd = Column(Numeric(20, 8), default=0, nullable=False)
    total_cost_basis = Column(Numeric(20, 8), default=0, nullable=False)
    unrealized_pnl = Column(Numeric(20, 8), default=0, nullable=False)
    realized_pnl = Column(Numeric(20, 8), default=0, nullable=False)

    # Performance Metrics
    daily_return = Column(Numeric(10, 6), default=0, nullable=False)
    weekly_return = Column(Numeric(10, 6), default=0, nullable=False)
    monthly_return = Column(Numeric(10, 6), default=0, nullable=False)
    yearly_return = Column(Numeric(10, 6), default=0, nullable=False)

    # Risk Metrics
    volatility = Column(Numeric(10, 6), nullable=True)
    sharpe_ratio = Column(Numeric(10, 6), nullable=True)
    max_drawdown = Column(Numeric(10, 6), nullable=True)
    beta = Column(Numeric(10, 6), nullable=True)

    # Last Update
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_rebalanced = Column(DateTime, nullable=True)
    next_rebalance = Column(DateTime, nullable=True)

    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="portfolios")
    assets = relationship(
        "PortfolioAsset", back_populates="portfolio", cascade="all, delete-orphan"
    )
    allocations = relationship(
        "AssetAllocation", back_populates="portfolio", cascade="all, delete-orphan"
    )
    snapshots = relationship(
        "PortfolioSnapshot", back_populates="portfolio", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_portfolio_name"),
        Index("idx_portfolio_user_type", "user_id", "portfolio_type"),
        Index("idx_portfolio_wallet_network", "wallet_address", "network"),
        Index("idx_portfolio_value", "total_value_usd"),
    )

    def calculate_total_value(self) -> Decimal:
        """Calculate total portfolio value"""
        total = Decimal("0")
        for asset in self.assets:
            if asset.current_value_usd:
                total += asset.current_value_usd
        return total

    def calculate_allocation_percentages(self) -> Dict[str, float]:
        """Calculate current allocation percentages"""
        total_value = self.total_value_usd
        if total_value == 0:
            return {}

        allocations = {}
        for asset in self.assets:
            if asset.current_value_usd:
                percentage = float(asset.current_value_usd / total_value * 100)
                allocations[asset.asset_symbol] = percentage

        return allocations

    def needs_rebalancing(self, threshold: float = 5.0) -> bool:
        """Check if portfolio needs rebalancing"""
        if not self.auto_rebalance or not self.target_allocations:
            return False

        current_allocations = self.calculate_allocation_percentages()

        for asset_symbol, target_percentage in self.target_allocations.items():
            current_percentage = current_allocations.get(asset_symbol, 0)
            deviation = abs(current_percentage - target_percentage)
            if deviation > threshold:
                return True

        return False

    def update_metrics(self) -> None:
        """Update portfolio metrics"""
        self.total_value_usd = self.calculate_total_value()
        self.last_updated = datetime.utcnow()


class PortfolioAsset(BaseModel, TimestampMixin, AuditMixin):
    """
    Individual assets within a portfolio
    """

    __tablename__ = "portfolio_assets"

    portfolio_id = Column(
        UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True
    )

    # Asset Details
    asset_symbol = Column(String(20), nullable=False, index=True)
    asset_name = Column(String(100), nullable=True)
    asset_type = Column(
        Enum(AssetType), default=AssetType.CRYPTOCURRENCY, nullable=False, index=True
    )
    contract_address = Column(String(42), nullable=True, index=True)

    # Holdings
    quantity = Column(Numeric(36, 18), nullable=False, default=0)
    cost_basis = Column(Numeric(20, 8), nullable=False, default=0)
    average_cost = Column(Numeric(20, 8), nullable=False, default=0)

    # Current Values
    current_price = Column(Numeric(20, 8), nullable=True)
    current_value_usd = Column(Numeric(20, 8), nullable=True)

    # P&L
    unrealized_pnl = Column(Numeric(20, 8), default=0, nullable=False)
    unrealized_pnl_percentage = Column(Numeric(10, 6), default=0, nullable=False)
    realized_pnl = Column(Numeric(20, 8), default=0, nullable=False)

    # Allocation
    target_allocation = Column(Numeric(5, 2), nullable=True)  # Target percentage
    current_allocation = Column(Numeric(5, 2), nullable=True)  # Current percentage

    # Staking Information
    is_staked = Column(Boolean, default=False, nullable=False)
    staking_rewards = Column(Numeric(36, 18), default=0, nullable=False)
    staking_apy = Column(Numeric(5, 2), nullable=True)

    # DeFi Information
    is_in_defi = Column(Boolean, default=False, nullable=False)
    defi_protocol = Column(String(50), nullable=True)
    defi_position_id = Column(String(100), nullable=True)

    # Last Update
    last_price_update = Column(DateTime, nullable=True)
    last_quantity_update = Column(DateTime, nullable=True)

    # Metadata
    extra_metadata = Column(JSON, nullable=True)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="assets")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "portfolio_id",
            "asset_symbol",
            "contract_address",
            name="uq_portfolio_asset",
        ),
        Index("idx_asset_symbol_type", "asset_symbol", "asset_type"),
        Index("idx_asset_value", "current_value_usd"),
    )

    def calculate_unrealized_pnl(self) -> Decimal:
        """Calculate unrealized P&L"""
        if self.current_value_usd and self.cost_basis:
            return self.current_value_usd - self.cost_basis
        return Decimal("0")

    def calculate_unrealized_pnl_percentage(self) -> Decimal:
        """Calculate unrealized P&L percentage"""
        if self.cost_basis and self.cost_basis > 0:
            pnl = self.calculate_unrealized_pnl()
            return (pnl / self.cost_basis) * 100
        return Decimal("0")

    def update_price(self, new_price: Decimal) -> None:
        """Update asset price and recalculate values"""
        self.current_price = new_price
        self.current_value_usd = self.quantity * new_price
        self.unrealized_pnl = self.calculate_unrealized_pnl()
        self.unrealized_pnl_percentage = self.calculate_unrealized_pnl_percentage()
        self.last_price_update = datetime.utcnow()

    def add_quantity(self, quantity: Decimal, cost: Decimal) -> None:
        """Add to asset quantity and update cost basis"""
        total_cost = self.cost_basis + cost
        total_quantity = self.quantity + quantity

        self.quantity = total_quantity
        self.cost_basis = total_cost

        if total_quantity > 0:
            self.average_cost = total_cost / total_quantity

        self.last_quantity_update = datetime.utcnow()

    def remove_quantity(self, quantity: Decimal) -> Decimal:
        """Remove asset quantity and calculate realized P&L"""
        if quantity > self.quantity:
            raise ValueError("Cannot remove more than available quantity")

        # Calculate realized P&L for the sold portion
        if self.current_price and self.average_cost:
            realized_pnl = quantity * (self.current_price - self.average_cost)
            self.realized_pnl += realized_pnl

        # Update quantities and cost basis
        cost_reduction = (quantity / self.quantity) * self.cost_basis
        self.quantity -= quantity
        self.cost_basis -= cost_reduction

        self.last_quantity_update = datetime.utcnow()

        return realized_pnl if "realized_pnl" in locals() else Decimal("0")


class AssetAllocation(BaseModel, TimestampMixin, AuditMixin):
    """
    Target asset allocations for portfolio rebalancing
    """

    __tablename__ = "asset_allocations"

    portfolio_id = Column(
        UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True
    )

    # Asset Details
    asset_symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(Enum(AssetType), nullable=False)

    # Allocation
    target_percentage = Column(Numeric(5, 2), nullable=False)  # 0-100
    min_percentage = Column(Numeric(5, 2), nullable=True)
    max_percentage = Column(Numeric(5, 2), nullable=True)

    # Rebalancing
    rebalance_threshold = Column(
        Numeric(5, 2), default=5.0, nullable=False
    )  # Deviation threshold
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="allocations")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "portfolio_id", "asset_symbol", name="uq_portfolio_allocation"
        ),
    )


class PortfolioSnapshot(BaseModel, TimestampMixin):
    """
    Historical portfolio snapshots for performance tracking
    """

    __tablename__ = "portfolio_snapshots"

    portfolio_id = Column(
        UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True
    )

    # Snapshot Data
    snapshot_date = Column(DateTime, nullable=False, index=True)
    total_value_usd = Column(Numeric(20, 8), nullable=False)
    total_cost_basis = Column(Numeric(20, 8), nullable=False)

    # Performance Metrics
    daily_return = Column(Numeric(10, 6), nullable=True)
    cumulative_return = Column(Numeric(10, 6), nullable=True)

    # Risk Metrics
    volatility = Column(Numeric(10, 6), nullable=True)
    sharpe_ratio = Column(Numeric(10, 6), nullable=True)

    # Asset Breakdown
    asset_breakdown = Column(JSON, nullable=False)  # Asset allocations at snapshot time

    # Relationships
    portfolio = relationship("Portfolio", back_populates="snapshots")

    # Constraints
    __table_args__ = (
        UniqueConstraint("portfolio_id", "snapshot_date", name="uq_portfolio_snapshot"),
        Index("idx_snapshot_date_value", "snapshot_date", "total_value_usd"),
    )


class PortfolioPerformance(BaseModel, TimestampMixin):
    """
    Portfolio performance analytics and benchmarking
    """

    __tablename__ = "portfolio_performance"

    portfolio_id = Column(
        UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True
    )

    # Time Period
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)
    period_type = Column(
        String(20), nullable=False, index=True
    )  # daily, weekly, monthly, yearly

    # Returns
    absolute_return = Column(Numeric(20, 8), nullable=False)
    percentage_return = Column(Numeric(10, 6), nullable=False)
    annualized_return = Column(Numeric(10, 6), nullable=True)

    # Risk Metrics
    volatility = Column(Numeric(10, 6), nullable=True)
    sharpe_ratio = Column(Numeric(10, 6), nullable=True)
    sortino_ratio = Column(Numeric(10, 6), nullable=True)
    max_drawdown = Column(Numeric(10, 6), nullable=True)

    # Benchmark Comparison
    benchmark_return = Column(Numeric(10, 6), nullable=True)
    alpha = Column(Numeric(10, 6), nullable=True)
    beta = Column(Numeric(10, 6), nullable=True)
    tracking_error = Column(Numeric(10, 6), nullable=True)

    # Additional Metrics
    win_rate = Column(Numeric(5, 2), nullable=True)
    profit_factor = Column(Numeric(10, 6), nullable=True)
    calmar_ratio = Column(Numeric(10, 6), nullable=True)

    # Relationships
    portfolio = relationship("Portfolio")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "portfolio_id",
            "period_start",
            "period_end",
            "period_type",
            name="uq_portfolio_performance",
        ),
        Index("idx_performance_period", "period_start", "period_end"),
    )

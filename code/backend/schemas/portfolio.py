"""
Portfolio-related Pydantic schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from schemas.base import BaseSchema


class AssetAllocation(BaseModel):
    """Asset allocation schema"""

    symbol: str
    target_percentage: Decimal

    # backward-compat aliases
    asset_symbol: Optional[str] = None
    allocation_percentage: Optional[Decimal] = None

    def model_post_init(self, __context: Any) -> None:
        # Sync alias fields
        if self.asset_symbol is None:
            object.__setattr__(self, "asset_symbol", self.symbol)
        if self.allocation_percentage is None:
            object.__setattr__(self, "allocation_percentage", self.target_percentage)


class PortfolioCreate(BaseModel):
    """Portfolio creation schema"""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    portfolio_type: Optional[str] = Field(default="main")
    base_currency: Optional[str] = Field(default="USD")
    target_allocation: Optional[dict] = Field(default=None)
    risk_tolerance: str = Field(default="moderate")
    investment_objective: Optional[str] = None
    rebalancing_frequency: Optional[str] = Field(default="monthly")
    auto_rebalance: Optional[bool] = Field(default=False)
    initial_cash: Optional[Decimal] = Field(default=Decimal("0.00"))


class PortfolioUpdate(BaseModel):
    """Portfolio update schema"""

    name: Optional[str] = None
    description: Optional[str] = None
    risk_tolerance: Optional[str] = None
    target_allocation: Optional[dict] = None
    investment_objective: Optional[str] = None
    rebalancing_frequency: Optional[str] = None
    auto_rebalance: Optional[bool] = None


class PortfolioResponse(BaseSchema):
    """Portfolio response schema"""

    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    total_value: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime


class PortfolioAnalytics(BaseSchema):
    """Portfolio analytics schema"""

    total_value: Decimal
    total_return: Decimal
    return_percentage: Decimal


class PortfolioPerformance(BaseSchema):
    """Portfolio performance schema"""

    period: str
    return_value: Decimal
    return_percentage: Decimal


class PortfolioAssetResponse(BaseSchema):
    """Portfolio asset response schema"""

    id: UUID
    portfolio_id: UUID
    asset_symbol: Optional[str] = None
    symbol: Optional[str] = None
    quantity: Decimal
    current_value: Optional[Decimal] = None


class PortfolioAssetCreate(BaseModel):
    """Portfolio asset creation schema"""

    symbol: str = Field(..., min_length=1, max_length=20)
    asset_type: Optional[str] = Field(default="cryptocurrency")
    quantity: Decimal = Field(..., gt=0)
    average_cost: Optional[Decimal] = None
    target_allocation: Optional[Decimal] = None


class PortfolioAssetUpdate(BaseModel):
    """Portfolio asset update schema"""

    symbol: Optional[str] = None
    asset_type: Optional[str] = None
    quantity: Optional[Decimal] = None
    average_cost: Optional[Decimal] = None
    target_allocation: Optional[Decimal] = None
    notes: Optional[str] = None


class RebalanceRequest(BaseModel):
    """Portfolio rebalance request schema"""

    target_allocations: List[AssetAllocation]
    execute_immediately: Optional[bool] = Field(default=False)
    rebalancing_method: Optional[str] = Field(default="threshold")


class RebalanceResponse(BaseModel):
    """Portfolio rebalance response schema"""

    trades_executed: int = 0
    new_allocations: Optional[Dict[str, Any]] = None
    status: Optional[str] = "completed"
    message: Optional[str] = None
    portfolio_id: Optional[UUID] = None
    rebalancing_date: Optional[datetime] = None
    proposed_trades: Optional[List[Dict[str, Any]]] = None
    total_cost: Optional[float] = None
    market_impact: Optional[Dict[str, Any]] = None
    success: Optional[bool] = True

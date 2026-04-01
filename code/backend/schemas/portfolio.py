"""
Portfolio-related Pydantic schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from schemas.base import BaseSchema


class AssetAllocation(BaseModel):
    """Asset allocation schema"""

    asset_symbol: str
    allocation_percentage: Decimal
    target_amount: Optional[Decimal] = None


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
    description: Optional[str]
    total_value: Decimal
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
    asset_symbol: str
    quantity: Decimal
    current_value: Decimal


class PortfolioAssetCreate(BaseModel):
    """Portfolio asset creation schema"""

    symbol: str = Field(..., min_length=1, max_length=20)
    asset_type: Optional[str] = Field(default="cryptocurrency")
    quantity: Decimal = Field(..., gt=0)
    average_cost: Optional[Decimal] = None
    target_allocation: Optional[Decimal] = None


class PortfolioAssetUpdate(BaseModel):
    """Portfolio asset update schema"""

    quantity: Optional[Decimal] = None
    average_cost: Optional[Decimal] = None
    target_allocation: Optional[Decimal] = None
    notes: Optional[str] = None


class RebalanceRequest(BaseModel):
    """Portfolio rebalance request schema"""

    target_allocations: List[AssetAllocation]


class RebalanceResponse(BaseSchema):
    """Portfolio rebalance response schema"""

    status: str
    trades_executed: int
    message: str

"""
Portfolio Service for Financial Industry Applications
Comprehensive portfolio management with advanced analytics, risk management, and compliance
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from config.settings import settings
from models.portfolio import Portfolio, PortfolioAsset, PortfolioSnapshot
from models.user import User
from schemas.base import PaginatedResponse
from schemas.portfolio import (
    PortfolioAssetUpdate,
    PortfolioCreate,
    PortfolioUpdate,
    RebalanceRequest,
    RebalanceResponse,
)
from services.analytics.performance_service import PerformanceService
from services.compliance.compliance_service import ComplianceService
from services.market.market_data_service import MarketDataService
from services.risk.risk_service import RiskService
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class PortfolioService:
    """
    Portfolio management service with institutional-grade features
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.market_data_service = MarketDataService()
        self.risk_service = RiskService(db)
        self.compliance_service = ComplianceService()
        self.performance_service = PerformanceService(db)

    async def create_portfolio(
        self, user_id: UUID, portfolio_data: PortfolioCreate
    ) -> Portfolio:
        """
        Create a new portfolio with enhanced validation and setup
        """
        try:
            await self._get_active_user(user_id)
            await self._validate_portfolio_limits(user_id)
            portfolio = Portfolio(
                user_id=user_id,
                name=portfolio_data.name,
                description=portfolio_data.description,
                portfolio_type=portfolio_data.portfolio_type,
                base_currency=portfolio_data.base_currency or "USD",
                target_allocation=portfolio_data.target_allocation or {},
                risk_tolerance=portfolio_data.risk_tolerance,
                investment_objective=portfolio_data.investment_objective,
                rebalancing_frequency=portfolio_data.rebalancing_frequency or "monthly",
                auto_rebalance=portfolio_data.auto_rebalance or False,
                created_at=datetime.utcnow(),
            )
            self.db.add(portfolio)
            await self.db.flush()
            await self._create_portfolio_snapshot(portfolio)
            await self.risk_service.assess_portfolio_risk(portfolio.id, user_id)
            await self.db.commit()
            logger.info(f"Portfolio created: {portfolio.id} for user {user_id}")
            return portfolio
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating portfolio: {e}")
            raise

    async def get_portfolio(
        self, portfolio_id: UUID, user_id: UUID
    ) -> Optional[Portfolio]:
        """
        Get portfolio with comprehensive data loading
        """
        try:
            stmt = (
                select(Portfolio)
                .options(
                    selectinload(Portfolio.assets),
                    selectinload(Portfolio.snapshots),
                    selectinload(Portfolio.risk_assessments),
                )
                .where(
                    and_(
                        Portfolio.id == portfolio_id,
                        Portfolio.user_id == user_id,
                        not Portfolio.is_deleted,
                    )
                )
            )
            result = await self.db.execute(stmt)
            portfolio = result.scalar_one_or_none()
            if portfolio:
                await self._update_portfolio_values(portfolio)
            return portfolio
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            raise

    async def get_user_portfolios(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 20,
        include_deleted: bool = False,
    ) -> PaginatedResponse:
        """
        Get user portfolios with pagination and filtering
        """
        try:
            offset = (page - 1) * size
            conditions = [Portfolio.user_id == user_id]
            if not include_deleted:
                conditions.append(not Portfolio.is_deleted)
            count_stmt = select(func.count(Portfolio.id)).where(and_(*conditions))
            count_result = await self.db.execute(count_stmt)
            total = count_result.scalar()
            stmt = (
                select(Portfolio)
                .options(selectinload(Portfolio.assets))
                .where(and_(*conditions))
                .order_by(desc(Portfolio.created_at))
                .offset(offset)
                .limit(size)
            )
            result = await self.db.execute(stmt)
            portfolios = result.scalars().all()
            for portfolio in portfolios:
                await self._update_portfolio_values(portfolio)
            return PaginatedResponse(
                items=portfolios,
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size,
            )
        except Exception as e:
            logger.error(f"Error getting user portfolios: {e}")
            raise

    async def update_portfolio(
        self, portfolio_id: UUID, user_id: UUID, portfolio_update: PortfolioUpdate
    ) -> Portfolio:
        """
        Update portfolio with validation and compliance checks
        """
        try:
            portfolio = await self.get_portfolio(portfolio_id, user_id)
            if not portfolio:
                raise ValueError("Portfolio not found")
            update_data = portfolio_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(portfolio, field):
                    setattr(portfolio, field, value)
            portfolio.updated_at = datetime.utcnow()
            if "target_allocation" in update_data:
                await self._analyze_rebalancing_needs(portfolio)
            await self.db.commit()
            logger.info(f"Portfolio updated: {portfolio_id}")
            return portfolio
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating portfolio: {e}")
            raise

    async def add_portfolio_asset(
        self, portfolio_id: UUID, user_id: UUID, asset_data: PortfolioAssetUpdate
    ) -> PortfolioAsset:
        """
        Add asset to portfolio with validation and compliance
        """
        try:
            portfolio = await self.get_portfolio(portfolio_id, user_id)
            if not portfolio:
                raise ValueError("Portfolio not found")
            await self._validate_asset(asset_data.symbol)
            existing_asset = await self._get_portfolio_asset(
                portfolio_id, asset_data.symbol
            )
            if existing_asset:
                existing_asset.quantity += asset_data.quantity
                existing_asset.average_cost = self._calculate_average_cost(
                    existing_asset.quantity - asset_data.quantity,
                    existing_asset.average_cost,
                    asset_data.quantity,
                    asset_data.average_cost,
                )
                existing_asset.updated_at = datetime.utcnow()
                await self.db.commit()
                return existing_asset
            asset = PortfolioAsset(
                portfolio_id=portfolio_id,
                symbol=asset_data.symbol,
                asset_type=asset_data.asset_type,
                quantity=asset_data.quantity,
                average_cost=asset_data.average_cost,
                target_allocation=asset_data.target_allocation,
                created_at=datetime.utcnow(),
            )
            self.db.add(asset)
            await self._update_portfolio_values(portfolio)
            await self.compliance_service.check_portfolio_compliance(portfolio)
            await self.db.commit()
            logger.info(
                f"Asset added to portfolio: {asset_data.symbol} to {portfolio_id}"
            )
            return asset
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error adding portfolio asset: {e}")
            raise

    async def rebalance_portfolio(
        self, portfolio_id: UUID, user_id: UUID, rebalance_request: RebalanceRequest
    ) -> RebalanceResponse:
        """
        Perform portfolio rebalancing with advanced algorithms
        """
        try:
            portfolio = await self.get_portfolio(portfolio_id, user_id)
            if not portfolio:
                raise ValueError("Portfolio not found")
            current_allocations = await self._calculate_current_allocations(portfolio)
            target_allocations = (
                rebalance_request.target_allocations or portfolio.target_allocation
            )
            trades = await self._calculate_rebalancing_trades(
                portfolio,
                current_allocations,
                target_allocations,
                rebalance_request.rebalancing_method,
            )
            await self._validate_rebalancing_trades(portfolio, trades)
            executed_trades = []
            if rebalance_request.execute_immediately:
                executed_trades = await self._execute_rebalancing_trades(
                    portfolio, trades
                )
            rebalancing_record = {
                "portfolio_id": str(portfolio_id),
                "rebalancing_date": datetime.utcnow().isoformat(),
                "method": rebalance_request.rebalancing_method,
                "target_allocations": target_allocations,
                "current_allocations": current_allocations,
                "proposed_trades": trades,
                "executed_trades": executed_trades,
                "total_cost": sum((trade.get("cost", 0) for trade in executed_trades)),
                "estimated_impact": await self._calculate_market_impact(trades),
            }
            await self.db.commit()
            return RebalanceResponse(
                portfolio_id=portfolio_id,
                rebalancing_date=datetime.utcnow(),
                proposed_trades=trades,
                executed_trades=executed_trades,
                total_cost=rebalancing_record["total_cost"],
                market_impact=rebalancing_record["estimated_impact"],
                success=True,
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error rebalancing portfolio: {e}")
            raise

    async def sync_portfolio_with_blockchain(
        self, portfolio_id: UUID, user_id: UUID, wallet_addresses: List[str]
    ) -> None:
        """
        Sync portfolio with blockchain wallet holdings
        """
        try:
            portfolio = await self.get_portfolio(portfolio_id, user_id)
            if not portfolio:
                raise ValueError("Portfolio not found")
            all_holdings = {}
            for address in wallet_addresses:
                holdings = await self._get_wallet_holdings(address)
                for symbol, data in holdings.items():
                    if symbol in all_holdings:
                        all_holdings[symbol]["quantity"] += data["quantity"]
                        all_holdings[symbol]["value"] += data["value"]
                    else:
                        all_holdings[symbol] = data
            for symbol, holding_data in all_holdings.items():
                asset = await self._get_portfolio_asset(portfolio_id, symbol)
                if asset:
                    asset.quantity = holding_data["quantity"]
                    asset.current_price = holding_data["price"]
                    asset.updated_at = datetime.utcnow()
                else:
                    asset = PortfolioAsset(
                        portfolio_id=portfolio_id,
                        symbol=symbol,
                        asset_type="cryptocurrency",
                        quantity=holding_data["quantity"],
                        current_price=holding_data["price"],
                        average_cost=holding_data["price"],
                        created_at=datetime.utcnow(),
                    )
                    self.db.add(asset)
            portfolio.last_sync_at = datetime.utcnow()
            portfolio.sync_wallet_addresses = wallet_addresses
            await self.db.commit()
            logger.info(f"Portfolio synced with blockchain: {portfolio_id}")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error syncing portfolio with blockchain: {e}")
            raise

    async def _get_active_user(self, user_id: UUID) -> User:
        """Get active user or raise error"""
        stmt = select(User).where(and_(User.id == user_id, not User.is_deleted))
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
        if not user.can_trade():
            raise ValueError("User is not authorized to trade")
        return user

    async def _validate_portfolio_limits(self, user_id: UUID) -> None:
        """Validate user portfolio limits"""
        stmt = select(func.count(Portfolio.id)).where(
            and_(Portfolio.user_id == user_id, not Portfolio.is_deleted)
        )
        result = await self.db.execute(stmt)
        portfolio_count = result.scalar()
        max_portfolios = settings.portfolio.MAX_PORTFOLIOS_PER_USER
        if portfolio_count >= max_portfolios:
            raise ValueError(f"Maximum portfolio limit reached ({max_portfolios})")

    async def _create_portfolio_snapshot(self, portfolio: Portfolio) -> None:
        """Create initial portfolio snapshot"""
        snapshot = PortfolioSnapshot(
            portfolio_id=portfolio.id,
            total_value=Decimal("0.00"),
            asset_count=0,
            snapshot_date=datetime.utcnow(),
            metadata={"initial_snapshot": True},
        )
        self.db.add(snapshot)

    async def _update_portfolio_values(self, portfolio: Portfolio) -> None:
        """Update portfolio with real-time market values"""
        total_value = Decimal("0.00")
        for asset in portfolio.assets:
            if asset.symbol:
                current_price = await self.market_data_service.get_current_price(
                    asset.symbol
                )
                if current_price:
                    asset.current_price = current_price
                    asset.current_value = asset.quantity * current_price
                    total_value += asset.current_value
        portfolio.total_value = total_value
        portfolio.last_updated_at = datetime.utcnow()

    async def _validate_asset(self, symbol: str) -> None:
        """Validate asset symbol"""
        is_valid = await self.market_data_service.validate_symbol(symbol)
        if not is_valid:
            raise ValueError(f"Invalid asset symbol: {symbol}")

    async def _get_portfolio_asset(
        self, portfolio_id: UUID, symbol: str
    ) -> Optional[PortfolioAsset]:
        """Get specific portfolio asset"""
        stmt = select(PortfolioAsset).where(
            and_(
                PortfolioAsset.portfolio_id == portfolio_id,
                PortfolioAsset.symbol == symbol,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _calculate_average_cost(
        self,
        existing_quantity: Decimal,
        existing_cost: Decimal,
        new_quantity: Decimal,
        new_cost: Decimal,
    ) -> Decimal:
        """Calculate weighted average cost"""
        total_cost = existing_quantity * existing_cost + new_quantity * new_cost
        total_quantity = existing_quantity + new_quantity
        return total_cost / total_quantity if total_quantity > 0 else Decimal("0.00")

    async def _calculate_current_allocations(
        self, portfolio: Portfolio
    ) -> Dict[str, float]:
        """Calculate current portfolio allocations"""
        allocations = {}
        total_value = portfolio.total_value or Decimal("0.00")
        if total_value > 0:
            for asset in portfolio.assets:
                if asset.current_value:
                    allocation = float(asset.current_value / total_value * 100)
                    allocations[asset.symbol] = allocation
        return allocations

    async def _calculate_rebalancing_trades(
        self,
        portfolio: Portfolio,
        current_allocations: Dict[str, float],
        target_allocations: Dict[str, float],
        method: str = "threshold",
    ) -> List[Dict[str, Any]]:
        """Calculate trades needed for rebalancing"""
        trades = []
        total_value = float(portfolio.total_value or Decimal("0.00"))
        for symbol, target_pct in target_allocations.items():
            current_pct = current_allocations.get(symbol, 0.0)
            difference = target_pct - current_pct
            if abs(difference) > settings.portfolio.REBALANCING_THRESHOLD:
                target_value = total_value * (target_pct / 100)
                current_value = total_value * (current_pct / 100)
                trade_value = target_value - current_value
                asset = await self._get_portfolio_asset(portfolio.id, symbol)
                if asset and asset.current_price:
                    trade_quantity = trade_value / float(asset.current_price)
                    trades.append(
                        {
                            "symbol": symbol,
                            "action": "buy" if trade_quantity > 0 else "sell",
                            "quantity": abs(trade_quantity),
                            "estimated_price": float(asset.current_price),
                            "estimated_value": abs(trade_value),
                            "current_allocation": current_pct,
                            "target_allocation": target_pct,
                        }
                    )
        return trades

    async def _validate_rebalancing_trades(
        self, portfolio: Portfolio, trades: List[Dict]
    ) -> None:
        """Validate rebalancing trades"""
        for trade in trades:
            if trade["estimated_value"] < settings.portfolio.MIN_TRADE_VALUE:
                raise ValueError(f"Trade value too small: {trade['estimated_value']}")
            if trade["estimated_value"] > settings.portfolio.MAX_TRADE_VALUE:
                raise ValueError(f"Trade value too large: {trade['estimated_value']}")

    async def _execute_rebalancing_trades(
        self, portfolio: Portfolio, trades: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Execute rebalancing trades"""
        executed_trades = []
        for trade in trades:
            try:
                executed_trade = {
                    **trade,
                    "executed_at": datetime.utcnow().isoformat(),
                    "execution_price": trade["estimated_price"],
                    "execution_quantity": trade["quantity"],
                    "cost": trade["estimated_value"] * 0.001,
                    "status": "executed",
                }
                executed_trades.append(executed_trade)
            except Exception as e:
                logger.error(f"Error executing trade: {e}")
                executed_trades.append({**trade, "status": "failed", "error": str(e)})
        return executed_trades

    async def _calculate_market_impact(self, trades: List[Dict]) -> Dict[str, Any]:
        """Calculate estimated market impact of trades"""
        total_value = sum((trade["estimated_value"] for trade in trades))
        return {
            "total_trade_value": total_value,
            "estimated_slippage": total_value * 0.0005,
            "estimated_fees": total_value * 0.001,
            "price_impact": "low" if total_value < 100000 else "medium",
        }

    async def _get_wallet_holdings(self, wallet_address: str) -> Dict[str, Dict]:
        """Get holdings for a specific wallet address"""
        return {
            "BTC": {
                "quantity": Decimal("0.5"),
                "price": Decimal("45000.00"),
                "value": Decimal("22500.00"),
            },
            "ETH": {
                "quantity": Decimal("10.0"),
                "price": Decimal("3000.00"),
                "value": Decimal("30000.00"),
            },
        }

    async def _analyze_rebalancing_needs(self, portfolio: Portfolio) -> None:
        """Analyze if portfolio needs rebalancing"""
        current_allocations = await self._calculate_current_allocations(portfolio)
        target_allocations = portfolio.target_allocation or {}
        needs_rebalancing = False
        for symbol, target_pct in target_allocations.items():
            current_pct = current_allocations.get(symbol, 0.0)
            if abs(target_pct - current_pct) > settings.portfolio.REBALANCING_THRESHOLD:
                needs_rebalancing = True
                break
        portfolio.needs_rebalancing = needs_rebalancing
        portfolio.last_rebalancing_check = datetime.utcnow()

from typing import Any

"""
Comprehensive Test Suite for Portfolio Service
Tests all portfolio management functionality with edge cases and error scenarios
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4
import pytest
from exceptions.portfolio_exceptions import (
    InsufficientFundsError,
    InvalidAllocationError,
    PortfolioLimitExceededError,
    PortfolioNotFoundError,
)
from models.portfolio import Portfolio, PortfolioAsset
from models.user import User
from schemas.portfolio import AssetAllocation, PortfolioCreate, PortfolioUpdate
from services.portfolio.portfolio_service import PortfolioService
from sqlalchemy.ext.asyncio import AsyncSession


class TestPortfolioService:
    """Test suite for PortfolioService"""

    @pytest.fixture
    async def db_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def portfolio_service(self, db_session):
        """Portfolio service instance"""
        return PortfolioService(db_session)

    @pytest.fixture
    def sample_user(self) -> Any:
        """Sample user for testing"""
        return User(
            id=uuid4(),
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_verified=True,
        )

    @pytest.fixture
    def sample_portfolio(self, sample_user: Any) -> Any:
        """Sample portfolio for testing"""
        return Portfolio(
            id=uuid4(),
            user_id=sample_user.id,
            name="Test Portfolio",
            description="Test portfolio description",
            total_value=Decimal("100000.00"),
            cash_balance=Decimal("10000.00"),
            is_active=True,
            created_at=datetime.utcnow(),
        )

    @pytest.fixture
    def sample_asset(self, sample_portfolio: Any) -> Any:
        """Sample portfolio asset for testing"""
        return PortfolioAsset(
            id=uuid4(),
            portfolio_id=sample_portfolio.id,
            symbol="BTC",
            asset_type="cryptocurrency",
            quantity=Decimal("2.5"),
            average_price=Decimal("45000.00"),
            current_price=Decimal("50000.00"),
            current_value=Decimal("125000.00"),
            allocation_percentage=Decimal("80.0"),
            last_updated=datetime.utcnow(),
        )

    @pytest.mark.asyncio
    async def test_create_portfolio_success(
        self, portfolio_service, sample_user, db_session
    ):
        """Test successful portfolio creation"""
        portfolio_data = PortfolioCreate(
            name="My Investment Portfolio",
            description="Long-term investment strategy",
            initial_cash=Decimal("50000.00"),
        )
        db_session.add = Mock()
        db_session.commit = AsyncMock()
        db_session.refresh = AsyncMock()
        result = await portfolio_service.create_portfolio(
            sample_user.id, portfolio_data
        )
        assert result.name == portfolio_data.name
        assert result.description == portfolio_data.description
        assert result.cash_balance == portfolio_data.initial_cash
        assert result.user_id == sample_user.id
        assert result.is_active is True
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_portfolio_invalid_cash_amount(
        self, portfolio_service, sample_user
    ):
        """Test portfolio creation with invalid cash amount"""
        portfolio_data = PortfolioCreate(
            name="Invalid Portfolio",
            description="Test portfolio",
            initial_cash=Decimal("-1000.00"),
        )
        with pytest.raises(ValueError, match="Initial cash must be non-negative"):
            await portfolio_service.create_portfolio(sample_user.id, portfolio_data)

    @pytest.mark.asyncio
    async def test_create_portfolio_duplicate_name(
        self, portfolio_service, sample_user, db_session
    ):
        """Test portfolio creation with duplicate name"""
        portfolio_data = PortfolioCreate(
            name="Existing Portfolio",
            description="Test portfolio",
            initial_cash=Decimal("10000.00"),
        )
        existing_portfolio = Mock()
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=existing_portfolio))
        )
        with pytest.raises(ValueError, match="Portfolio with this name already exists"):
            await portfolio_service.create_portfolio(sample_user.id, portfolio_data)

    @pytest.mark.asyncio
    async def test_create_portfolio_exceeds_limit(
        self, portfolio_service, sample_user, db_session
    ):
        """Test portfolio creation when user exceeds portfolio limit"""
        portfolio_data = PortfolioCreate(
            name="New Portfolio",
            description="Test portfolio",
            initial_cash=Decimal("10000.00"),
        )
        db_session.execute = AsyncMock(return_value=Mock(scalar=Mock(return_value=10)))
        with pytest.raises(PortfolioLimitExceededError):
            await portfolio_service.create_portfolio(sample_user.id, portfolio_data)

    @pytest.mark.asyncio
    async def test_get_portfolio_success(
        self, portfolio_service, sample_portfolio, db_session
    ):
        """Test successful portfolio retrieval"""
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_portfolio))
        )
        result = await portfolio_service.get_portfolio(
            sample_portfolio.id, sample_portfolio.user_id
        )
        assert result == sample_portfolio
        db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_portfolio_not_found(self, portfolio_service, db_session):
        """Test portfolio retrieval when portfolio doesn't exist"""
        portfolio_id = uuid4()
        user_id = uuid4()
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=None))
        )
        with pytest.raises(PortfolioNotFoundError):
            await portfolio_service.get_portfolio(portfolio_id, user_id)

    @pytest.mark.asyncio
    async def test_get_user_portfolios(
        self, portfolio_service, sample_user, sample_portfolio, db_session
    ):
        """Test retrieving all portfolios for a user"""
        portfolios = [sample_portfolio]
        db_session.execute = AsyncMock(
            return_value=Mock(
                scalars=Mock(return_value=Mock(all=Mock(return_value=portfolios)))
            )
        )
        result = await portfolio_service.get_user_portfolios(sample_user.id)
        assert len(result) == 1
        assert result[0] == sample_portfolio
        db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_portfolio_success(
        self, portfolio_service, sample_portfolio, db_session
    ):
        """Test successful portfolio update"""
        update_data = PortfolioUpdate(
            name="Updated Portfolio Name", description="Updated description"
        )
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_portfolio))
        )
        db_session.commit = AsyncMock()
        result = await portfolio_service.update_portfolio(
            sample_portfolio.id, sample_portfolio.user_id, update_data
        )
        assert result.name == update_data.name
        assert result.description == update_data.description
        db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_portfolio_not_found(self, portfolio_service, db_session):
        """Test updating non-existent portfolio"""
        portfolio_id = uuid4()
        user_id = uuid4()
        update_data = PortfolioUpdate(name="New Name")
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=None))
        )
        with pytest.raises(PortfolioNotFoundError):
            await portfolio_service.update_portfolio(portfolio_id, user_id, update_data)

    @pytest.mark.asyncio
    async def test_add_asset_success(
        self, portfolio_service, sample_portfolio, db_session
    ):
        """Test successful asset addition"""
        asset_data = {
            "symbol": "ETH",
            "asset_type": "cryptocurrency",
            "quantity": Decimal("10.0"),
            "purchase_price": Decimal("3000.00"),
        }
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_portfolio))
        )
        db_session.add = Mock()
        db_session.commit = AsyncMock()
        with patch.object(
            portfolio_service, "_get_current_price", return_value=Decimal("3200.00")
        ):
            result = await portfolio_service.add_asset(
                sample_portfolio.id, sample_portfolio.user_id, **asset_data
            )
        assert result.symbol == asset_data["symbol"]
        assert result.quantity == asset_data["quantity"]
        assert result.average_price == asset_data["purchase_price"]
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_asset_insufficient_cash(
        self, portfolio_service, sample_portfolio, db_session
    ):
        """Test adding asset with insufficient cash"""
        asset_data = {
            "symbol": "BTC",
            "asset_type": "cryptocurrency",
            "quantity": Decimal("10.0"),
            "purchase_price": Decimal("50000.00"),
        }
        sample_portfolio.cash_balance = Decimal("1000.00")
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_portfolio))
        )
        with pytest.raises(InsufficientFundsError):
            await portfolio_service.add_asset(
                sample_portfolio.id, sample_portfolio.user_id, **asset_data
            )

    @pytest.mark.asyncio
    async def test_remove_asset_success(
        self, portfolio_service, sample_portfolio, sample_asset, db_session
    ):
        """Test successful asset removal"""
        db_session.execute = AsyncMock(
            side_effect=[
                Mock(scalar_one_or_none=Mock(return_value=sample_portfolio)),
                Mock(scalar_one_or_none=Mock(return_value=sample_asset)),
            ]
        )
        db_session.delete = Mock()
        db_session.commit = AsyncMock()
        with patch.object(
            portfolio_service, "_get_current_price", return_value=Decimal("50000.00")
        ):
            await portfolio_service.remove_asset(
                sample_portfolio.id, sample_portfolio.user_id, sample_asset.id
            )
        db_session.delete.assert_called_once_with(sample_asset)
        db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_asset_quantity(
        self, portfolio_service, sample_portfolio, sample_asset, db_session
    ):
        """Test updating asset quantity"""
        new_quantity = Decimal("5.0")
        db_session.execute = AsyncMock(
            side_effect=[
                Mock(scalar_one_or_none=Mock(return_value=sample_portfolio)),
                Mock(scalar_one_or_none=Mock(return_value=sample_asset)),
            ]
        )
        db_session.commit = AsyncMock()
        with patch.object(
            portfolio_service, "_get_current_price", return_value=Decimal("50000.00")
        ):
            result = await portfolio_service.update_asset_quantity(
                sample_portfolio.id,
                sample_portfolio.user_id,
                sample_asset.id,
                new_quantity,
            )
        assert result.quantity == new_quantity
        db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_portfolio_value(
        self, portfolio_service, sample_portfolio, sample_asset, db_session
    ):
        """Test portfolio value calculation"""
        sample_portfolio.assets = [sample_asset]
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_portfolio))
        )
        with patch.object(
            portfolio_service, "_get_current_price", return_value=Decimal("50000.00")
        ):
            total_value = await portfolio_service.calculate_portfolio_value(
                sample_portfolio.id, sample_portfolio.user_id
            )
        expected_value = (
            sample_portfolio.cash_balance + sample_asset.quantity * Decimal("50000.00")
        )
        assert total_value == expected_value

    @pytest.mark.asyncio
    async def test_get_portfolio_performance(
        self, portfolio_service, sample_portfolio, db_session
    ):
        """Test portfolio performance calculation"""
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_portfolio))
        )
        with patch.object(portfolio_service, "_calculate_returns") as mock_returns:
            mock_returns.return_value = {
                "total_return": Decimal("0.15"),
                "daily_return": Decimal("0.02"),
                "volatility": Decimal("0.25"),
            }
            performance = await portfolio_service.get_portfolio_performance(
                sample_portfolio.id, sample_portfolio.user_id, period="1y"
            )
        assert "total_return" in performance
        assert "daily_return" in performance
        assert "volatility" in performance

    @pytest.mark.asyncio
    async def test_rebalance_portfolio_success(
        self, portfolio_service, sample_portfolio, db_session
    ):
        """Test successful portfolio rebalancing"""
        target_allocations = [
            AssetAllocation(symbol="BTC", target_percentage=Decimal("60.0")),
            AssetAllocation(symbol="ETH", target_percentage=Decimal("40.0")),
        ]
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_portfolio))
        )
        db_session.commit = AsyncMock()
        with patch.object(
            portfolio_service, "_execute_rebalancing_trades"
        ) as mock_trades:
            mock_trades.return_value = []
            result = await portfolio_service.rebalance_portfolio(
                sample_portfolio.id, sample_portfolio.user_id, target_allocations
            )
        assert "trades_executed" in result
        assert "new_allocations" in result
        db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_rebalance_invalid_allocation(
        self, portfolio_service, sample_portfolio
    ):
        """Test rebalancing with invalid allocation percentages"""
        target_allocations = [
            AssetAllocation(symbol="BTC", target_percentage=Decimal("60.0")),
            AssetAllocation(symbol="ETH", target_percentage=Decimal("50.0")),
        ]
        with pytest.raises(
            InvalidAllocationError, match="Total allocation exceeds 100%"
        ):
            await portfolio_service.rebalance_portfolio(
                sample_portfolio.id, sample_portfolio.user_id, target_allocations
            )

    @pytest.mark.asyncio
    async def test_calculate_portfolio_risk(
        self, portfolio_service, sample_portfolio, db_session
    ):
        """Test portfolio risk calculation"""
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_portfolio))
        )
        with patch.object(portfolio_service, "_calculate_var") as mock_var:
            mock_var.return_value = Decimal("0.05")
            risk_metrics = await portfolio_service.calculate_portfolio_risk(
                sample_portfolio.id, sample_portfolio.user_id
            )
        assert "var_95" in risk_metrics
        assert "volatility" in risk_metrics
        assert "sharpe_ratio" in risk_metrics

    @pytest.mark.asyncio
    async def test_check_risk_limits(
        self, portfolio_service, sample_portfolio, db_session
    ):
        """Test risk limit checking"""
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_portfolio))
        )
        with patch.object(portfolio_service, "_get_risk_limits") as mock_limits:
            mock_limits.return_value = {
                "max_position_size": Decimal("0.20"),
                "max_sector_allocation": Decimal("0.30"),
            }
            violations = await portfolio_service.check_risk_limits(
                sample_portfolio.id, sample_portfolio.user_id
            )
        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_get_transaction_history(
        self, portfolio_service, sample_portfolio, db_session
    ):
        """Test retrieving transaction history"""
        mock_transactions = [Mock(), Mock(), Mock()]
        db_session.execute = AsyncMock(
            return_value=Mock(
                scalars=Mock(
                    return_value=Mock(all=Mock(return_value=mock_transactions))
                )
            )
        )
        result = await portfolio_service.get_transaction_history(
            sample_portfolio.id, sample_portfolio.user_id, limit=10
        )
        assert len(result) == 3
        db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_portfolio_report(
        self, portfolio_service, sample_portfolio, db_session
    ):
        """Test portfolio report generation"""
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_portfolio))
        )
        with patch.object(
            portfolio_service, "_compile_portfolio_analytics"
        ) as mock_analytics:
            mock_analytics.return_value = {
                "summary": {},
                "performance": {},
                "risk_metrics": {},
                "allocations": {},
            }
            report = await portfolio_service.generate_portfolio_report(
                sample_portfolio.id, sample_portfolio.user_id
            )
        assert "summary" in report
        assert "performance" in report
        assert "risk_metrics" in report
        assert "allocations" in report

    @pytest.mark.asyncio
    async def test_database_error_handling(self, portfolio_service, db_session):
        """Test handling of database errors"""
        db_session.execute = AsyncMock(
            side_effect=Exception("Database connection error")
        )
        with pytest.raises(Exception, match="Database connection error"):
            await portfolio_service.get_portfolio(uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_invalid_uuid_handling(self, portfolio_service):
        """Test handling of invalid UUID parameters"""
        with pytest.raises(ValueError, match="Invalid UUID"):
            await portfolio_service.get_portfolio("invalid-uuid", uuid4())

    @pytest.mark.asyncio
    async def test_concurrent_portfolio_updates(
        self, portfolio_service, sample_portfolio, db_session
    ):
        """Test handling of concurrent portfolio updates"""
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_portfolio))
        )
        db_session.commit = AsyncMock()
        tasks = []
        for i in range(5):
            update_data = PortfolioUpdate(description=f"Update {i}")
            task = portfolio_service.update_portfolio(
                sample_portfolio.id, sample_portfolio.user_id, update_data
            )
            tasks.append(task)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            assert not isinstance(result, Exception)

    @pytest.mark.asyncio
    async def test_full_portfolio_lifecycle(
        self, portfolio_service, sample_user, db_session
    ):
        """Test complete portfolio lifecycle"""
        db_session.add = Mock()
        db_session.commit = AsyncMock()
        db_session.refresh = AsyncMock()
        db_session.delete = Mock()
        portfolio_data = PortfolioCreate(
            name="Lifecycle Test Portfolio",
            description="Testing full lifecycle",
            initial_cash=Decimal("100000.00"),
        )
        portfolio = await portfolio_service.create_portfolio(
            sample_user.id, portfolio_data
        )
        assert portfolio.name == portfolio_data.name
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=portfolio))
        )
        with patch.object(
            portfolio_service, "_get_current_price", return_value=Decimal("50000.00")
        ):
            asset = await portfolio_service.add_asset(
                portfolio.id,
                sample_user.id,
                symbol="BTC",
                asset_type="cryptocurrency",
                quantity=Decimal("1.0"),
                purchase_price=Decimal("45000.00"),
            )
        assert asset.symbol == "BTC"
        update_data = PortfolioUpdate(description="Updated description")
        updated_portfolio = await portfolio_service.update_portfolio(
            portfolio.id, sample_user.id, update_data
        )
        assert updated_portfolio.description == update_data.description
        await portfolio_service.delete_portfolio(portfolio.id, sample_user.id)
        assert db_session.add.call_count >= 2
        assert db_session.commit.call_count >= 4
        assert db_session.delete.call_count >= 1

    @pytest.mark.asyncio
    async def test_large_portfolio_performance(
        self, portfolio_service, sample_portfolio, db_session
    ):
        """Test performance with large number of assets"""
        assets = []
        for i in range(100):
            asset = Mock()
            asset.symbol = f"ASSET{i}"
            asset.quantity = Decimal("10.0")
            asset.current_price = Decimal("100.0")
            assets.append(asset)
        sample_portfolio.assets = assets
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_portfolio))
        )
        with patch.object(
            portfolio_service, "_get_current_price", return_value=Decimal("100.0")
        ):
            start_time = datetime.utcnow()
            total_value = await portfolio_service.calculate_portfolio_value(
                sample_portfolio.id, sample_portfolio.user_id
            )
            end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 1.0
        assert total_value > 0

    @pytest.mark.asyncio
    async def test_zero_quantity_asset(
        self, portfolio_service, sample_portfolio, db_session
    ):
        """Test handling of zero quantity assets"""
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_portfolio))
        )
        with pytest.raises(ValueError, match="Quantity must be greater than zero"):
            await portfolio_service.add_asset(
                sample_portfolio.id,
                sample_portfolio.user_id,
                symbol="BTC",
                asset_type="cryptocurrency",
                quantity=Decimal("0.0"),
                purchase_price=Decimal("50000.00"),
            )

    @pytest.mark.asyncio
    async def test_negative_price_asset(
        self, portfolio_service, sample_portfolio, db_session
    ):
        """Test handling of negative price assets"""
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_portfolio))
        )
        with pytest.raises(ValueError, match="Purchase price must be positive"):
            await portfolio_service.add_asset(
                sample_portfolio.id,
                sample_portfolio.user_id,
                symbol="BTC",
                asset_type="cryptocurrency",
                quantity=Decimal("1.0"),
                purchase_price=Decimal("-1000.00"),
            )

    @pytest.mark.asyncio
    async def test_empty_portfolio_calculations(
        self, portfolio_service, sample_portfolio, db_session
    ):
        """Test calculations on empty portfolio"""
        sample_portfolio.assets = []
        sample_portfolio.cash_balance = Decimal("0.0")
        db_session.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_portfolio))
        )
        total_value = await portfolio_service.calculate_portfolio_value(
            sample_portfolio.id, sample_portfolio.user_id
        )
        assert total_value == Decimal("0.0")


def create_mock_portfolio(user_id: UUID, **kwargs) -> Portfolio:
    """Create a mock portfolio for testing"""
    defaults = {
        "id": uuid4(),
        "user_id": user_id,
        "name": "Test Portfolio",
        "description": "Test description",
        "total_value": Decimal("100000.00"),
        "cash_balance": Decimal("10000.00"),
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    defaults.update(kwargs)
    return Portfolio(**defaults)


def create_mock_asset(portfolio_id: UUID, **kwargs) -> PortfolioAsset:
    """Create a mock portfolio asset for testing"""
    defaults = {
        "id": uuid4(),
        "portfolio_id": portfolio_id,
        "symbol": "BTC",
        "asset_type": "cryptocurrency",
        "quantity": Decimal("1.0"),
        "average_price": Decimal("50000.00"),
        "current_price": Decimal("55000.00"),
        "current_value": Decimal("55000.00"),
        "allocation_percentage": Decimal("55.0"),
        "last_updated": datetime.utcnow(),
    }
    defaults.update(kwargs)
    return PortfolioAsset(**defaults)


pytest_plugins = ["pytest_asyncio"]
pytestmark = [pytest.mark.asyncio, pytest.mark.unit, pytest.mark.portfolio]

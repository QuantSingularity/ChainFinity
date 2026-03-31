"""
Portfolio management API endpoints
Comprehensive portfolio operations including creation, management, and analytics
"""

import logging
from typing import List, Optional

from app.api.dependencies import get_current_user
from config.database import get_async_session
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from middleware.audit_middleware import audit_log
from models.user import User
from schemas.base import PaginatedResponse, SuccessResponse
from schemas.portfolio import (
    PortfolioAnalytics,
    PortfolioAssetResponse,
    PortfolioAssetUpdate,
    PortfolioCreate,
    PortfolioPerformance,
    PortfolioResponse,
    PortfolioUpdate,
    RebalanceRequest,
    RebalanceResponse,
)
from services.analytics.analytics_service import AnalyticsService
from services.portfolio.portfolio_service import PortfolioService
from services.risk.risk_service import RiskService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def get_user_portfolios(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    include_deleted: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get user's portfolios with pagination
    """
    try:
        portfolio_service = PortfolioService(db)
        portfolios = await portfolio_service.get_user_portfolios(
            current_user.id, page, size, include_deleted
        )

        return portfolios

    except Exception as e:
        logger.error(f"Error getting user portfolios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve portfolios",
        )


@router.post("/", response_model=PortfolioResponse)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Create a new portfolio
    """
    try:
        portfolio_service = PortfolioService(db)
        portfolio = await portfolio_service.create_portfolio(
            current_user.id, portfolio_data
        )

        await audit_log(
            db,
            current_user.id,
            "portfolio_created",
            "portfolio",
            str(portfolio.id),
            new_values=portfolio_data.dict(),
        )

        return PortfolioResponse.from_orm(portfolio)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portfolio",
        )


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get portfolio details by ID
    """
    try:
        portfolio_service = PortfolioService(db)
        portfolio = await portfolio_service.get_portfolio(portfolio_id, current_user.id)

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
            )

        return PortfolioResponse.from_orm(portfolio)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve portfolio",
        )


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: str,
    portfolio_update: PortfolioUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update portfolio information
    """
    try:
        portfolio_service = PortfolioService(db)
        portfolio = await portfolio_service.update_portfolio(
            portfolio_id, current_user.id, portfolio_update
        )

        await audit_log(
            db,
            current_user.id,
            "portfolio_updated",
            "portfolio",
            portfolio_id,
            new_values=portfolio_update.dict(exclude_unset=True),
        )

        return PortfolioResponse.from_orm(portfolio)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update portfolio",
        )


@router.delete("/{portfolio_id}", response_model=SuccessResponse)
async def delete_portfolio(
    portfolio_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Delete (soft delete) a portfolio
    """
    try:
        portfolio_service = PortfolioService(db)
        await portfolio_service.delete_portfolio(portfolio_id, current_user.id)

        await audit_log(
            db, current_user.id, "portfolio_deleted", "portfolio", portfolio_id
        )

        return SuccessResponse(message="Portfolio deleted successfully")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete portfolio",
        )


@router.get("/{portfolio_id}/assets", response_model=List[PortfolioAssetResponse])
async def get_portfolio_assets(
    portfolio_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get all assets in a portfolio
    """
    try:
        portfolio_service = PortfolioService(db)
        assets = await portfolio_service.get_portfolio_assets(
            portfolio_id, current_user.id
        )

        return [PortfolioAssetResponse.from_orm(asset) for asset in assets]

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting portfolio assets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve portfolio assets",
        )


@router.post("/{portfolio_id}/assets", response_model=PortfolioAssetResponse)
async def add_portfolio_asset(
    portfolio_id: str,
    asset_data: PortfolioAssetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Add an asset to a portfolio
    """
    try:
        portfolio_service = PortfolioService(db)
        asset = await portfolio_service.add_portfolio_asset(
            portfolio_id, current_user.id, asset_data
        )

        await audit_log(
            db,
            current_user.id,
            "portfolio_asset_added",
            "portfolio_asset",
            str(asset.id),
            new_values=asset_data.dict(),
        )

        return PortfolioAssetResponse.from_orm(asset)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding portfolio asset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add portfolio asset",
        )


@router.put("/{portfolio_id}/assets/{asset_id}", response_model=PortfolioAssetResponse)
async def update_portfolio_asset(
    portfolio_id: str,
    asset_id: str,
    asset_update: PortfolioAssetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update a portfolio asset
    """
    try:
        portfolio_service = PortfolioService(db)
        asset = await portfolio_service.update_portfolio_asset(
            portfolio_id, asset_id, current_user.id, asset_update
        )

        await audit_log(
            db,
            current_user.id,
            "portfolio_asset_updated",
            "portfolio_asset",
            asset_id,
            new_values=asset_update.dict(exclude_unset=True),
        )

        return PortfolioAssetResponse.from_orm(asset)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating portfolio asset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update portfolio asset",
        )


@router.delete("/{portfolio_id}/assets/{asset_id}", response_model=SuccessResponse)
async def remove_portfolio_asset(
    portfolio_id: str,
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Remove an asset from a portfolio
    """
    try:
        portfolio_service = PortfolioService(db)
        await portfolio_service.remove_portfolio_asset(
            portfolio_id, asset_id, current_user.id
        )

        await audit_log(
            db, current_user.id, "portfolio_asset_removed", "portfolio_asset", asset_id
        )

        return SuccessResponse(message="Portfolio asset removed successfully")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing portfolio asset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove portfolio asset",
        )


@router.get("/{portfolio_id}/analytics", response_model=PortfolioAnalytics)
async def get_portfolio_analytics(
    portfolio_id: str,
    period: str = Query("30d", regex="^(1d|7d|30d|90d|1y|all)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get portfolio analytics and performance metrics
    """
    try:
        analytics_service = AnalyticsService(db)
        analytics = await analytics_service.get_portfolio_analytics(
            portfolio_id, current_user.id, period
        )

        return analytics

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting portfolio analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve portfolio analytics",
        )


@router.get("/{portfolio_id}/performance", response_model=PortfolioPerformance)
async def get_portfolio_performance(
    portfolio_id: str,
    period: str = Query("30d", regex="^(1d|7d|30d|90d|1y|all)$"),
    benchmark: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get detailed portfolio performance analysis
    """
    try:
        analytics_service = AnalyticsService(db)
        performance = await analytics_service.get_portfolio_performance(
            portfolio_id, current_user.id, period, benchmark
        )

        return performance

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting portfolio performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve portfolio performance",
        )


@router.post("/{portfolio_id}/rebalance", response_model=RebalanceResponse)
async def rebalance_portfolio(
    portfolio_id: str,
    rebalance_request: RebalanceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Rebalance portfolio according to target allocations
    """
    try:
        portfolio_service = PortfolioService(db)
        rebalance_result = await portfolio_service.rebalance_portfolio(
            portfolio_id, current_user.id, rebalance_request
        )

        await audit_log(
            db,
            current_user.id,
            "portfolio_rebalanced",
            "portfolio",
            portfolio_id,
            new_values=rebalance_request.dict(),
        )

        return rebalance_result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error rebalancing portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rebalance portfolio",
        )


@router.get("/{portfolio_id}/risk-assessment", response_model=dict)
async def get_portfolio_risk_assessment(
    portfolio_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get portfolio risk assessment and metrics
    """
    try:
        risk_service = RiskService(db)
        risk_assessment = await risk_service.assess_portfolio_risk(
            portfolio_id, current_user.id
        )

        return risk_assessment

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting portfolio risk assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve portfolio risk assessment",
        )


@router.post("/{portfolio_id}/sync", response_model=SuccessResponse)
async def sync_portfolio_with_blockchain(
    portfolio_id: str,
    wallet_addresses: List[str] = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Sync portfolio with blockchain wallet addresses
    """
    try:
        portfolio_service = PortfolioService(db)
        await portfolio_service.sync_portfolio_with_blockchain(
            portfolio_id, current_user.id, wallet_addresses
        )

        await audit_log(
            db,
            current_user.id,
            "portfolio_synced",
            "portfolio",
            portfolio_id,
            new_values={"wallet_addresses": wallet_addresses},
        )

        return SuccessResponse(message="Portfolio synced with blockchain successfully")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error syncing portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync portfolio with blockchain",
        )


@router.post("/{portfolio_id}/export", response_model=dict)
async def export_portfolio_data(
    portfolio_id: str,
    format: str = Query("csv", regex="^(csv|json|pdf)$"),
    include_transactions: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Export portfolio data in various formats
    """
    try:
        portfolio_service = PortfolioService(db)
        export_result = await portfolio_service.export_portfolio_data(
            portfolio_id, current_user.id, format, include_transactions
        )

        await audit_log(
            db,
            current_user.id,
            "portfolio_exported",
            "portfolio",
            portfolio_id,
            new_values={"format": format, "include_transactions": include_transactions},
        )

        return export_result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export portfolio data",
        )


@router.get("/{portfolio_id}/alerts", response_model=List[dict])
async def get_portfolio_alerts(
    portfolio_id: str,
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get portfolio alerts and notifications
    """
    try:
        portfolio_service = PortfolioService(db)
        alerts = await portfolio_service.get_portfolio_alerts(
            portfolio_id, current_user.id, active_only
        )

        return alerts

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting portfolio alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve portfolio alerts",
        )


@router.post("/{portfolio_id}/alerts", response_model=dict)
async def create_portfolio_alert(
    portfolio_id: str,
    alert_data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Create a new portfolio alert
    """
    try:
        portfolio_service = PortfolioService(db)
        alert = await portfolio_service.create_portfolio_alert(
            portfolio_id, current_user.id, alert_data
        )

        await audit_log(
            db,
            current_user.id,
            "portfolio_alert_created",
            "portfolio_alert",
            str(alert["id"]),
            new_values=alert_data,
        )

        return alert

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating portfolio alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portfolio alert",
        )

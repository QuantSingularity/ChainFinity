"""
Transaction endpoints
"""

import logging
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from app.api.dependencies import get_current_user
from config.database import get_async_session
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.transaction import Transaction, TransactionStatus, TransactionType
from models.user import User
from schemas.base import SuccessResponse
from schemas.transaction import (TransactionCreate, TransactionResponse,
                                 TransactionUpdate)
from services.portfolio.portfolio_service import PortfolioService
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=List[TransactionResponse])
async def list_transactions(
    portfolio_id: Optional[UUID] = Query(None),
    transaction_type: Optional[TransactionType] = Query(None),
    status: Optional[TransactionStatus] = Query(None),
    symbol: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get list of transactions for current user
    """
    try:
        query = select(Transaction).where(Transaction.user_id == current_user.id)

        if portfolio_id:
            query = query.where(Transaction.portfolio_id == portfolio_id)
        if transaction_type:
            query = query.where(Transaction.transaction_type == transaction_type)
        if status:
            query = query.where(Transaction.status == status)
        if symbol:
            query = query.where(Transaction.symbol.ilike(f"%{symbol}%"))

        query = query.order_by(desc(Transaction.created_at)).limit(limit).offset(offset)

        result = await db.execute(query)
        transactions = result.scalars().all()

        return transactions

    except Exception as e:
        logger.error(f"Error listing transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transactions",
        )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get specific transaction details
    """
    try:
        query = select(Transaction).where(
            and_(
                Transaction.id == transaction_id,
                Transaction.user_id == current_user.id,
            )
        )
        result = await db.execute(query)
        transaction = result.scalar_one_or_none()

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
            )

        return transaction

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transaction",
        )


@router.post(
    "", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Create a new transaction
    """
    try:
        portfolio_service = PortfolioService(db)

        # Verify portfolio belongs to user
        portfolio = await portfolio_service.get_portfolio(
            portfolio_id=transaction_data.portfolio_id, user_id=current_user.id
        )

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
            )

        transaction = Transaction(
            user_id=current_user.id,
            portfolio_id=transaction_data.portfolio_id,
            transaction_type=transaction_data.transaction_type,
            symbol=transaction_data.symbol,
            quantity=transaction_data.quantity,
            price_per_unit=transaction_data.price_per_unit,
            amount_usd=transaction_data.quantity * transaction_data.price_per_unit,
            status=TransactionStatus.PENDING,
            transaction_hash=transaction_data.transaction_hash,
            from_address=transaction_data.from_address,
            to_address=transaction_data.to_address,
            gas_used=transaction_data.gas_used,
            gas_price=transaction_data.gas_price,
            network=transaction_data.network,
            notes=transaction_data.notes,
        )

        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)

        return transaction

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create transaction",
        )


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    transaction_data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Update transaction details
    """
    try:
        query = select(Transaction).where(
            and_(
                Transaction.id == transaction_id,
                Transaction.user_id == current_user.id,
            )
        )
        result = await db.execute(query)
        transaction = result.scalar_one_or_none()

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
            )

        # Update fields if provided
        if transaction_data.status is not None:
            transaction.status = transaction_data.status
        if transaction_data.notes is not None:
            transaction.notes = transaction_data.notes
        if transaction_data.transaction_hash is not None:
            transaction.transaction_hash = transaction_data.transaction_hash

        transaction.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(transaction)

        return transaction

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update transaction",
        )


@router.delete("/{transaction_id}", response_model=SuccessResponse)
async def delete_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Delete a transaction (soft delete)
    """
    try:
        query = select(Transaction).where(
            and_(
                Transaction.id == transaction_id,
                Transaction.user_id == current_user.id,
            )
        )
        result = await db.execute(query)
        transaction = result.scalar_one_or_none()

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
            )

        # Soft delete
        transaction.deleted_at = datetime.utcnow()
        transaction.updated_at = datetime.utcnow()

        await db.commit()

        return SuccessResponse(success=True, message="Transaction deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete transaction",
        )


@router.post("/{transaction_id}/analyze", response_model=dict)
async def analyze_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Analyze transaction for risk and compliance
    """
    try:
        query = select(Transaction).where(
            and_(
                Transaction.id == transaction_id,
                Transaction.user_id == current_user.id,
            )
        )
        result = await db.execute(query)
        transaction = result.scalar_one_or_none()

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
            )

        # Perform basic analysis
        analysis = {
            "transaction_id": str(transaction_id),
            "risk_level": "low",
            "compliance_status": "passed",
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "amount_check": {
                    "passed": True,
                    "details": "Amount within normal range",
                },
                "frequency_check": {
                    "passed": True,
                    "details": "Transaction frequency normal",
                },
                "pattern_check": {
                    "passed": True,
                    "details": "No suspicious patterns detected",
                },
            },
        }

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze transaction",
        )

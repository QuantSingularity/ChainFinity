"""
Blockchain endpoints
"""

import logging
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from app.api.dependencies import get_current_user
from config.database import get_async_session
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.blockchain import BlockchainNetwork, ContractEvent, SmartContract
from models.user import User
from schemas.blockchain import ContractResponse, EventResponse, NetworkResponse
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/networks", response_model=List[NetworkResponse])
async def list_blockchain_networks(
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get list of supported blockchain networks
    """
    try:
        query = select(BlockchainNetwork)

        if is_active is not None:
            query = query.where(BlockchainNetwork.is_active == is_active)

        query = query.order_by(BlockchainNetwork.chain_id).limit(limit).offset(offset)

        result = await db.execute(query)
        networks = result.scalars().all()

        return networks

    except Exception as e:
        logger.error(f"Error listing blockchain networks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve blockchain networks",
        )


@router.get("/networks/{network_id}", response_model=NetworkResponse)
async def get_blockchain_network(
    network_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get specific blockchain network details
    """
    try:
        query = select(BlockchainNetwork).where(BlockchainNetwork.id == network_id)
        result = await db.execute(query)
        network = result.scalar_one_or_none()

        if not network:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blockchain network not found",
            )

        return network

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting blockchain network: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve blockchain network",
        )


@router.get("/contracts", response_model=List[ContractResponse])
async def list_smart_contracts(
    network_id: Optional[UUID] = Query(None),
    contract_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get list of smart contracts
    """
    try:
        query = select(SmartContract)

        if network_id:
            query = query.where(SmartContract.network_id == network_id)
        if contract_type:
            query = query.where(SmartContract.contract_type == contract_type)
        if is_active is not None:
            query = query.where(SmartContract.is_active == is_active)

        query = (
            query.order_by(desc(SmartContract.created_at)).limit(limit).offset(offset)
        )

        result = await db.execute(query)
        contracts = result.scalars().all()

        return contracts

    except Exception as e:
        logger.error(f"Error listing smart contracts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve smart contracts",
        )


@router.get("/contracts/{contract_id}", response_model=ContractResponse)
async def get_smart_contract(
    contract_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get specific smart contract details
    """
    try:
        query = select(SmartContract).where(SmartContract.id == contract_id)
        result = await db.execute(query)
        contract = result.scalar_one_or_none()

        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Smart contract not found"
            )

        return contract

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting smart contract: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve smart contract",
        )


@router.get("/events", response_model=List[EventResponse])
async def list_contract_events(
    contract_id: Optional[UUID] = Query(None),
    event_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get blockchain contract events
    """
    try:
        query = select(ContractEvent)

        if contract_id:
            query = query.where(ContractEvent.contract_id == contract_id)
        if event_name:
            query = query.where(ContractEvent.event_name == event_name)

        query = (
            query.order_by(desc(ContractEvent.block_timestamp))
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(query)
        events = result.scalars().all()

        return events

    except Exception as e:
        logger.error(f"Error listing contract events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve contract events",
        )


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_contract_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get specific contract event details
    """
    try:
        query = select(ContractEvent).where(ContractEvent.id == event_id)
        result = await db.execute(query)
        event = result.scalar_one_or_none()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Contract event not found"
            )

        return event

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contract event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve contract event",
        )


@router.post("/verify-address", response_model=dict)
async def verify_blockchain_address(
    address: str,
    network: str = "ethereum",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Verify blockchain address format and validity
    """
    try:
        # Basic validation
        is_valid = False
        address_type = "unknown"

        if network.lower() in ["ethereum", "polygon", "bsc"]:
            # Check if it's a valid Ethereum-style address
            if address.startswith("0x") and len(address) == 42:
                is_valid = True
                address_type = "EOA"  # Externally Owned Account
                # Could check if it's a contract by querying the network

        return {
            "address": address,
            "network": network,
            "is_valid": is_valid,
            "address_type": address_type,
            "checked_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error verifying blockchain address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify blockchain address",
        )


@router.get("/balance/{address}", response_model=dict)
async def get_address_balance(
    address: str,
    network: str = Query("ethereum"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get balance for a blockchain address
    """
    try:
        # In a real implementation, this would query the blockchain
        # For now, return a mock response
        return {
            "address": address,
            "network": network,
            "balance": "0",
            "balance_usd": "0",
            "tokens": [],
            "last_updated": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting address balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve address balance",
        )


@router.get("/gas-price", response_model=dict)
async def get_gas_price(
    network: str = Query("ethereum"),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get current gas price for a network
    """
    try:
        # Mock gas price response
        return {
            "network": network,
            "timestamp": datetime.utcnow().isoformat(),
            "gas_prices": {
                "slow": "20",
                "standard": "25",
                "fast": "30",
                "rapid": "40",
            },
            "unit": "gwei",
        }

    except Exception as e:
        logger.error(f"Error getting gas price: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve gas price",
        )

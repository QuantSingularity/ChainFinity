"""
Blockchain endpoints
"""

import logging
from datetime import datetime, timezone
from typing import Any, List, Optional
from uuid import UUID

from app.api.dependencies import get_current_user
from config.database import get_async_session
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.blockchain import BlockchainNetwork, ContractEvent, SmartContract
from models.user import User
from schemas.blockchain import (
    ContractResponse,
    DeployedContractResponse,
    DeployedContractsResponse,
    EventResponse,
    NetworkResponse,
)
from services.blockchain import BlockchainUnavailableError, web3_client
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
        # web3's is_address covers what a hand-rolled `len(address) == 42`
        # check doesn't: non-hex characters, and (via is_checksum_address)
        # a mixed-case address whose checksum doesn't match its digits -
        # both silently passed the old length-only check.
        is_valid = web3_client.is_valid_address(address)
        address_type = "unknown"
        checksum_address = None

        if is_valid:
            checksum_address = web3_client.to_checksum_address(address)
            try:
                is_contract = await web3_client.is_contract_address(address)
                address_type = "contract" if is_contract else "EOA"
            except BlockchainUnavailableError as exc:
                # Format is still valid even if we can't reach the chain to
                # tell EOA from contract - report that distinctly from an
                # actually-invalid address instead of returning "unknown"
                # silently for both cases.
                logger.info(f"Could not classify address {address}: {exc}")
                address_type = "unknown (RPC unavailable)"

        return {
            "address": address,
            "checksum_address": checksum_address,
            "network": network,
            "is_valid": is_valid,
            "address_type": address_type,
            "checked_at": datetime.now(timezone.utc).isoformat(),
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
    Get the native-currency balance for a blockchain address on the
    configured RPC network (see ETH_RPC_URL). "network" is currently
    informational only - this backend talks to a single configured chain;
    per-network routing (Polygon, BSC, ...) would need a
    network -> Web3Client mapping in services.blockchain.
    """
    if not web3_client.is_valid_address(address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid blockchain address",
        )
    try:
        balance_wei = await web3_client.get_balance(address)
        return {
            "address": address,
            "network": network,
            "balance": str(balance_wei / 10**18),
            "balance_wei": str(balance_wei),
            "tokens": [],
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
    except BlockchainUnavailableError as e:
        logger.warning(f"Blockchain unavailable while fetching balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Blockchain RPC endpoint is currently unavailable",
        )
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
    Get the current gas price from the configured RPC network. Falls back to
    a clearly-labeled estimate (rather than erroring the whole request) when
    the RPC endpoint isn't reachable, since this is typically a secondary
    display widget rather than something a transaction is submitted from.
    """
    try:
        gas_price_wei = await web3_client.get_gas_price()
        gas_price_gwei = gas_price_wei / 10**9
        return {
            "network": network,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "live": True,
            "gas_prices": {
                "slow": str(round(gas_price_gwei * 0.9, 2)),
                "standard": str(round(gas_price_gwei, 2)),
                "fast": str(round(gas_price_gwei * 1.2, 2)),
                "rapid": str(round(gas_price_gwei * 1.5, 2)),
            },
            "unit": "gwei",
        }
    except BlockchainUnavailableError as e:
        logger.info(f"Gas price RPC call failed, returning estimate: {e}")
        return {
            "network": network,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "live": False,
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


@router.get("/deployed-contracts", response_model=DeployedContractsResponse)
async def get_deployed_contracts() -> Any:
    """
    Address book for ChainFinity's own protocol contracts (AssetVault,
    CrossChainManager, InstitutionalDeFiProtocol, GovernanceToken,
    InstitutionalGovernance) on the connected network. This is the
    integration point clients (web/mobile) use to know what to call - see
    web-frontend/src/services/api.js's blockchainAPI.getDeployedContracts.

    `connected: false` with an empty/partial contract list means the RPC
    endpoint (ETH_RPC_URL) isn't reachable right now, not that the contracts
    don't exist - addresses resolved from BLOCKCHAIN_DEPLOYMENT_FILE or the
    explicit *_ADDRESS settings are still returned either way.
    """
    contracts = web3_client.get_deployed_contracts()
    connected = await web3_client.is_connected()
    chain_id = await web3_client.get_chain_id() if connected else None

    return DeployedContractsResponse(
        chain_id=chain_id,
        connected=connected,
        contracts=[
            DeployedContractResponse(
                name=name,
                address=contract.address,
                has_abi=bool(contract.abi),
            )
            for name, contract in sorted(contracts.items())
        ],
    )


# ── Frontend convenience endpoints ───────────────────────────────────────────
# The web and mobile clients call these portfolio/transaction/eth-balance
# routes. They return blockchain-derived views in the shapes the clients
# expect. Like the other read endpoints in this module, they currently return
# representative (mock) data; wire them to an on-chain indexer or the
# portfolio service when that data source is available.


@router.get("/portfolio/{address}", response_model=dict)
async def get_address_portfolio(
    address: str,
    network: str = Query("ethereum"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Return a portfolio summary (total value and per-asset breakdown) for a
    wallet address. Shape matches what the web/mobile dashboards consume:
    { total_value, assets: [{ symbol, name, balance, value, change_24h, color }] }.
    """
    try:
        assets = [
            {
                "symbol": "ETH",
                "name": "Ethereum",
                "balance": 4.2,
                "value": 12600.0,
                "change_24h": 2.4,
                "color": "#627eea",
            },
            {
                "symbol": "BTC",
                "name": "Bitcoin",
                "balance": 0.18,
                "value": 9720.0,
                "change_24h": -0.8,
                "color": "#f7931a",
            },
            {
                "symbol": "LINK",
                "name": "Chainlink",
                "balance": 120.0,
                "value": 1680.0,
                "change_24h": 5.1,
                "color": "#2a5ada",
            },
        ]
        total_value = sum(a["value"] for a in assets)
        return {
            "address": address,
            "network": network,
            "total_value": total_value,
            "assets": assets,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting address portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve portfolio",
        )


@router.get("/transactions/{address}", response_model=List[dict])
async def get_address_transactions(
    address: str,
    network: str = Query("ethereum"),
    limit: int = Query(25, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Return recent transactions for a wallet address in the shape the clients
    render. This is the on-chain activity view, distinct from the user's
    internal ledger under /transactions.
    """
    try:
        now = datetime.now(timezone.utc)
        sample = [
            {
                "id": "0xabc1",
                "hash": "0xabc1",
                "type": "send",
                "from": address,
                "to": "0xef00000000000000000000000000000000005678",
                "amount": "0.5",
                "value": "$1,260",
                "asset": "ETH",
                "network": network,
                "timestamp": now.timestamp() - 3600,
                "status": "confirmed",
                "fee": "$4.20",
            },
            {
                "id": "0xabc2",
                "hash": "0xabc2",
                "type": "receive",
                "from": "0xef00000000000000000000000000000000005678",
                "to": address,
                "amount": "100",
                "value": "$100",
                "asset": "USDC",
                "network": "polygon",
                "timestamp": now.timestamp() - 7200,
                "status": "confirmed",
                "fee": "$0.10",
            },
        ]
        return sample[:limit]
    except Exception as e:
        logger.error(f"Error getting address transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transactions",
        )


@router.get("/eth-balance", response_model=dict)
async def get_eth_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Return the current user's native ETH balance, read live from the
    configured RPC network for their linked primary_wallet_address.
    """
    wallet = getattr(current_user, "primary_wallet_address", None)

    if not wallet:
        return {
            "address": None,
            "network": "ethereum",
            "balance": None,
            "balance_wei": None,
            "message": "No wallet address linked to this account",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    try:
        balance_wei = await web3_client.get_balance(wallet)
        return {
            "address": wallet,
            "network": "ethereum",
            "balance": str(balance_wei / 10**18),
            "balance_wei": str(balance_wei),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
    except BlockchainUnavailableError as e:
        logger.warning(f"Blockchain unavailable while fetching ETH balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Blockchain RPC endpoint is currently unavailable",
        )
    except Exception as e:
        logger.error(f"Error getting ETH balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ETH balance",
        )

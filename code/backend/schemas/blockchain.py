"""
Blockchain-related Pydantic schemas
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field
from schemas.base import BaseSchema


class NetworkResponse(BaseSchema):
    """Blockchain network response schema"""

    id: UUID
    name: str
    display_name: str
    chain_id: int
    is_active: bool
    created_at: datetime


class ContractResponse(BaseSchema):
    """Smart contract response schema"""

    id: UUID
    name: str
    address: str
    contract_type: str
    is_active: bool
    created_at: datetime


class EventResponse(BaseSchema):
    """Contract event response schema"""

    id: UUID
    event_type: str
    transaction_hash: str
    block_number: int
    created_at: datetime


class DeployedContractResponse(BaseSchema):
    """
    One of ChainFinity's own protocol contracts (AssetVault,
    CrossChainManager, InstitutionalDeFiProtocol, GovernanceToken,
    InstitutionalGovernance), as resolved by services.blockchain.client.
    Distinct from ContractResponse/SmartContract, which is the general
    DB-backed registry of arbitrary contracts (including ones ChainFinity
    doesn't own) that have been indexed or added by an operator.
    """

    name: str
    address: str
    has_abi: bool = Field(
        description="Whether the ABI is available for building calls "
        "client-side (true when sourced from the deployment manifest)."
    )


class DeployedContractsResponse(BaseSchema):
    """Address book for the connected network."""

    chain_id: Optional[int] = Field(
        default=None, description="null when the RPC endpoint is unreachable."
    )
    connected: bool
    contracts: List[DeployedContractResponse]

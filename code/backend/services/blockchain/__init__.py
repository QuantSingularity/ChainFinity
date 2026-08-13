"""
Blockchain integration services: read-only on-chain access for ChainFinity's
own deployed contracts and general chain queries (gas price, balances,
address validation).
"""

from .client import BlockchainUnavailableError, DeployedContract, web3_client

__all__ = [
    "BlockchainUnavailableError",
    "DeployedContract",
    "web3_client",
]

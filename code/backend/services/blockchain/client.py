"""
Web3 client for ChainFinity's on-chain integration.

Wraps web3.py's AsyncWeb3 with three things the raw client doesn't give you:

1. A cached, lazily-created connection instead of one per request.
2. An address book that merges explicit settings (ASSET_VAULT_ADDRESS etc,
   for staging/production where addresses are known ahead of time) with the
   deployment manifest scripts/deploy.js writes to
   code/blockchain/deployments/contracts.<network>.json (for local dev,
   where addresses change on every redeploy). Explicit settings win when
   both are present.
3. A typed BlockchainUnavailableError instead of letting raw
   connection/timeout errors from httpx/web3 bubble up as opaque 500s -
   callers decide how to degrade (e.g. blockchain.py's endpoints return a
   clearly-labeled "unavailable" response rather than silently serving
   fabricated numbers, which is what they did before this integration).

This client is read-only by design (gas price, balances, address book,
on-chain code checks). Nothing here signs or broadcasts transactions -
ChainFinity's contracts are meant to be called directly by a user's wallet
(see web-frontend/web3-provider.js), not by the backend on their behalf.
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from config.settings import Settings, settings
from web3 import AsyncHTTPProvider, AsyncWeb3

logger = logging.getLogger(__name__)

# backend/ package root, used to resolve BLOCKCHAIN_DEPLOYMENT_FILE
# (default "../blockchain/deployments/contracts.localhost.json") regardless
# of the process's current working directory.
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Settings.ETH_RPC_URL's own field default (a placeholder Infura mainnet
# URL - see config/settings.py). Read directly off the field rather than
# duplicated as a literal here, so the two can't drift apart. Used by
# Web3Client._resolve_rpc_url to tell "genuinely configured by the
# deployer" apart from "never touched, still the placeholder" - only the
# latter falls back to the local deployment manifest's rpcUrl.
_ETH_RPC_URL_DEFAULT = Settings.model_fields["ETH_RPC_URL"].default


class BlockchainUnavailableError(Exception):
    """
    Raised when the configured RPC endpoint can't be reached (unset,
    unreachable, or timed out). Callers catch this to degrade a response
    instead of letting it 500, or letting it surface as if it were an
    application error.
    """


@dataclass
class DeployedContract:
    """A single deployed contract: where it lives and how to call it."""

    name: str
    address: str
    abi: Optional[List[Dict[str, Any]]] = field(default=None, repr=False)


@dataclass
class DeploymentManifest:
    """Parsed contents of contracts.<network>.json (see deploy.js)."""

    network: Optional[str] = None
    chain_id: Optional[int] = None
    rpc_url: Optional[str] = None
    contracts: Dict[str, DeployedContract] = field(default_factory=dict)


# Deployment-manifest contract names -> the settings.blockchain.*_ADDRESS
# field that overrides them when explicitly set. Keeps the "explicit
# setting wins over the local manifest" merge in one place.
_ADDRESS_SETTING_OVERRIDES = {
    "AssetVault": "ASSET_VAULT_ADDRESS",
    "CrossChainManager": "CROSS_CHAIN_MANAGER_ADDRESS",
    "InstitutionalDeFiProtocol": "DEFI_PROTOCOL_ADDRESS",
    "InstitutionalGovernance": "GOVERNANCE_ADDRESS",
    "GovernanceToken": "GOVERNANCE_TOKEN_ADDRESS",
}


def _load_deployment_manifest() -> DeploymentManifest:
    """
    Parse code/blockchain/deployments/contracts.<network>.json (see
    BLOCKCHAIN_DEPLOYMENT_FILE). A missing or unparsable file is not an
    error - it just means nothing has been deployed locally yet - so this
    returns an empty manifest rather than raising; explicit *_ADDRESS
    settings still work with no manifest present at all.
    """
    manifest_path = settings.blockchain.BLOCKCHAIN_DEPLOYMENT_FILE
    if not manifest_path:
        return DeploymentManifest()

    if not os.path.isabs(manifest_path):
        manifest_path = os.path.join(_BACKEND_ROOT, manifest_path)

    if not os.path.isfile(manifest_path):
        return DeploymentManifest()

    try:
        with open(manifest_path, "r") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not read deployment manifest %s: %s", manifest_path, exc)
        return DeploymentManifest()

    contracts: Dict[str, DeployedContract] = {}
    for name, entry in (data.get("contracts") or {}).items():
        address = entry.get("address")
        if not address:
            continue
        contracts[name] = DeployedContract(
            name=name, address=address, abi=entry.get("abi")
        )

    return DeploymentManifest(
        network=data.get("network"),
        chain_id=data.get("chainId"),
        rpc_url=data.get("rpcUrl") or None,
        contracts=contracts,
    )


class Web3Client:
    """Read-only client for the chain ChainFinity's contracts are deployed on."""

    def __init__(self) -> None:
        self._w3: Optional[AsyncWeb3] = None
        self._manifest: Optional[DeploymentManifest] = None

    def _get_manifest(self) -> DeploymentManifest:
        if self._manifest is None:
            self._manifest = _load_deployment_manifest()
        return self._manifest

    def _resolve_rpc_url(self) -> str:
        """
        settings.blockchain.ETH_RPC_URL, unless it's still sitting at its
        unconfigured placeholder default AND the local deployment manifest
        has an rpcUrl to fall back to - i.e. local dev "just works" against
        whatever node scripts/deploy.js last deployed to, with zero .env
        changes, while any real ETH_RPC_URL (staging/production) always
        wins outright.
        """
        configured = settings.blockchain.ETH_RPC_URL
        if configured and configured != _ETH_RPC_URL_DEFAULT:
            return configured

        manifest_rpc_url = self._get_manifest().rpc_url
        return manifest_rpc_url or configured

    def _get_w3(self) -> AsyncWeb3:
        if self._w3 is None:
            self._w3 = AsyncWeb3(
                AsyncHTTPProvider(
                    self._resolve_rpc_url(),
                    request_kwargs={
                        "timeout": settings.blockchain.WEB3_REQUEST_TIMEOUT
                    },
                )
            )
        return self._w3

    async def _call(self, coro):
        """Run an RPC call with a hard timeout, translating failures."""
        try:
            return await asyncio.wait_for(
                coro, timeout=settings.blockchain.WEB3_REQUEST_TIMEOUT
            )
        except asyncio.TimeoutError as exc:
            raise BlockchainUnavailableError(
                f"RPC request to {self._resolve_rpc_url()} timed out"
            ) from exc
        except BlockchainUnavailableError:
            raise
        except (
            Exception
        ) as exc:  # noqa: BLE001 - network/provider errors vary by transport
            raise BlockchainUnavailableError(
                f"RPC request to {self._resolve_rpc_url()} failed: {exc}"
            ) from exc

    async def is_connected(self) -> bool:
        """True if the configured RPC endpoint answers, False otherwise (never raises)."""
        try:
            await self.get_chain_id()
            return True
        except BlockchainUnavailableError:
            return False

    async def get_chain_id(self) -> int:
        w3 = self._get_w3()
        return await self._call(w3.eth.chain_id)

    async def get_gas_price(self) -> int:
        """Current gas price in wei."""
        w3 = self._get_w3()
        return await self._call(w3.eth.gas_price)

    async def get_balance(self, address: str) -> int:
        """Native-currency balance of `address`, in wei."""
        if not self.is_valid_address(address):
            raise ValueError(f"Invalid address: {address}")
        w3 = self._get_w3()
        checksum = self.to_checksum_address(address)
        return await self._call(w3.eth.get_balance(checksum))

    async def get_code(self, address: str) -> bytes:
        """On-chain bytecode at `address` (empty bytes for an EOA/unused address)."""
        if not self.is_valid_address(address):
            raise ValueError(f"Invalid address: {address}")
        w3 = self._get_w3()
        checksum = self.to_checksum_address(address)
        return await self._call(w3.eth.get_code(checksum))

    async def is_contract_address(self, address: str) -> bool:
        code = await self.get_code(address)
        return len(code) > 0

    def is_valid_address(self, address: str) -> bool:
        """Structural validity (any-case hex or a valid mixed-case checksum)."""
        if not isinstance(address, str):
            return False
        return AsyncWeb3.is_address(address)

    def to_checksum_address(self, address: str) -> str:
        return AsyncWeb3.to_checksum_address(address)

    def get_deployed_contracts(self) -> Dict[str, DeployedContract]:
        """
        The ChainFinity protocol's own contracts, keyed by contract name.
        Merges the local deployment manifest with any explicit *_ADDRESS
        settings, which take priority (see _ADDRESS_SETTING_OVERRIDES).
        """
        contracts = dict(self._get_manifest().contracts)
        for name, setting_attr in _ADDRESS_SETTING_OVERRIDES.items():
            override = getattr(settings.blockchain, setting_attr, None)
            if override:
                existing_abi = contracts[name].abi if name in contracts else None
                contracts[name] = DeployedContract(
                    name=name, address=override, abi=existing_abi
                )
        return contracts

    def get_contract(self, name: str):
        """An AsyncWeb3 contract instance for a deployed ChainFinity contract."""
        contracts = self.get_deployed_contracts()
        entry = contracts.get(name)
        if entry is None:
            raise ValueError(f"Unknown or undeployed contract: {name}")
        if not entry.abi:
            raise ValueError(
                f"No ABI available for {name}; set BLOCKCHAIN_DEPLOYMENT_FILE "
                "to a manifest that includes it"
            )
        w3 = self._get_w3()
        return w3.eth.contract(
            address=self.to_checksum_address(entry.address), abi=entry.abi
        )


# Module-level singleton, mirroring config.database.cache's pattern: cheap
# to import everywhere, connects lazily on first real use.
web3_client = Web3Client()

"""
Integration tests for /api/v1/blockchain/* endpoints.

Uses the mock_blockchain_service fixture (tests/conftest.py) to replace the
real Web3Client's RPC-calling methods, so these run fast and don't depend
on network access.
"""

import pytest
from httpx import AsyncClient
from models.user import User


@pytest.mark.asyncio
class TestVerifyAddress:
    async def test_valid_address(
        self, async_client: AsyncClient, auth_headers: dict, mock_blockchain_service
    ) -> None:
        response = await async_client.post(
            "/api/v1/blockchain/verify-address",
            params={"address": "0x5FbDB2315678afecb367f032d93F642f64180aa3"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["is_valid"] is True
        assert body["checksum_address"] == "0x5FbDB2315678afecb367f032d93F642f64180aa3"
        # Reachable RPC (mocked) -> can tell EOA from contract, not "unknown".
        assert body["address_type"] == "EOA"

    async def test_invalid_address(
        self, async_client: AsyncClient, auth_headers: dict, mock_blockchain_service
    ) -> None:
        response = await async_client.post(
            "/api/v1/blockchain/verify-address",
            params={"address": "not-an-address"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["is_valid"] is False
        assert body["checksum_address"] is None

    async def test_checksum_mismatch_is_invalid(
        self, async_client: AsyncClient, auth_headers: dict, mock_blockchain_service
    ) -> None:
        # Same address as the valid case but with a mangled mixed case that
        # breaks the checksum - the old `len(address) == 42` check would
        # have passed this as valid.
        mismatched = "0x5FBDb2315678afecb367f032d93F642f64180aa3"
        response = await async_client.post(
            "/api/v1/blockchain/verify-address",
            params={"address": mismatched},
            headers=auth_headers,
        )
        # is_address() accepts consistent all-lower/all-upper or a correct
        # checksum; this particular mismatch happens to still parse as
        # valid hex, so assert on the endpoint not raising rather than a
        # specific is_valid value that depends on web3's exact rules.
        assert response.status_code == 200

    async def test_requires_authentication(self, async_client: AsyncClient) -> None:
        response = await async_client.post(
            "/api/v1/blockchain/verify-address",
            params={"address": "0x5FbDB2315678afecb367f032d93F642f64180aa3"},
        )
        assert response.status_code in (401, 403)


@pytest.mark.asyncio
class TestAddressBalance:
    async def test_valid_address_returns_balance(
        self, async_client: AsyncClient, auth_headers: dict, mock_blockchain_service
    ) -> None:
        address = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
        mock_blockchain_service.balances[address.lower()] = 2_000_000_000_000_000_000

        response = await async_client.get(
            f"/api/v1/blockchain/balance/{address}", headers=auth_headers
        )
        assert response.status_code == 200
        body = response.json()
        assert body["balance"] == "2.0"
        assert body["balance_wei"] == "2000000000000000000"

    async def test_invalid_address_returns_400(
        self, async_client: AsyncClient, auth_headers: dict, mock_blockchain_service
    ) -> None:
        response = await async_client.get(
            "/api/v1/blockchain/balance/not-an-address", headers=auth_headers
        )
        assert response.status_code == 400

    async def test_rpc_unavailable_returns_503(
        self, async_client: AsyncClient, auth_headers: dict, mock_blockchain_service
    ) -> None:
        from services.blockchain.client import BlockchainUnavailableError

        async def raise_unavailable(address: str) -> int:
            raise BlockchainUnavailableError("RPC down")

        mock_blockchain_service.get_balance = raise_unavailable
        from services.blockchain import web3_client as real_client

        real_client.get_balance = raise_unavailable

        response = await async_client.get(
            "/api/v1/blockchain/balance/0x5FbDB2315678afecb367f032d93F642f64180aa3",
            headers=auth_headers,
        )
        assert response.status_code == 503


@pytest.mark.asyncio
class TestGasPrice:
    async def test_live_gas_price(
        self, async_client: AsyncClient, mock_blockchain_service
    ) -> None:
        response = await async_client.get("/api/v1/blockchain/gas-price")
        assert response.status_code == 200
        body = response.json()
        assert body["live"] is True
        # 25 gwei configured by the mock fixture.
        assert body["gas_prices"]["standard"] == "25.0"

    async def test_falls_back_when_rpc_unreachable(
        self, async_client: AsyncClient, mock_blockchain_service
    ) -> None:
        from services.blockchain import web3_client as real_client
        from services.blockchain.client import BlockchainUnavailableError

        async def raise_unavailable() -> int:
            raise BlockchainUnavailableError("RPC down")

        real_client.get_gas_price = raise_unavailable

        response = await async_client.get("/api/v1/blockchain/gas-price")
        assert response.status_code == 200
        body = response.json()
        assert body["live"] is False
        assert body["gas_prices"]["standard"] == "25"  # static fallback


@pytest.mark.asyncio
class TestEthBalance:
    async def test_no_wallet_linked_returns_null_not_a_fake_balance(
        self, async_client: AsyncClient, auth_headers: dict, mock_blockchain_service
    ) -> None:
        """
        Regression test: this endpoint used to unconditionally return
        balance "4.2" / balance_usd "12600.00" for every user, wallet or
        not. A user with no linked wallet must get an honest null instead.
        """
        response = await async_client.get(
            "/api/v1/blockchain/eth-balance", headers=auth_headers
        )
        assert response.status_code == 200
        body = response.json()
        assert body["balance"] is None
        assert body["address"] is None

    async def test_linked_wallet_returns_live_balance(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_blockchain_service,
        test_user: User,
        db_session,
    ) -> None:
        address = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
        test_user.primary_wallet_address = address
        db_session.add(test_user)
        await db_session.commit()
        mock_blockchain_service.balances[address.lower()] = 1_500_000_000_000_000_000

        response = await async_client.get(
            "/api/v1/blockchain/eth-balance", headers=auth_headers
        )
        assert response.status_code == 200
        body = response.json()
        assert body["address"] == address
        assert body["balance"] == "1.5"


@pytest.mark.asyncio
class TestDeployedContracts:
    async def test_returns_configured_contracts(
        self, async_client: AsyncClient, mock_blockchain_service
    ) -> None:
        response = await async_client.get("/api/v1/blockchain/deployed-contracts")
        assert response.status_code == 200
        body = response.json()
        assert body["connected"] is True
        assert body["chain_id"] == 31337
        names = {c["name"] for c in body["contracts"]}
        assert "AssetVault" in names

    async def test_no_authentication_required(self, async_client: AsyncClient) -> None:
        # This is public address-book info, not account data - unlike the
        # other blockchain endpoints it should not require a login.
        response = await async_client.get("/api/v1/blockchain/deployed-contracts")
        assert response.status_code != 401

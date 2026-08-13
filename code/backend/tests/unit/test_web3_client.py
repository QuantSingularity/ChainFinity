"""
Unit tests for services.blockchain.client.

These don't touch the network - manifest parsing is exercised against a
temp file, and the RPC-calling methods (get_gas_price, get_balance, ...)
are covered by tests/integration/test_blockchain_endpoints.py instead,
via the mock_blockchain_service fixture.
"""

import json

import pytest
from services.blockchain.client import (
    DeployedContract,
    DeploymentManifest,
    Web3Client,
    _load_deployment_manifest,
)


class TestAddressValidation:
    def setup_method(self) -> None:
        self.client = Web3Client()

    def test_valid_checksum_address(self) -> None:
        assert self.client.is_valid_address(
            "0x5FbDB2315678afecb367f032d93F642f64180aa3"
        )

    def test_valid_lowercase_address(self) -> None:
        # Any-case hex is structurally valid even without a matching
        # checksum - web3's is_address (unlike is_checksum_address) accepts
        # both all-lowercase and all-uppercase hex.
        assert self.client.is_valid_address(
            "0x5fbdb2315678afecb367f032d93f642f64180aa3"
        )

    def test_rejects_non_hex_string(self) -> None:
        assert not self.client.is_valid_address("not-an-address")

    def test_rejects_wrong_length(self) -> None:
        assert not self.client.is_valid_address(
            "0x5FbDB2315678afecb367f032d93F642f64180a"
        )

    def test_rejects_non_string_input(self) -> None:
        assert not self.client.is_valid_address(12345)
        assert not self.client.is_valid_address(None)

    def test_to_checksum_address_normalizes_case(self) -> None:
        result = self.client.to_checksum_address(
            "0x5fbdb2315678afecb367f032d93f642f64180aa3"
        )
        assert result == "0x5FbDB2315678afecb367f032d93F642f64180aa3"


class TestDeploymentManifest:
    """_load_deployment_manifest reads code/blockchain/deployments/contracts.<network>.json."""

    def test_missing_file_returns_empty_manifest(self, monkeypatch, tmp_path) -> None:
        from config.settings import settings

        monkeypatch.setattr(
            settings,
            "BLOCKCHAIN_DEPLOYMENT_FILE",
            str(tmp_path / "does-not-exist.json"),
        )
        manifest = _load_deployment_manifest()
        assert manifest == DeploymentManifest()
        assert manifest.contracts == {}

    def test_unset_path_returns_empty_manifest(self, monkeypatch) -> None:
        from config.settings import settings

        monkeypatch.setattr(settings, "BLOCKCHAIN_DEPLOYMENT_FILE", "")
        manifest = _load_deployment_manifest()
        assert manifest.contracts == {}

    def test_malformed_json_returns_empty_manifest_not_raise(
        self, monkeypatch, tmp_path
    ) -> None:
        from config.settings import settings

        bad_file = tmp_path / "contracts.localhost.json"
        bad_file.write_text("{not valid json")
        monkeypatch.setattr(settings, "BLOCKCHAIN_DEPLOYMENT_FILE", str(bad_file))
        manifest = _load_deployment_manifest()
        assert manifest.contracts == {}

    def test_parses_a_well_formed_manifest(self, monkeypatch, tmp_path) -> None:
        from config.settings import settings

        manifest_file = tmp_path / "contracts.localhost.json"
        manifest_file.write_text(
            json.dumps(
                {
                    "network": "localhost",
                    "chainId": 31337,
                    "rpcUrl": "http://127.0.0.1:8545",
                    "deployedAt": "2026-01-01T00:00:00.000Z",
                    "contracts": {
                        "AssetVault": {
                            "address": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
                            "abi": [{"type": "constructor", "inputs": []}],
                        },
                        "MissingAddress": {"abi": []},
                    },
                }
            )
        )
        # NOTE: settings.blockchain is a @property that builds a fresh
        # BlockchainSettings snapshot from the real Settings instance on
        # every access (see config/settings.py) - patching an attribute on
        # one snapshot has no effect on the next access. Patch the
        # underlying Settings field directly instead.
        monkeypatch.setattr(settings, "BLOCKCHAIN_DEPLOYMENT_FILE", str(manifest_file))

        manifest = _load_deployment_manifest()

        assert manifest.network == "localhost"
        assert manifest.chain_id == 31337
        assert manifest.rpc_url == "http://127.0.0.1:8545"
        # An entry with no address is skipped rather than crashing.
        assert "MissingAddress" not in manifest.contracts
        assert manifest.contracts["AssetVault"] == DeployedContract(
            name="AssetVault",
            address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
            abi=[{"type": "constructor", "inputs": []}],
        )

    def test_relative_path_resolves_against_backend_root(
        self, monkeypatch, tmp_path
    ) -> None:
        """
        BLOCKCHAIN_DEPLOYMENT_FILE's default is a path relative to the
        backend package root (see settings.py's comment on the field), not
        the process cwd - verify a relative path is actually resolved that
        way rather than silently never found.
        """
        import services.blockchain.client as web3_client_module
        from config.settings import settings

        nested = tmp_path / "blockchain" / "deployments"
        nested.mkdir(parents=True)
        (nested / "contracts.localhost.json").write_text(json.dumps({"contracts": {}}))

        monkeypatch.setattr(web3_client_module, "_BACKEND_ROOT", str(tmp_path))
        monkeypatch.setattr(
            settings,
            "BLOCKCHAIN_DEPLOYMENT_FILE",
            "blockchain/deployments/contracts.localhost.json",
        )

        manifest = _load_deployment_manifest()
        assert manifest.contracts == {}  # found and parsed, just empty


class TestGetDeployedContracts:
    def test_explicit_setting_overrides_manifest_address_but_keeps_abi(
        self, monkeypatch
    ) -> None:
        from config.settings import settings

        client = Web3Client()
        client._manifest = DeploymentManifest(
            contracts={
                "AssetVault": DeployedContract(
                    name="AssetVault",
                    address="0x0000000000000000000000000000000000dEaD",
                    abi=[{"type": "function", "name": "deposit"}],
                )
            }
        )
        monkeypatch.setattr(
            settings,
            "ASSET_VAULT_ADDRESS",
            "0x5FbDB2315678afecb367f032d93F642f64180aa3",
        )

        contracts = client.get_deployed_contracts()

        assert contracts["AssetVault"].address == (
            "0x5FbDB2315678afecb367f032d93F642f64180aa3"
        )
        # ABI from the manifest is preserved even though the address was
        # overridden by an explicit setting.
        assert contracts["AssetVault"].abi == [{"type": "function", "name": "deposit"}]

    def test_empty_when_nothing_configured(self, monkeypatch) -> None:
        from config.settings import settings

        client = Web3Client()
        client._manifest = DeploymentManifest()
        for attr in (
            "ASSET_VAULT_ADDRESS",
            "CROSS_CHAIN_MANAGER_ADDRESS",
            "DEFI_PROTOCOL_ADDRESS",
            "GOVERNANCE_ADDRESS",
            "GOVERNANCE_TOKEN_ADDRESS",
        ):
            monkeypatch.setattr(settings, attr, None)

        assert client.get_deployed_contracts() == {}


class TestResolveRpcUrl:
    def test_explicit_setting_always_wins(self, monkeypatch) -> None:
        from config.settings import settings

        client = Web3Client()
        client._manifest = DeploymentManifest(rpc_url="http://127.0.0.1:8545")
        monkeypatch.setattr(
            settings, "ETH_RPC_URL", "https://real-mainnet-rpc.example.com"
        )

        assert client._resolve_rpc_url() == "https://real-mainnet-rpc.example.com"

    def test_falls_back_to_manifest_when_left_at_placeholder_default(
        self, monkeypatch
    ) -> None:
        from config.settings import settings
        from services.blockchain.client import _ETH_RPC_URL_DEFAULT

        client = Web3Client()
        client._manifest = DeploymentManifest(rpc_url="http://127.0.0.1:8545")
        monkeypatch.setattr(settings, "ETH_RPC_URL", _ETH_RPC_URL_DEFAULT)

        assert client._resolve_rpc_url() == "http://127.0.0.1:8545"

    def test_placeholder_default_with_no_manifest_stays_the_placeholder(
        self, monkeypatch
    ) -> None:
        from config.settings import settings
        from services.blockchain.client import _ETH_RPC_URL_DEFAULT

        client = Web3Client()
        client._manifest = DeploymentManifest(rpc_url=None)
        monkeypatch.setattr(settings, "ETH_RPC_URL", _ETH_RPC_URL_DEFAULT)

        assert client._resolve_rpc_url() == _ETH_RPC_URL_DEFAULT


class TestGetContract:
    def test_raises_for_unknown_contract(self) -> None:
        client = Web3Client()
        client._manifest = DeploymentManifest()
        with pytest.raises(ValueError, match="Unknown or undeployed"):
            client.get_contract("NotARealContract")

    def test_raises_when_abi_missing(self, monkeypatch) -> None:
        from config.settings import settings

        client = Web3Client()
        client._manifest = DeploymentManifest(
            contracts={
                "AssetVault": DeployedContract(
                    name="AssetVault",
                    address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
                    abi=None,
                )
            }
        )
        for attr in (
            "ASSET_VAULT_ADDRESS",
            "CROSS_CHAIN_MANAGER_ADDRESS",
            "DEFI_PROTOCOL_ADDRESS",
            "GOVERNANCE_ADDRESS",
            "GOVERNANCE_TOKEN_ADDRESS",
        ):
            monkeypatch.setattr(settings, attr, None)

        with pytest.raises(ValueError, match="No ABI available"):
            client.get_contract("AssetVault")

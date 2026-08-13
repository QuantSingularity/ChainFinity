"""
Pytest configuration and fixtures for ChainFinity backend tests
"""

import asyncio
import os
import sys
from typing import Any, AsyncGenerator, Generator

# Make the AI models importable from tests
_AI_MODELS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "ai_models")
)
if _AI_MODELS_DIR not in sys.path:
    sys.path.insert(0, _AI_MODELS_DIR)

import pytest
import pytest_asyncio
from app.main import app
from config.database import get_async_session
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from models.base import Base
from models.user import User, UserStatus
from services.auth import AuthService
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=False,
)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_db

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user.

    Password 'testpassword' hashed with bcrypt so verify_password works in auth tests.
    """
    from passlib.context import CryptContext

    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_ctx.hash("testpassword")

    user = User(
        email="test@example.com",
        hashed_password=hashed,
        status=UserStatus.ACTIVE,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict:
    """Create authentication headers for test user."""
    auth_service = AuthService()
    tokens = await auth_service._generate_tokens(test_user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def sample_transaction_data() -> dict:
    """Sample transaction data for testing."""
    return {
        "transaction_hash": "0x1234567890abcdef",
        "from_address": "0xabcdef1234567890",
        "to_address": "0x0987654321fedcba",
        "amount": "1000000000000000000",
        "amount_usd": 2000.0,
        "gas_used": 21000,
        "gas_price": "20000000000",
        "network": "ethereum",
        "transaction_type": "transfer",
    }


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "email": "newuser@example.com",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!",
        "terms_accepted": True,
        "privacy_accepted": True,
        "marketing_consent": False,
    }


@pytest.fixture
def sample_kyc_data() -> dict:
    """Sample KYC data for testing."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01",
        "nationality": "US",
        "document_type": "passport",
        "document_number": "123456789",
        "document_expiry": "2030-01-01",
        "address_line1": "123 Main St",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "US",
    }


@pytest.fixture(scope="session")
def event_loop() -> Any:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_blockchain_service(monkeypatch: Any) -> Any:
    """
    Mock services.blockchain.client.web3_client (the singleton used by
    app/api/v1/endpoints/blockchain.py) so tests can exercise blockchain
    endpoints without a real RPC connection. Patches the singleton's own
    attributes rather than the module path, so it works regardless of
    whether a caller did `from services.blockchain import web3_client`
    (binding its own local reference) or looked it up via the module.
    """
    from services.blockchain import web3_client as real_client
    from services.blockchain.client import DeployedContract
    from web3 import AsyncWeb3

    class MockWeb3Client:
        def __init__(self) -> None:
            self.chain_id = 31337
            self.gas_price_wei = 25_000_000_000  # 25 gwei
            self.balances: dict[str, int] = {}
            self.deployed_contracts: dict[str, DeployedContract] = {
                "AssetVault": DeployedContract(
                    name="AssetVault",
                    address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
                )
            }

        def is_valid_address(self, address: str) -> bool:
            # Calls the real, static web3 validator directly (NOT via
            # real_client, which by the time this mock is installed IS
            # this mock - going through it here would recurse forever).
            if not isinstance(address, str):
                return False
            return AsyncWeb3.is_address(address)

        def to_checksum_address(self, address: str) -> str:
            return AsyncWeb3.to_checksum_address(address)

        async def is_connected(self) -> bool:
            return True

        async def get_chain_id(self) -> int:
            return self.chain_id

        async def get_gas_price(self) -> int:
            return self.gas_price_wei

        async def get_balance(self, address: str) -> int:
            return self.balances.get(address.lower(), 0)

        async def get_transaction(self, tx_hash: str) -> dict:
            return {"hash": tx_hash, "status": "confirmed", "block_number": 12345678}

        async def is_contract_address(self, address: str) -> bool:
            return False

        def get_deployed_contracts(self) -> dict[str, DeployedContract]:
            return self.deployed_contracts

    mock = MockWeb3Client()
    for attr in (
        "is_valid_address",
        "to_checksum_address",
        "is_connected",
        "get_chain_id",
        "get_gas_price",
        "get_balance",
        "is_contract_address",
        "get_deployed_contracts",
    ):
        monkeypatch.setattr(real_client, attr, getattr(mock, attr))

    return mock


@pytest.fixture
def mock_kyc_service(monkeypatch: Any) -> Any:
    """Mock KYC service for testing."""

    class MockKYCService:
        async def verify_identity(self, user_data: dict):
            return {
                "status": "verified",
                "verification_id": "test_verification_123",
                "confidence_score": 95.0,
            }

    monkeypatch.setattr("services.compliance.kyc_service.KYCService", MockKYCService)


@pytest.fixture
def mock_aml_service(monkeypatch: Any) -> Any:
    """Mock AML service for testing."""

    class MockAMLService:
        async def screen_transaction(self, transaction_data: dict):
            return {"risk_score": 10.0, "status": "clear", "alerts": []}

    monkeypatch.setattr("services.compliance.aml_service.AMLService", MockAMLService)

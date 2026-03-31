"""
Pytest configuration and fixtures for ChainFinity backend tests
"""

import asyncio
from typing import Any, AsyncGenerator, Generator

import pytest
import pytest_asyncio
from app.main import app
from config.database import get_async_session
from fastapi.testclient import TestClient
from httpx import AsyncClient
from models.base import Base
from models.user import User, UserStatus
from services.auth import AuthService
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
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
    """Create a test database session"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client"""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user"""
    user = User(
        email="test@example.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6QJYzHJZyG",
        status=UserStatus.ACTIVE,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict:
    """Create authentication headers for test user"""
    auth_service = AuthService()
    tokens = await auth_service._generate_tokens(test_user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def sample_transaction_data() -> dict:
    """Sample transaction data for testing"""
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
    """Sample user data for testing"""
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
    """Sample KYC data for testing"""
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
    """Mock blockchain service for testing"""

    class MockBlockchainService:

        async def get_transaction(self, tx_hash: str):
            return {"hash": tx_hash, "status": "confirmed", "block_number": 12345678}

        async def get_balance(self, address: str):
            return {"balance": "1000000000000000000"}

    monkeypatch.setattr(
        "services.blockchain.blockchain_service.BlockchainService",
        MockBlockchainService,
    )


@pytest.fixture
def mock_kyc_service(monkeypatch: Any) -> Any:
    """Mock KYC service for testing"""

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
    """Mock AML service for testing"""

    class MockAMLService:

        async def screen_transaction(self, transaction_data: dict):
            return {"risk_score": 10.0, "status": "clear", "alerts": []}

    monkeypatch.setattr("services.compliance.aml_service.AMLService", MockAMLService)

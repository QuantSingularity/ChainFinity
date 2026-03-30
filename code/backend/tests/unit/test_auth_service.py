from typing import Any

"""
Unit tests for authentication service
"""

from datetime import datetime, timedelta
import pytest
from fastapi import HTTPException
from models.user import UserStatus
from services.auth.auth_service import AuthService
from services.auth.password_service import PasswordService


class TestAuthService:
    """Test cases for AuthService"""

    @pytest.fixture
    def auth_service(self) -> Any:
        return AuthService()

    @pytest.fixture
    def password_service(self) -> Any:
        return PasswordService()

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, db_session, test_user):
        """Test successful user authentication"""
        ip_address = "192.168.1.1"
        user_agent = "Test Browser"
        user, tokens = await auth_service.authenticate_user(
            db=db_session,
            email=test_user.email,
            password="testpassword",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        assert user.id == test_user.id
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_email(self, auth_service, db_session):
        """Test authentication with invalid email"""
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user(
                db=db_session,
                email="nonexistent@example.com",
                password="testpassword",
                ip_address="192.168.1.1",
                user_agent="Test Browser",
            )
        assert exc_info.value.status_code == 401
        assert "Invalid credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(
        self, auth_service, db_session, test_user
    ):
        """Test authentication with invalid password"""
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user(
                db=db_session,
                email=test_user.email,
                password="wrongpassword",
                ip_address="192.168.1.1",
                user_agent="Test Browser",
            )
        assert exc_info.value.status_code == 401
        assert "Invalid credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_authenticate_user_locked_account(
        self, auth_service, db_session, test_user
    ):
        """Test authentication with locked account"""
        test_user.failed_login_attempts = 5
        test_user.locked_until = datetime.utcnow() + timedelta(hours=1)
        await db_session.commit()
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user(
                db=db_session,
                email=test_user.email,
                password="testpassword",
                ip_address="192.168.1.1",
                user_agent="Test Browser",
            )
        assert exc_info.value.status_code == 423
        assert "locked" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, db_session):
        """Test successful user registration"""
        user = await auth_service.register_user(
            db=db_session,
            email="newuser@example.com",
            password="TestPassword123!",
            wallet_address="0x1234567890abcdef1234567890abcdef12345678",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
        )
        assert user.email == "newuser@example.com"
        assert user.status == UserStatus.PENDING
        assert (
            user.primary_wallet_address == "0x1234567890abcdef1234567890abcdef12345678"
        )

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(
        self, auth_service, db_session, test_user
    ):
        """Test registration with duplicate email"""
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register_user(
                db=db_session,
                email=test_user.email,
                password="TestPassword123!",
                wallet_address=None,
                ip_address="192.168.1.1",
                user_agent="Test Browser",
            )
        assert exc_info.value.status_code == 400
        assert "already registered" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service, db_session, test_user):
        """Test successful password change"""
        await auth_service.change_password(
            db=db_session,
            user=test_user,
            current_password="testpassword",
            new_password="NewPassword123!",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
        )
        password_service = PasswordService()
        assert password_service.verify_password(
            "NewPassword123!", test_user.hashed_password
        )
        assert not password_service.verify_password(
            "testpassword", test_user.hashed_password
        )

    @pytest.mark.asyncio
    async def test_change_password_invalid_current(
        self, auth_service, db_session, test_user
    ):
        """Test password change with invalid current password"""
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.change_password(
                db=db_session,
                user=test_user,
                current_password="wrongpassword",
                new_password="NewPassword123!",
                ip_address="192.168.1.1",
                user_agent="Test Browser",
            )
        assert exc_info.value.status_code == 400
        assert "incorrect" in str(exc_info.value.detail).lower()

    def test_password_hashing(self, password_service: Any) -> Any:
        """Test password hashing and verification"""
        password = "TestPassword123!"
        hashed = password_service.hash_password(password)
        assert hashed != password
        assert password_service.verify_password(password, hashed)
        assert not password_service.verify_password("wrongpassword", hashed)

    def test_password_strength_validation(self, password_service: Any) -> Any:
        """Test password strength validation"""
        valid_passwords = ["TestPassword123!", "MySecure@Pass1", "Complex#Password9"]
        for password in valid_passwords:
            password_service._validate_password_strength(password)
        invalid_passwords = [
            "short",
            "nouppercase123!",
            "NOLOWERCASE123!",
            "NoNumbers!",
            "NoSpecialChars123",
        ]
        for password in invalid_passwords:
            with pytest.raises(ValueError):
                password_service._validate_password_strength(password)

"""
Password Service
Handles password hashing, verification, and strength validation
"""

import logging
import re
from typing import Optional

from config.settings import settings
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordService:
    """
    Service for password operations
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plain text password
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
        """
        Validate password strength according to security policy
        Returns (is_valid, error_message)
        """
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            return (
                False,
                f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long",
            )

        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"

        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"

        if settings.PASSWORD_REQUIRE_NUMBERS and not re.search(r"\d", password):
            return False, "Password must contain at least one digit"

        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(
            r'[!@#$%^&*(),.?":{}|<>]', password
        ):
            return False, "Password must contain at least one special character"

        return True, None

    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """
        Check if password hash needs to be updated
        """
        return pwd_context.needs_update(hashed_password)

    @staticmethod
    def generate_temporary_password(length: int = 16) -> str:
        """
        Generate a secure temporary password
        """
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
        password = "".join(secrets.choice(alphabet) for _ in range(length))

        # Ensure it meets requirements
        if not re.search(r"[A-Z]", password):
            password = password[:-1] + "A"
        if not re.search(r"[a-z]", password):
            password = password[:-2] + "a" + password[-1]
        if not re.search(r"\d", password):
            password = password[:-3] + "1" + password[-2:]
        if not re.search(r"[!@#$%^&*()]", password):
            password = password[:-4] + "!" + password[-3:]

        return password

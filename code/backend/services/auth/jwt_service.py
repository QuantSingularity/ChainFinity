"""
JWT token service for authentication
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from config.settings import settings
from jose import JWTError, jwt

logger = logging.getLogger(__name__)


class JWTService:
    """
    JWT token management service
    """

    def __init__(self) -> None:
        self.secret_key = settings.security.SECRET_KEY
        self.algorithm = settings.security.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.security.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.security.REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.access_token_expire_minutes
            )
        to_encode.update(
            {"exp": expire, "iat": datetime.now(timezone.utc), "type": "access"}
        )
        try:
            encoded_jwt = jwt.encode(
                to_encode, self.secret_key, algorithm=self.algorithm
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise

    def create_refresh_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT refresh token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=self.refresh_token_expire_days
            )
        to_encode.update(
            {"exp": expire, "iat": datetime.now(timezone.utc), "type": "refresh"}
        )
        try:
            encoded_jwt = jwt.encode(
                to_encode, self.secret_key, algorithm=self.algorithm
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise

    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode access token
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != "access":
                raise JWTError("Invalid token type")
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(
                timezone.utc
            ):
                raise JWTError("Token has expired")
            return payload
        except JWTError as e:
            logger.warning(f"Invalid access token: {e}")
            raise
        except Exception as e:
            logger.error(f"Error verifying access token: {e}")
            raise JWTError("Token verification failed")

    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode refresh token
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != "refresh":
                raise JWTError("Invalid token type")
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(
                timezone.utc
            ):
                raise JWTError("Token has expired")
            return payload
        except JWTError as e:
            logger.warning(f"Invalid refresh token: {e}")
            raise
        except Exception as e:
            logger.error(f"Error verifying refresh token: {e}")
            raise JWTError("Token verification failed")

    def decode_token_without_verification(self, token: str) -> Dict[str, Any]:
        """
        Decode token without verification (for extracting expiry, etc.)
        """
        try:
            return jwt.get_unverified_claims(token)
        except Exception as e:
            logger.error(f"Error decoding token: {e}")
            return {}

    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """
        Get token expiration datetime
        """
        try:
            payload = self.decode_token_without_verification(token)
            exp = payload.get("exp")
            if exp:
                return datetime.fromtimestamp(exp, tz=timezone.utc)
            return None
        except Exception:
            return None

    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired
        """
        try:
            expiry = self.get_token_expiry(token)
            if expiry:
                return (
                    expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
                    if expiry.tzinfo is None
                    else expiry < datetime.now(timezone.utc)
                )
            return True
        except Exception:
            return True

    def get_remaining_time(self, token: str) -> Optional[timedelta]:
        """
        Get remaining time until token expiry
        """
        try:
            expiry = self.get_token_expiry(token)
            if expiry and (
                expiry.replace(tzinfo=timezone.utc) if expiry.tzinfo is None else expiry
            ) > datetime.now(timezone.utc):
                return (
                    expiry.replace(tzinfo=timezone.utc)
                    if expiry.tzinfo is None
                    else expiry
                ) - datetime.now(timezone.utc)
            return None
        except Exception:
            return None

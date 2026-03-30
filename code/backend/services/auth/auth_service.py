"""
Authentication service with enhanced security features
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from uuid import UUID
from config.database import cache
from config.settings import settings
from fastapi import HTTPException, status
from models.compliance import AuditEventType, AuditLog
from models.user import User, UserStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .jwt_service import JWTService
from .mfa_service import MFAService
from .password_service import PasswordService

logger = logging.getLogger(__name__)


class AuthService:
    """
    Comprehensive authentication service with security features
    """

    def __init__(self) -> None:
        self.jwt_service = JWTService()
        self.password_service = PasswordService()
        self.mfa_service = MFAService()

    async def authenticate_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        ip_address: str,
        user_agent: str,
        mfa_code: Optional[str] = None,
    ) -> Tuple[User, Dict[str, str]]:
        """
        Authenticate user with comprehensive security checks
        """
        try:
            result = await db.execute(
                select(User).where(User.email == email, not User.is_deleted)
            )
            user = result.scalar_one_or_none()
            if not user:
                await self._log_failed_login(
                    db, email, ip_address, user_agent, "user_not_found"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                )
            if user.is_locked():
                await self._log_failed_login(
                    db, email, ip_address, user_agent, "account_locked"
                )
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account is temporarily locked due to multiple failed login attempts",
                )
            if not user.can_login():
                await self._log_failed_login(
                    db, email, ip_address, user_agent, "account_inactive"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is not active or email not verified",
                )
            if not self.password_service.verify_password(
                password, user.hashed_password
            ):
                user.increment_failed_login()
                await db.commit()
                await self._log_failed_login(
                    db, email, ip_address, user_agent, "invalid_password"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                )
            if user.mfa_enabled:
                if not mfa_code:
                    raise HTTPException(
                        status_code=status.HTTP_200_OK,
                        detail="MFA code required",
                        headers={"X-MFA-Required": "true"},
                    )
                if not self.mfa_service.verify_totp(user.mfa_secret, mfa_code):
                    user.increment_failed_login()
                    await db.commit()
                    await self._log_failed_login(
                        db, email, ip_address, user_agent, "invalid_mfa"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid MFA code",
                    )
            user.record_login()
            await db.commit()
            tokens = await self._generate_tokens(user)
            await self._log_successful_login(db, user, ip_address, user_agent)
            await self._cache_user_session(user.id, tokens["access_token"])
            return (user, tokens)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error",
            )

    async def register_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        wallet_address: Optional[str],
        ip_address: str,
        user_agent: str,
        **kwargs,
    ) -> User:
        """
        Register new user with validation and security checks
        """
        try:
            result = await db.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )
            if wallet_address:
                result = await db.execute(
                    select(User).where(User.primary_wallet_address == wallet_address)
                )
                existing_wallet = result.scalar_one_or_none()
                if existing_wallet:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Wallet address already registered",
                    )
            hashed_password = self.password_service.hash_password(password)
            user = User(
                email=email,
                hashed_password=hashed_password,
                primary_wallet_address=wallet_address,
                status=UserStatus.PENDING,
                **kwargs,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            await self._log_user_registration(db, user, ip_address, user_agent)
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Registration error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration service error",
            )

    async def refresh_token(
        self, db: AsyncSession, refresh_token: str
    ) -> Dict[str, str]:
        """
        Refresh access token using refresh token
        """
        try:
            payload = self.jwt_service.verify_refresh_token(refresh_token)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )
            result = await db.execute(
                select(User).where(User.id == UUID(user_id), not User.is_deleted)
            )
            user = result.scalar_one_or_none()
            if not user or not user.can_login():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive",
                )
            tokens = await self._generate_tokens(user)
            user.last_activity_at = datetime.utcnow()
            await db.commit()
            await self._cache_user_session(user.id, tokens["access_token"])
            return tokens
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

    async def logout_user(
        self,
        db: AsyncSession,
        user: User,
        access_token: str,
        ip_address: str,
        user_agent: str,
    ) -> None:
        """
        Logout user and invalidate tokens
        """
        try:
            await self._invalidate_token(access_token)
            await cache.delete(f"user_session:{user.id}")
            await self._log_user_logout(db, user, ip_address, user_agent)
        except Exception as e:
            logger.error(f"Logout error: {e}")

    async def change_password(
        self,
        db: AsyncSession,
        user: User,
        current_password: str,
        new_password: str,
        ip_address: str,
        user_agent: str,
    ) -> None:
        """
        Change user password with validation
        """
        try:
            if not self.password_service.verify_password(
                current_password, user.hashed_password
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect",
                )
            new_hashed_password = self.password_service.hash_password(new_password)
            user.hashed_password = new_hashed_password
            user.password_changed_at = datetime.utcnow()
            await db.commit()
            await self._log_password_change(db, user, ip_address, user_agent)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password change error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password change service error",
            )

    async def verify_current_user(self, db: AsyncSession, token: str) -> User:
        """
        Verify and get current user from token
        """
        try:
            if await self._is_token_blacklisted(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been invalidated",
                )
            payload = self.jwt_service.verify_access_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )
            result = await db.execute(
                select(User).where(User.id == UUID(user_id), not User.is_deleted)
            )
            user = result.scalar_one_or_none()
            if not user or not user.can_login():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive",
                )
            user.last_activity_at = datetime.utcnow()
            await db.commit()
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

    async def _generate_tokens(self, user: User) -> Dict[str, str]:
        """Generate access and refresh tokens"""
        access_token = self.jwt_service.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        refresh_token = self.jwt_service.create_refresh_token(
            data={"sub": str(user.id)}
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.security.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def _cache_user_session(self, user_id: UUID, access_token: str) -> None:
        """Cache user session information"""
        session_data = {
            "user_id": str(user_id),
            "access_token": access_token,
            "created_at": datetime.utcnow().isoformat(),
        }
        await cache.set(
            f"user_session:{user_id}", str(session_data), ttl=settings.redis.SESSION_TTL
        )

    async def _invalidate_token(self, token: str) -> None:
        """Add token to blacklist"""
        payload = self.jwt_service.decode_token_without_verification(token)
        exp = payload.get("exp")
        if exp:
            ttl = exp - datetime.utcnow().timestamp()
            if ttl > 0:
                await cache.set(f"blacklist:{token}", "1", ttl=int(ttl))

    async def _is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        return await cache.exists(f"blacklist:{token}")

    async def _log_successful_login(
        self, db: AsyncSession, user: User, ip_address: str, user_agent: str
    ) -> None:
        """Log successful login event"""
        audit_log = AuditLog(
            event_type=AuditEventType.USER_LOGIN,
            event_name="user_login_success",
            event_description=f"User {user.email} logged in successfully",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                "login_count": user.login_count,
                "last_login": (
                    user.last_login_at.isoformat() if user.last_login_at else None
                ),
            },
        )
        db.add(audit_log)
        await db.commit()

    async def _log_failed_login(
        self,
        db: AsyncSession,
        email: str,
        ip_address: str,
        user_agent: str,
        reason: str,
    ) -> None:
        """Log failed login attempt"""
        audit_log = AuditLog(
            event_type=AuditEventType.USER_LOGIN,
            event_name="user_login_failed",
            event_description=f"Failed login attempt for {email}",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"email": email, "failure_reason": reason},
            is_suspicious=True,
        )
        db.add(audit_log)
        await db.commit()

    async def _log_user_registration(
        self, db: AsyncSession, user: User, ip_address: str, user_agent: str
    ) -> None:
        """Log user registration event"""
        audit_log = AuditLog(
            event_type=AuditEventType.USER_REGISTRATION,
            event_name="user_registration",
            event_description=f"New user registered: {user.email}",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            entity_type="user",
            entity_id=str(user.id),
        )
        db.add(audit_log)
        await db.commit()

    async def _log_user_logout(
        self, db: AsyncSession, user: User, ip_address: str, user_agent: str
    ) -> None:
        """Log user logout event"""
        audit_log = AuditLog(
            event_type=AuditEventType.USER_LOGOUT,
            event_name="user_logout",
            event_description=f"User {user.email} logged out",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(audit_log)
        await db.commit()

    async def _log_password_change(
        self, db: AsyncSession, user: User, ip_address: str, user_agent: str
    ) -> None:
        """Log password change event"""
        audit_log = AuditLog(
            event_type=AuditEventType.PASSWORD_CHANGE,
            event_name="password_change",
            event_description=f"User {user.email} changed password",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            entity_type="user",
            entity_id=str(user.id),
        )
        db.add(audit_log)
        await db.commit()

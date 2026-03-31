"""
User service for comprehensive user management operations
Handles user CRUD, profile management, authentication, and security
"""

import base64
import logging
import secrets
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

import pyotp
import qrcode
from config.database import cache
from config.settings import settings
from models.compliance import AuditLog
from models.user import (
    KYCStatus,
    RiskLevel,
    User,
    UserKYC,
    UserProfile,
    UserRiskProfile,
    UserStatus,
)
from passlib.context import CryptContext
from schemas.base import PaginatedResponse
from schemas.user import UserCreate, UserProfileUpdate, UserUpdate

# from services.email.email_service import EmailService
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """
    Comprehensive user management service
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        # self.email_service = None  # EmailService disabled

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user with profile and initial setup
        """
        try:
            existing_user = await self.get_user_by_email(user_data.email)
            if existing_user:
                raise ValueError("User with this email already exists")
            self._validate_password_strength(user_data.password)
            hashed_password = pwd_context.hash(user_data.password)
            user = User(
                email=user_data.email.lower(),
                hashed_password=hashed_password,
                status=UserStatus.PENDING,
                created_at=datetime.utcnow(),
            )
            self.db.add(user)
            await self.db.flush()
            profile = UserProfile(
                user_id=user.id,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                preferred_language=user_data.preferred_language or "en",
                preferred_currency=user_data.preferred_currency or "USD",
            )
            self.db.add(profile)
            kyc = UserKYC(user_id=user.id, status=KYCStatus.NOT_STARTED)
            self.db.add(kyc)
            risk_profile = UserRiskProfile(
                user_id=user.id,
                risk_level=RiskLevel.MEDIUM,
                assessment_date=datetime.utcnow(),
            )
            self.db.add(risk_profile)
            await self.db.commit()
            await self.send_email_verification(user.id)
            logger.info(f"User created successfully: {user.email}")
            return user
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating user: {e}")
            raise

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID with all relationships
        """
        try:
            stmt = (
                select(User)
                .options(
                    selectinload(User.profile),
                    selectinload(User.kyc),
                    selectinload(User.risk_profile),
                )
                .where(and_(User.id == user_id, not User.is_deleted))
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            raise

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address
        """
        try:
            stmt = select(User).where(
                and_(User.email == email.lower(), not User.is_deleted)
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            raise

    async def update_user(self, user_id: str, user_update: UserUpdate) -> User:
        """
        Update user basic information
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            update_data = user_update.dict(exclude_unset=True)
            if "email" in update_data:
                existing_user = await self.get_user_by_email(update_data["email"])
                if existing_user and existing_user.id != user_id:
                    raise ValueError("Email already in use")
                user.email = update_data["email"].lower()
                user.email_verified = False
            if "primary_wallet_address" in update_data:
                user.primary_wallet_address = update_data["primary_wallet_address"]
            user.updated_at = datetime.utcnow()
            await self.db.commit()
            logger.info(f"User updated successfully: {user.email}")
            return user
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating user: {e}")
            raise

    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user profile information
        """
        try:
            stmt = select(UserProfile).where(UserProfile.user_id == user_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            raise

    async def update_user_profile(
        self, user_id: str, profile_update: UserProfileUpdate
    ) -> UserProfile:
        """
        Update user profile information
        """
        try:
            profile = await self.get_user_profile(user_id)
            if not profile:
                profile = UserProfile(user_id=user_id)
                self.db.add(profile)
            update_data = profile_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(profile, field):
                    setattr(profile, field, value)
            profile.updated_at = datetime.utcnow()
            await self.db.commit()
            logger.info(f"User profile updated successfully: {user_id}")
            return profile
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating user profile: {e}")
            raise

    async def get_user_kyc(self, user_id: str) -> Optional[UserKYC]:
        """
        Get user KYC information
        """
        try:
            stmt = select(UserKYC).where(UserKYC.user_id == user_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user KYC: {e}")
            raise

    async def get_user_risk_profile(self, user_id: str) -> Optional[UserRiskProfile]:
        """
        Get user risk profile
        """
        try:
            stmt = select(UserRiskProfile).where(UserRiskProfile.user_id == user_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user risk profile: {e}")
            raise

    async def deactivate_user(self, user_id: str, reason: str) -> None:
        """
        Deactivate user account
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            user.status = UserStatus.DEACTIVATED
            user.status_reason = reason
            user.status_changed_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            await self.db.commit()
            logger.info(f"User deactivated: {user.email}, reason: {reason}")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deactivating user: {e}")
            raise

    async def get_user_activity(
        self, user_id: str, page: int, size: int
    ) -> PaginatedResponse:
        """
        Get user activity history with pagination
        """
        try:
            offset = (page - 1) * size
            count_stmt = select(AuditLog).where(AuditLog.user_id == user_id)
            count_result = await self.db.execute(count_stmt)
            total = len(count_result.all())
            stmt = (
                select(AuditLog)
                .where(AuditLog.user_id == user_id)
                .order_by(AuditLog.created_at.desc())
                .offset(offset)
                .limit(size)
            )
            result = await self.db.execute(stmt)
            activities = result.scalars().all()
            return PaginatedResponse(
                items=[
                    {
                        "id": str(activity.id),
                        "action": activity.action,
                        "resource_type": activity.resource_type,
                        "resource_id": activity.resource_id,
                        "ip_address": activity.ip_address,
                        "created_at": activity.created_at.isoformat(),
                        "metadata": activity.metadata,
                    }
                    for activity in activities
                ],
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size,
            )
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            raise

    async def send_email_verification(self, user_id: str) -> None:
        """
        Send email verification token
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            if user.email_verified:
                raise ValueError("Email already verified")
            token = secrets.token_urlsafe(32)
            cache_key = f"email_verification:{token}"
            await cache.set(cache_key, str(user_id), ttl=86400)
            await self.email_service.send_email_verification(
                user.email, token, user.profile.first_name if user.profile else None
            )
            logger.info(f"Email verification sent to: {user.email}")
        except Exception as e:
            logger.error(f"Error sending email verification: {e}")
            raise

    async def verify_email(self, token: str) -> User:
        """
        Verify email address with token
        """
        try:
            cache_key = f"email_verification:{token}"
            user_id = await cache.get(cache_key)
            if not user_id:
                raise ValueError("Invalid or expired verification token")
            user = await self.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            user.email_verified = True
            user.email_verified_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            if user.status == UserStatus.PENDING:
                user.status = UserStatus.ACTIVE
                user.status_changed_at = datetime.utcnow()
            await self.db.commit()
            await cache.delete(cache_key)
            logger.info(f"Email verified successfully: {user.email}")
            return user
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error verifying email: {e}")
            raise

    async def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> None:
        """
        Change user password
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            if not pwd_context.verify(current_password, user.hashed_password):
                raise ValueError("Current password is incorrect")
            self._validate_password_strength(new_password)
            user.hashed_password = pwd_context.hash(new_password)
            user.password_changed_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            await self.db.commit()
            logger.info(f"Password changed successfully for user: {user.email}")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error changing password: {e}")
            raise

    async def enable_mfa(self, user_id: str) -> Dict[str, Any]:
        """
        Enable multi-factor authentication for user
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            if user.mfa_enabled:
                raise ValueError("MFA is already enabled")
            secret = pyotp.random_base32()
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user.email, issuer_name=settings.app.APP_NAME
            )
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            cache_key = f"mfa_setup:{user_id}"
            await cache.set(cache_key, secret, ttl=600)
            return {
                "secret": secret,
                "qr_code": f"data:image/png;base64,{qr_code_base64}",
                "manual_entry_key": secret,
            }
        except Exception as e:
            logger.error(f"Error enabling MFA: {e}")
            raise

    async def verify_mfa_setup(self, user_id: str, token: str) -> List[str]:
        """
        Verify MFA setup and enable it
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            cache_key = f"mfa_setup:{user_id}"
            secret = await cache.get(cache_key)
            if not secret:
                raise ValueError("MFA setup not found or expired")
            totp = pyotp.TOTP(secret)
            if not totp.verify(token):
                raise ValueError("Invalid MFA token")
            backup_codes = [secrets.token_hex(4) for _ in range(10)]
            hashed_backup_codes = [pwd_context.hash(code) for code in backup_codes]
            user.mfa_enabled = True
            user.mfa_secret = secret
            user.backup_codes = hashed_backup_codes
            user.updated_at = datetime.utcnow()
            await self.db.commit()
            await cache.delete(cache_key)
            logger.info(f"MFA enabled successfully for user: {user.email}")
            return backup_codes
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error verifying MFA setup: {e}")
            raise

    async def disable_mfa(self, user_id: str, password: str) -> None:
        """
        Disable multi-factor authentication
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            if not user.mfa_enabled:
                raise ValueError("MFA is not enabled")
            if not pwd_context.verify(password, user.hashed_password):
                raise ValueError("Password is incorrect")
            user.mfa_enabled = False
            user.mfa_secret = None
            user.backup_codes = None
            user.updated_at = datetime.utcnow()
            await self.db.commit()
            logger.info(f"MFA disabled successfully for user: {user.email}")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error disabling MFA: {e}")
            raise

    def _validate_password_strength(self, password: str) -> None:
        """
        Validate password strength according to security policy
        """
        if len(password) < settings.security.PASSWORD_MIN_LENGTH:
            raise ValueError(
                f"Password must be at least {settings.security.PASSWORD_MIN_LENGTH} characters long"
            )
        if settings.security.PASSWORD_REQUIRE_UPPERCASE and (
            not any((c.isupper() for c in password))
        ):
            raise ValueError("Password must contain at least one uppercase letter")
        if settings.security.PASSWORD_REQUIRE_LOWERCASE and (
            not any((c.islower() for c in password))
        ):
            raise ValueError("Password must contain at least one lowercase letter")
        if settings.security.PASSWORD_REQUIRE_NUMBERS and (
            not any((c.isdigit() for c in password))
        ):
            raise ValueError("Password must contain at least one number")
        if settings.security.PASSWORD_REQUIRE_SPECIAL and (
            not any((c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password))
        ):
            raise ValueError("Password must contain at least one special character")

    async def verify_totp_token(self, user_id: str, token: str) -> bool:
        """
        Verify TOTP token for MFA
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user or not user.mfa_enabled or (not user.mfa_secret):
                return False
            totp = pyotp.TOTP(user.mfa_secret)
            return totp.verify(token)
        except Exception as e:
            logger.error(f"Error verifying TOTP token: {e}")
            return False

    async def verify_backup_code(self, user_id: str, backup_code: str) -> bool:
        """
        Verify backup code for MFA
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user or not user.mfa_enabled or (not user.backup_codes):
                return False
            for stored_code in user.backup_codes:
                if pwd_context.verify(backup_code, stored_code):
                    user.backup_codes.remove(stored_code)
                    user.updated_at = datetime.utcnow()
                    await self.db.commit()
                    return True
            return False
        except Exception as e:
            logger.error(f"Error verifying backup code: {e}")
            return False

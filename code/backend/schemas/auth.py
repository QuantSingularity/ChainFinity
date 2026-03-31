"""
Authentication and authorization schemas
"""

import re
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from .base import BaseSchema


class LoginRequest(BaseModel):
    """Login request schema"""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")
    remember_me: bool = Field(default=False, description="Remember login session")
    mfa_code: Optional[str] = Field(
        None, description="Multi-factor authentication code"
    )

    @field_validator("mfa_code")
    @classmethod
    def validate_mfa_code(cls, v: Any) -> Any:
        if v is not None and (not re.match("^\\d{6}$", v)):
            raise ValueError("MFA code must be 6 digits")
        return v


class RegisterRequest(BaseModel):
    """User registration request schema"""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    confirm_password: str = Field(..., description="Password confirmation")
    wallet_address: Optional[str] = Field(None, description="Primary wallet address")
    terms_accepted: bool = Field(..., description="Terms and conditions acceptance")
    privacy_accepted: bool = Field(..., description="Privacy policy acceptance")
    marketing_consent: bool = Field(
        default=False, description="Marketing communications consent"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Any) -> Any:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search("[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search("[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search("\\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search('[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("confirm_password")
    @classmethod
    def validate_password_match(cls, v: Any, info: Any) -> Any:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("wallet_address")
    @classmethod
    def validate_wallet_address(cls, v: Any) -> Any:
        if v is not None and (not re.match("^0x[a-fA-F0-9]{40}$", v)):
            raise ValueError("Invalid Ethereum wallet address format")
        return v

    @field_validator("terms_accepted")
    @classmethod
    def validate_terms_accepted(cls, v: Any) -> Any:
        if not v:
            raise ValueError("Terms and conditions must be accepted")
        return v

    @field_validator("privacy_accepted")
    @classmethod
    def validate_privacy_accepted(cls, v: Any) -> Any:
        if not v:
            raise ValueError("Privacy policy must be accepted")
        return v


class PasswordChangeRequest(BaseModel):
    """Password change request schema"""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="New password confirmation")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: Any) -> Any:
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search("[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search("[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search("\\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search('[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("confirm_password")
    @classmethod
    def validate_password_match(cls, v: Any, info: Any) -> Any:
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""

    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="New password confirmation")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: Any) -> Any:
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search("[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search("[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search("\\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search('[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("confirm_password")
    @classmethod
    def validate_password_match(cls, v: Any, info: Any) -> Any:
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class MFASetupRequest(BaseModel):
    """MFA setup request schema"""

    password: str = Field(..., description="Current password for verification")


class MFASetupResponse(BaseModel):
    """MFA setup response schema"""

    secret: str = Field(..., description="TOTP secret key")
    qr_code_url: str = Field(..., description="QR code URL for authenticator apps")
    backup_codes: List[str] = Field(
        ..., description="Backup codes for account recovery"
    )


class MFAVerifyRequest(BaseModel):
    """MFA verification request schema"""

    code: str = Field(..., description="TOTP code from authenticator app")

    @field_validator("code")
    @classmethod
    def validate_mfa_code(cls, v: Any) -> Any:
        if not re.match("^\\d{6}$", v):
            raise ValueError("MFA code must be 6 digits")
        return v


class MFADisableRequest(BaseModel):
    """MFA disable request schema"""

    password: str = Field(..., description="Current password for verification")
    code: str = Field(..., description="TOTP code from authenticator app")

    @field_validator("code")
    @classmethod
    def validate_mfa_code(cls, v: Any) -> Any:
        if not re.match("^\\d{6}$", v):
            raise ValueError("MFA code must be 6 digits")
        return v


class Token(BaseModel):
    """JWT token response schema"""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Token payload data schema"""

    email: Optional[str] = None
    user_id: Optional[str] = None
    scopes: List[str] = []


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""

    refresh_token: str = Field(..., description="Refresh token")


class APIKeyCreate(BaseModel):
    """API key creation request schema"""

    name: str = Field(..., min_length=1, max_length=100, description="API key name")
    description: Optional[str] = Field(
        None, max_length=500, description="API key description"
    )
    scopes: List[str] = Field(default=[], description="API key scopes/permissions")
    expires_at: Optional[datetime] = Field(None, description="API key expiration date")


class APIKeyResponse(BaseSchema):
    """API key response schema"""

    id: str
    name: str
    description: Optional[str]
    key_prefix: str
    scopes: List[str]
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime


class SessionInfo(BaseModel):
    """User session information schema"""

    session_id: str
    user_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    is_current: bool


class LoginHistory(BaseModel):
    """Login history schema"""

    timestamp: datetime
    ip_address: str
    user_agent: str
    success: bool
    failure_reason: Optional[str]
    location: Optional[str]


class SecuritySettings(BaseModel):
    """User security settings schema"""

    mfa_enabled: bool
    password_changed_at: datetime
    failed_login_attempts: int
    account_locked: bool
    locked_until: Optional[datetime]
    login_notifications: bool
    suspicious_activity_alerts: bool

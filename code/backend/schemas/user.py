"""
User-related Pydantic schemas
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field
from schemas.base import BaseSchema


class UserCreate(BaseModel):
    """User creation schema"""

    email: EmailStr
    password: str = Field(..., min_length=8)
    wallet_address: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_language: Optional[str] = "en"
    preferred_currency: Optional[str] = "USD"


class UserUpdate(BaseModel):
    """User update schema"""

    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserResponse(BaseSchema):
    """User response schema"""

    id: UUID
    email: str
    email_verified: bool
    status: str
    mfa_enabled: bool
    primary_wallet_address: Optional[str] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UserProfile(BaseSchema):
    """User profile schema"""

    id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    wallet_address: Optional[str]
    created_at: datetime


class UserKYC(BaseModel):
    """User KYC submission schema"""

    document_type: str
    document_number: str
    country: str


class UserRiskProfile(BaseSchema):
    """User risk profile schema"""

    id: UUID
    risk_tolerance: str
    investment_goals: Optional[List[str]]
    created_at: datetime


class UserProfileResponse(UserProfile):
    """User profile response schema"""


class UserProfileUpdate(BaseModel):
    """User profile update schema"""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    country: Optional[str] = None


class UserKYCResponse(BaseSchema):
    """User KYC response schema"""

    id: UUID
    user_id: UUID
    document_type: str
    verification_status: str
    submitted_at: datetime
    verified_at: Optional[datetime] = None


class UserKYCUpdate(BaseModel):
    """User KYC update schema"""

    document_type: Optional[str] = None
    document_number: Optional[str] = None
    country: Optional[str] = None


class UserRiskProfileResponse(UserRiskProfile):
    """User risk profile response schema"""


class UserRiskProfileUpdate(BaseModel):
    """User risk profile update schema"""

    risk_tolerance: Optional[str] = None
    investment_goals: Optional[List[str]] = None
    time_horizon: Optional[str] = None

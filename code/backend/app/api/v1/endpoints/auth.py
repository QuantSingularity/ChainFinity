"""
Authentication endpoints
"""

import logging
from datetime import datetime
from typing import Any

from app.api.dependencies import get_client_info, get_current_user
from config.database import get_async_session
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from models.user import User
from schemas.auth import (
    LoginRequest,
    MFASetupRequest,
    MFASetupResponse,
    MFAVerifyRequest,
    PasswordChangeRequest,
    RefreshTokenRequest,
    RegisterRequest,
    Token,
)
from schemas.base import SuccessResponse
from schemas.user import UserResponse
from services.auth import AuthService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()
auth_service = AuthService()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    request: RegisterRequest,
    client_info: dict = Depends(get_client_info),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Register a new user account
    """
    try:
        user = await auth_service.register_user(
            db=db,
            email=request.email,
            password=request.password,
            wallet_address=request.wallet_address,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            terms_accepted_at=datetime.utcnow() if request.terms_accepted else None,
            privacy_accepted_at=datetime.utcnow() if request.privacy_accepted else None,
            marketing_consent=request.marketing_consent,
        )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=Token)
async def login(
    request: LoginRequest,
    client_info: dict = Depends(get_client_info),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    User login with email and password
    """
    try:
        user, tokens = await auth_service.authenticate_user(
            db=db,
            email=request.email,
            password=request.password,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            mfa_code=request.mfa_code,
        )

        return tokens

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@router.post("/login/form", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    client_info: dict = Depends(get_client_info),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    OAuth2 compatible login endpoint
    """
    try:
        user, tokens = await auth_service.authenticate_user(
            db=db,
            email=form_data.username,
            password=form_data.password,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
        )

        return tokens

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Form login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest, db: AsyncSession = Depends(get_async_session)
) -> Any:
    """
    Refresh access token using refresh token
    """
    try:
        tokens = await auth_service.refresh_token(
            db=db, refresh_token=request.refresh_token
        )

        return tokens

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token refresh failed"
        )


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Logout current user
    """
    try:
        # Extract token from Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header",
            )

        access_token = authorization.split(" ")[1]

        await auth_service.logout_user(
            db=db,
            user=current_user,
            access_token=access_token,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
        )

        return SuccessResponse(message="Logged out successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> Any:
    """
    Get current user information
    """
    return current_user


@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Change user password
    """
    try:
        await auth_service.change_password(
            db=db,
            user=current_user,
            current_password=request.current_password,
            new_password=request.new_password,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
        )

        return SuccessResponse(message="Password changed successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed",
        )


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    request: MFASetupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Set up multi-factor authentication
    """
    try:
        # Verify current password
        from services.auth.password_service import PasswordService

        password_service = PasswordService()

        if not password_service.verify_password(
            request.password, current_user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        # Generate MFA setup
        from services.auth.mfa_service import MFAService

        mfa_service = MFAService()

        secret, qr_code_url, backup_codes = mfa_service.setup_totp(current_user.email)

        # Store secret temporarily (user needs to verify before enabling)
        current_user.mfa_secret = secret
        current_user.backup_codes = backup_codes
        await db.commit()

        return MFASetupResponse(
            secret=secret, qr_code_url=qr_code_url, backup_codes=backup_codes
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA setup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="MFA setup failed"
        )


@router.post("/mfa/verify", response_model=SuccessResponse)
async def verify_mfa(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Verify and enable multi-factor authentication
    """
    try:
        if not current_user.mfa_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA not set up. Please set up MFA first.",
            )

        # Verify TOTP code
        from services.auth.mfa_service import MFAService

        mfa_service = MFAService()

        if not mfa_service.verify_totp(current_user.mfa_secret, request.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code"
            )

        # Enable MFA
        current_user.mfa_enabled = True
        await db.commit()

        return SuccessResponse(message="MFA enabled successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA verification failed",
        )

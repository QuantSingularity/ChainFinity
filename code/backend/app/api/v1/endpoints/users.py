"""
User management API endpoints
Comprehensive user operations including profile management, KYC, and risk assessment
"""

import logging

from app.api.dependencies import get_current_user
from config.database import get_async_session
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from middleware.audit_middleware import audit_log
from models.user import User
from schemas.base import PaginatedResponse, SuccessResponse
from schemas.user import (
    UserKYCResponse,
    UserKYCUpdate,
    UserProfileResponse,
    UserProfileUpdate,
    UserResponse,
    UserRiskProfileResponse,
    UserRiskProfileUpdate,
    UserUpdate,
)
from services.user.user_service import UserService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get current user's profile information
    """
    try:
        # Load user with all relationships
        stmt = (
            select(User)
            .options(
                selectinload(User.profile),
                selectinload(User.kyc),
                selectinload(User.risk_profile),
            )
            .where(User.id == current_user.id)
        )

        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        await audit_log(
            db, current_user.id, "user_profile_viewed", "user", str(user.id)
        )

        return UserResponse.from_orm(user)

    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile",
        )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update current user's basic information
    """
    try:
        user_service = UserService(db)
        updated_user = await user_service.update_user(current_user.id, user_update)

        await audit_log(
            db,
            current_user.id,
            "user_updated",
            "user",
            str(current_user.id),
            new_values=user_update.dict(exclude_unset=True),
        )

        return UserResponse.from_orm(updated_user)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get user's detailed profile information
    """
    try:
        user_service = UserService(db)
        profile = await user_service.get_user_profile(current_user.id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
            )

        return UserProfileResponse.from_orm(profile)

    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile",
        )


@router.put("/me/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update user's profile information
    """
    try:
        user_service = UserService(db)
        updated_profile = await user_service.update_user_profile(
            current_user.id, profile_update
        )

        await audit_log(
            db,
            current_user.id,
            "user_profile_updated",
            "user_profile",
            str(updated_profile.id),
            new_values=profile_update.dict(exclude_unset=True),
        )

        return UserProfileResponse.from_orm(updated_profile)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile",
        )


@router.get("/me/kyc", response_model=UserKYCResponse)
async def get_user_kyc(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get user's KYC verification status and information
    """
    try:
        user_service = UserService(db)
        kyc = await user_service.get_user_kyc(current_user.id)

        if not kyc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KYC information not found",
            )

        return UserKYCResponse.from_orm(kyc)

    except Exception as e:
        logger.error(f"Error getting user KYC: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve KYC information",
        )


@router.post("/me/kyc/submit", response_model=UserKYCResponse)
async def submit_kyc_verification(
    kyc_data: UserKYCUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Submit KYC verification documents and information
    """
    try:
        kyc_service = KYCService(db)
        kyc = await kyc_service.submit_kyc_verification(current_user.id, kyc_data)

        await audit_log(
            db,
            current_user.id,
            "kyc_submitted",
            "user_kyc",
            str(kyc.id),
            new_values={"status": kyc.status.value},
        )

        return UserKYCResponse.from_orm(kyc)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting KYC: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit KYC verification",
        )


@router.get("/me/risk-profile", response_model=UserRiskProfileResponse)
async def get_user_risk_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get user's risk profile and assessment
    """
    try:
        user_service = UserService(db)
        risk_profile = await user_service.get_user_risk_profile(current_user.id)

        if not risk_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Risk profile not found"
            )

        return UserRiskProfileResponse.from_orm(risk_profile)

    except Exception as e:
        logger.error(f"Error getting user risk profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve risk profile",
        )


@router.post("/me/risk-assessment", response_model=UserRiskProfileResponse)
async def request_risk_assessment(
    assessment_data: UserRiskProfileUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Request a new risk assessment for the user
    """
    try:
        risk_service = RiskService(db)
        risk_profile = await risk_service.perform_user_risk_assessment(
            current_user.id, assessment_data
        )

        await audit_log(
            db,
            current_user.id,
            "risk_assessment_requested",
            "user_risk_profile",
            str(risk_profile.id),
            new_values={"risk_level": risk_profile.risk_level.value},
        )

        return UserRiskProfileResponse.from_orm(risk_profile)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error performing risk assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform risk assessment",
        )


@router.post("/me/deactivate", response_model=SuccessResponse)
async def deactivate_user_account(
    reason: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Deactivate user account
    """
    try:
        user_service = UserService(db)
        await user_service.deactivate_user(current_user.id, reason)

        await audit_log(
            db,
            current_user.id,
            "user_deactivated",
            "user",
            str(current_user.id),
            new_values={"status": "deactivated", "reason": reason},
        )

        return SuccessResponse(message="Account deactivated successfully")

    except Exception as e:
        logger.error(f"Error deactivating user account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate account",
        )


@router.get("/me/activity", response_model=PaginatedResponse)
async def get_user_activity(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get user's activity history
    """
    try:
        user_service = UserService(db)
        activities = await user_service.get_user_activity(current_user.id, page, size)

        return activities

    except Exception as e:
        logger.error(f"Error getting user activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user activity",
        )


@router.post("/me/verify-email", response_model=SuccessResponse)
async def request_email_verification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Request email verification
    """
    try:
        user_service = UserService(db)
        await user_service.send_email_verification(current_user.id)

        await audit_log(
            db,
            current_user.id,
            "email_verification_requested",
            "user",
            str(current_user.id),
        )

        return SuccessResponse(message="Email verification sent successfully")

    except Exception as e:
        logger.error(f"Error sending email verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email verification",
        )


@router.post("/verify-email/{token}", response_model=SuccessResponse)
async def verify_email(token: str, db: AsyncSession = Depends(get_async_session)):
    """
    Verify email address with token
    """
    try:
        user_service = UserService(db)
        user = await user_service.verify_email(token)

        await audit_log(db, user.id, "email_verified", "user", str(user.id))

        return SuccessResponse(message="Email verified successfully")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email",
        )


@router.post("/me/change-password", response_model=SuccessResponse)
async def change_password(
    current_password: str = Body(...),
    new_password: str = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Change user password
    """
    try:
        user_service = UserService(db)
        await user_service.change_password(
            current_user.id, current_password, new_password
        )

        await audit_log(
            db, current_user.id, "password_changed", "user", str(current_user.id)
        )

        return SuccessResponse(message="Password changed successfully")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password",
        )


@router.post("/me/enable-mfa", response_model=dict)
async def enable_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Enable multi-factor authentication
    """
    try:
        user_service = UserService(db)
        mfa_data = await user_service.enable_mfa(current_user.id)

        await audit_log(
            db, current_user.id, "mfa_enabled", "user", str(current_user.id)
        )

        return mfa_data

    except Exception as e:
        logger.error(f"Error enabling MFA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable MFA",
        )


@router.post("/me/verify-mfa", response_model=SuccessResponse)
async def verify_mfa_setup(
    token: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Verify MFA setup with TOTP token
    """
    try:
        user_service = UserService(db)
        backup_codes = await user_service.verify_mfa_setup(current_user.id, token)

        await audit_log(
            db, current_user.id, "mfa_verified", "user", str(current_user.id)
        )

        return {"message": "MFA verified successfully", "backup_codes": backup_codes}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying MFA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify MFA",
        )


@router.post("/me/disable-mfa", response_model=SuccessResponse)
async def disable_mfa(
    password: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Disable multi-factor authentication
    """
    try:
        user_service = UserService(db)
        await user_service.disable_mfa(current_user.id, password)

        await audit_log(
            db, current_user.id, "mfa_disabled", "user", str(current_user.id)
        )

        return SuccessResponse(message="MFA disabled successfully")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error disabling MFA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable MFA",
        )

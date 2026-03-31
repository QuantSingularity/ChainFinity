"""
API dependencies for authentication and common functionality
"""

import logging
from typing import Dict

from config.database import get_async_session
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from models.user import User
from services.auth import AuthService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
security = HTTPBearer()
auth_service = AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """
    Get current authenticated user
    """
    try:
        token = credentials.credentials
        user = await auth_service.verify_current_user(db, token)
        return user
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user (additional check for user status)
    """
    if not current_user.is_active():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


def get_client_info(request: Request) -> Dict[str, str]:
    """
    Extract client information from request
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    else:
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            ip_address = real_ip
        else:
            ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")
    return {"ip_address": ip_address, "user_agent": user_agent}


class PermissionChecker:
    """
    Permission checker for role-based access control
    """

    def __init__(self, required_permissions: list) -> None:
        self.required_permissions = required_permissions

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        """
        Check if user has required permissions
        """
        if hasattr(current_user, "is_admin") and current_user.is_admin:
            return current_user
        for permission in self.required_permissions:
            if not self._user_has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission} required",
                )
        return current_user

    def _user_has_permission(self, user: User, permission: str) -> bool:
        """
        Check if user has specific permission
        """
        basic_permissions = [
            "read_own_data",
            "update_own_profile",
            "view_own_transactions",
            "manage_own_portfolio",
        ]
        if permission in basic_permissions:
            return user.is_active()
        admin_permissions = [
            "read_all_users",
            "manage_compliance",
            "view_audit_logs",
            "manage_risk_settings",
        ]
        if permission in admin_permissions:
            return hasattr(user, "is_admin") and user.is_admin
        return False


require_admin = PermissionChecker(["admin_access"])
require_compliance_access = PermissionChecker(["manage_compliance"])
require_risk_access = PermissionChecker(["manage_risk_settings"])

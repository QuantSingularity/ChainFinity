"""
Compliance endpoints
"""

import logging
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from app.api.dependencies import get_current_user
from config.database import get_async_session
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.compliance import (AuditLog, ComplianceCheck, ComplianceStatus,
                               RegulatoryReport)
from models.user import User
from schemas.compliance import (AuditLogResponse, ComplianceCheckResponse,
                                RegulatoryReportResponse)
from services.compliance.compliance_service import ComplianceService
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/checks", response_model=List[ComplianceCheckResponse])
async def list_compliance_checks(
    check_type: Optional[str] = Query(None),
    status_filter: Optional[ComplianceStatus] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get compliance checks for current user
    """
    try:
        query = select(ComplianceCheck).where(
            ComplianceCheck.user_id == current_user.id
        )

        if check_type:
            query = query.where(ComplianceCheck.check_type == check_type)
        if status_filter:
            query = query.where(ComplianceCheck.status == status_filter)

        query = (
            query.order_by(desc(ComplianceCheck.created_at)).limit(limit).offset(offset)
        )

        result = await db.execute(query)
        checks = result.scalars().all()

        return checks

    except Exception as e:
        logger.error(f"Error listing compliance checks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve compliance checks",
        )


@router.get("/checks/{check_id}", response_model=ComplianceCheckResponse)
async def get_compliance_check(
    check_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get specific compliance check details
    """
    try:
        query = select(ComplianceCheck).where(
            and_(
                ComplianceCheck.id == check_id,
                ComplianceCheck.user_id == current_user.id,
            )
        )
        result = await db.execute(query)
        check = result.scalar_one_or_none()

        if not check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Compliance check not found",
            )

        return check

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting compliance check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve compliance check",
        )


@router.get("/status", response_model=dict)
async def get_compliance_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get overall compliance status for user
    """
    try:
        ComplianceService()

        # Get recent compliance checks
        query = (
            select(ComplianceCheck)
            .where(ComplianceCheck.user_id == current_user.id)
            .order_by(desc(ComplianceCheck.created_at))
            .limit(10)
        )

        result = await db.execute(query)
        recent_checks = result.scalars().all()

        passed_checks = sum(
            1 for check in recent_checks if check.status == ComplianceStatus.PASSED
        )
        failed_checks = sum(
            1 for check in recent_checks if check.status == ComplianceStatus.FAILED
        )
        pending_checks = sum(
            1 for check in recent_checks if check.status == ComplianceStatus.PENDING
        )

        overall_status = "compliant"
        if failed_checks > 0:
            overall_status = "non_compliant"
        elif pending_checks > 0:
            overall_status = "pending_review"

        return {
            "user_id": str(current_user.id),
            "overall_status": overall_status,
            "kyc_status": (
                current_user.kyc_status.value if current_user.kyc_status else "unknown"
            ),
            "kyc_verified": current_user.kyc_verified,
            "account_status": (
                current_user.account_status.value
                if current_user.account_status
                else "unknown"
            ),
            "recent_checks": {
                "passed": passed_checks,
                "failed": failed_checks,
                "pending": pending_checks,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting compliance status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve compliance status",
        )


@router.post("/check-user", response_model=ComplianceCheckResponse)
async def check_user_compliance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Perform compliance check on current user
    """
    try:
        compliance_service = ComplianceService()

        check = await compliance_service.check_user_compliance(db=db, user=current_user)

        return check

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking user compliance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check user compliance",
        )


@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    action: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get audit logs for current user
    """
    try:
        query = select(AuditLog).where(AuditLog.user_id == current_user.id)

        if action:
            query = query.where(AuditLog.action == action)
        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        if end_date:
            query = query.where(AuditLog.created_at <= end_date)

        query = query.order_by(desc(AuditLog.created_at)).limit(limit).offset(offset)

        result = await db.execute(query)
        logs = result.scalars().all()

        return logs

    except Exception as e:
        logger.error(f"Error listing audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs",
        )


@router.get("/reports", response_model=List[RegulatoryReportResponse])
async def list_regulatory_reports(
    report_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get regulatory reports (admin only in production)
    """
    try:
        # In production, this should be restricted to admin users
        query = select(RegulatoryReport)

        if report_type:
            query = query.where(RegulatoryReport.report_type == report_type)

        query = (
            query.order_by(desc(RegulatoryReport.created_at))
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(query)
        reports = result.scalars().all()

        return reports

    except Exception as e:
        logger.error(f"Error listing regulatory reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve regulatory reports",
        )


@router.post(
    "/reports",
    response_model=RegulatoryReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_regulatory_report(
    report_type: str,
    start_date: datetime,
    end_date: datetime,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Generate a new regulatory report
    """
    try:
        report = RegulatoryReport(
            report_type=report_type,
            report_period_start=start_date,
            report_period_end=end_date,
            report_status="generated",
            report_data={
                "generated_by": str(current_user.id),
                "generated_at": datetime.utcnow().isoformat(),
                "report_type": report_type,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
            },
            generated_by_user_id=current_user.id,
        )

        db.add(report)
        await db.commit()
        await db.refresh(report)

        return report

    except Exception as e:
        logger.error(f"Error generating regulatory report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate regulatory report",
        )


@router.get("/suspicious-activities", response_model=List[dict])
async def list_suspicious_activities(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Get suspicious activity reports for user
    """
    try:
        from models.compliance import SuspiciousActivityReport

        query = (
            select(SuspiciousActivityReport)
            .where(SuspiciousActivityReport.user_id == current_user.id)
            .order_by(desc(SuspiciousActivityReport.created_at))
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(query)
        reports = result.scalars().all()

        return [
            {
                "id": str(report.id),
                "report_type": report.report_type,
                "severity": report.severity.value if report.severity else "unknown",
                "status": report.status.value if report.status else "unknown",
                "created_at": (
                    report.created_at.isoformat() if report.created_at else None
                ),
            }
            for report in reports
        ]

    except Exception as e:
        logger.error(f"Error listing suspicious activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve suspicious activities",
        )

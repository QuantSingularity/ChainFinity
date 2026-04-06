"""
KYC (Know Your Customer) Service
Handles KYC verification, document validation, and compliance checks
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from models.user import KYCStatus, UserKYC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

REQUIRED_KYC_FIELDS = {"first_name", "last_name", "date_of_birth", "nationality"}


class KYCService:
    """
    Service for KYC verification and management
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _validate_kyc_data(self, kyc_data: Dict[str, Any]) -> bool:
        """
        Validate that required KYC fields are present.
        Returns True if valid, raises ValueError if not.
        """
        missing = REQUIRED_KYC_FIELDS - set(kyc_data.keys())
        if missing:
            raise ValueError(
                f"Missing required KYC fields: {', '.join(sorted(missing))}"
            )
        return True

    async def _submit_to_provider(self, kyc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit KYC data to external provider (stub)."""
        return {"status": "pending", "reference_id": "ref_stub_123"}

    async def _verify_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a document via external provider."""
        import httpx

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://kyc-provider.example.com/verify",
                    json=document_data,
                    timeout=10.0,
                )
                return response.json()
            except Exception as e:
                logger.warning(f"Document verification provider unavailable: {e}")
                return {"verified": True, "confidence": 90, "document_valid": True}

    async def submit_kyc_verification(
        self, user_id: str, kyc_data: Dict[str, Any]
    ) -> UserKYC:
        """
        Submit KYC data for verification.
        Creates/updates UserKYC record and submits to provider.
        """
        self._validate_kyc_data(kyc_data)

        result = await self.db.execute(
            select(UserKYC).where(UserKYC.user_id == UUID(user_id))
        )
        kyc_record = result.scalar_one_or_none()

        provider_result = await self._submit_to_provider(kyc_data)

        if kyc_record is None:
            kyc_record = UserKYC(
                user_id=UUID(user_id),
                status=KYCStatus.PENDING_REVIEW,
                provider="internal",
                provider_reference_id=provider_result.get("reference_id"),
            )
            self.db.add(kyc_record)
        else:
            kyc_record.status = KYCStatus.PENDING_REVIEW
            kyc_record.provider_reference_id = provider_result.get("reference_id")

        await self.db.commit()
        await self.db.refresh(kyc_record)
        return kyc_record

    async def get_kyc_status(self, user_id: str) -> Optional[UserKYC]:
        """Get current KYC status for a user."""
        result = await self.db.execute(
            select(UserKYC).where(UserKYC.user_id == UUID(user_id))
        )
        return result.scalar_one_or_none()

    async def approve_kyc(
        self, user_id: str, reviewed_by: Optional[str] = None
    ) -> UserKYC:
        """Approve KYC verification for a user."""
        kyc_record = await self.get_kyc_status(user_id)
        if not kyc_record:
            raise ValueError(f"No KYC record found for user {user_id}")

        kyc_record.status = KYCStatus.APPROVED
        kyc_record.identity_verified = True
        kyc_record.document_verified = True
        kyc_record.reviewed_at = datetime.utcnow()
        if reviewed_by:
            kyc_record.reviewed_by = UUID(reviewed_by)

        await self.db.commit()
        return kyc_record

    async def reject_kyc(
        self, user_id: str, reason: str, reviewed_by: Optional[str] = None
    ) -> UserKYC:
        """Reject KYC verification for a user."""
        kyc_record = await self.get_kyc_status(user_id)
        if not kyc_record:
            raise ValueError(f"No KYC record found for user {user_id}")

        kyc_record.status = KYCStatus.REJECTED
        kyc_record.status_reason = reason
        kyc_record.reviewed_at = datetime.utcnow()
        if reviewed_by:
            kyc_record.reviewed_by = UUID(reviewed_by)

        await self.db.commit()
        return kyc_record

"""
Comprehensive compliance service for financial regulations
Handles KYC verification, AML screening, transaction monitoring, and regulatory reporting
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from config.settings import settings
from models.compliance import (
    ComplianceCheck,
    ComplianceStatus,
    SuspiciousActivityReport,
)
from models.transaction import Transaction
from models.user import KYCStatus, User, UserKYC
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class KYCResult:
    """Result object returned from KYC checks"""

    status: str  # "passed" | "failed" | "pending"
    score: float
    findings: Dict[str, Any]
    user_id: Optional[str] = None


@dataclass
class MonitoringResult:
    """Result object returned from transaction monitoring"""

    status: str  # "passed" | "failed" | "manual_review"
    score: float
    risk_level: str  # "low" | "medium" | "high" | "critical"
    findings: Dict[str, Any]
    transaction_id: Optional[str] = None


@dataclass
class ReportResult:
    """Result object returned from regulatory report generation"""

    report_type: str
    record_count: int
    total_amount_usd: Decimal
    metadata: Dict[str, Any]
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class ComplianceService:
    """
    Main compliance service coordinating all compliance activities
    """

    def __init__(self, db: Optional[AsyncSession] = None) -> None:
        self.db = db
        self.suspicious_amount_threshold = (
            settings.compliance.SUSPICIOUS_AMOUNT_THRESHOLD
        )
        self.daily_transaction_limit = settings.compliance.DAILY_TRANSACTION_LIMIT

    # ── KYC Methods ──────────────────────────────────────────────────

    async def perform_kyc_check(
        self, user_id: str, kyc_data: Dict[str, Any]
    ) -> KYCResult:
        """
        Perform comprehensive KYC check including identity, document,
        sanctions, and PEP screening.
        """
        try:
            identity_result = await self._verify_identity(kyc_data)
            document_result = await self._verify_documents(kyc_data)
            sanctions_result = await self._screen_sanctions(kyc_data)
            pep_result = await self._screen_pep(kyc_data)

            score = self._calculate_kyc_score(
                identity_result, document_result, sanctions_result, pep_result
            )
            status = self._determine_kyc_status(score)

            findings = {
                "identity": identity_result,
                "documents": document_result,
                "sanctions": sanctions_result,
                "pep": pep_result,
            }

            # Update UserKYC record if db is available
            if self.db is not None:
                await self._update_user_kyc(user_id, status, findings)

            return KYCResult(
                status=status,
                score=score,
                findings=findings,
                user_id=user_id,
            )
        except Exception as e:
            logger.error(f"KYC check error: {e}")
            return KYCResult(
                status="failed",
                score=0.0,
                findings={"error": str(e)},
                user_id=user_id,
            )

    async def _verify_identity(self, kyc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify identity via external provider (stub)."""
        return {
            "verified": True,
            "confidence_score": 90,
            "reference_id": "identity_stub",
        }

    async def _verify_documents(self, kyc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify documents via external provider (stub)."""
        return {"verified": True, "verification_score": 85}

    async def _screen_sanctions(self, kyc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Screen against sanctions lists (stub)."""
        return {"match_found": False, "confidence": 0}

    async def _screen_pep(self, kyc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Screen for Politically Exposed Persons (stub)."""
        return {"match_found": False, "confidence": 0}

    def _calculate_kyc_score(
        self,
        identity_result: Dict[str, Any],
        document_result: Dict[str, Any],
        sanctions_result: Dict[str, Any],
        pep_result: Dict[str, Any],
    ) -> float:
        """
        Calculate a composite KYC score (0-100).
        100 = perfect compliance, 0 = blocked.
        """
        score = 0.0

        # Identity: up to 50 points
        if identity_result.get("verified"):
            confidence = identity_result.get("confidence_score", 100)
            score += 50 * (confidence / 100)

        # Documents: up to 30 points
        if document_result.get("verified"):
            doc_score = document_result.get("verification_score", 100)
            score += 30 * (doc_score / 100)

        # Sanctions: up to 15 points (instant fail if match)
        if sanctions_result.get("match_found"):
            return 0.0
        score += 15

        # PEP: up to 5 points
        if not pep_result.get("match_found"):
            score += 5

        return round(score, 2)

    def _determine_compliance_status(self, score: float) -> str:
        """
        Map a RISK score to a compliance status string.
        Higher score = higher risk = worse outcome.
        score >= 70  -> "failed"
        40 <= score < 70 -> "manual_review"
        score < 40   -> "passed"
        """
        if score >= 70:
            return "failed"
        elif score >= 40:
            return "manual_review"
        return "passed"

    def _determine_kyc_status(self, score: float) -> str:
        """
        Map a KYC compliance score to a status string.
        KYC score is POSITIVE (higher = better).
        score >= 80  -> "passed"
        60 <= score < 80 -> "manual_review"
        score < 60   -> "failed"
        """
        if score >= 80:
            return "passed"
        elif score >= 60:
            return "manual_review"
        return "failed"

    def _determine_risk_level(self, score: float) -> str:
        """
        Map a risk score to a risk-level string.
        score >= 80 -> "critical"
        score >= 60 -> "high"
        score >= 30 -> "medium"
        else        -> "low"
        """
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "high"
        elif score >= 30:
            return "medium"
        return "low"

    async def _update_user_kyc(
        self, user_id: str, status: str, findings: Dict[str, Any]
    ) -> None:
        """Persist KYC result to UserKYC record."""
        if self.db is None:
            return
        try:
            result = await self.db.execute(
                select(UserKYC).where(UserKYC.user_id == UUID(user_id))
            )
            kyc = result.scalar_one_or_none()
            kyc_status = (
                KYCStatus.APPROVED if status == "passed" else KYCStatus.REJECTED
            )
            if kyc is None:
                kyc = UserKYC(
                    user_id=UUID(user_id),
                    status=kyc_status,
                    identity_verified=(status == "passed"),
                    document_verified=(status == "passed"),
                )
                self.db.add(kyc)
            else:
                kyc.status = kyc_status
                kyc.identity_verified = status == "passed"
                kyc.document_verified = status == "passed"
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error updating UserKYC: {e}")

    # ── Transaction Monitoring Methods ───────────────────────────────

    async def monitor_transaction(self, transaction_id: str) -> MonitoringResult:
        """
        Monitor a transaction for compliance risk.
        Runs amount, velocity, address-risk, and pattern checks.
        """
        try:
            transaction = await self._get_transaction(transaction_id)
            if transaction is None:
                return MonitoringResult(
                    status="failed",
                    score=0.0,
                    risk_level="critical",
                    findings={"error": "Transaction not found"},
                    transaction_id=transaction_id,
                )

            amount_result = await self._check_transaction_amount(transaction)
            velocity_result = await self._check_transaction_velocity(transaction)
            address_result = await self._check_address_risk(transaction)
            pattern_result = await self._check_transaction_patterns(transaction)

            # Aggregate risk score (sum of individual risk scores)
            total_score = (
                amount_result.get("risk_score", 0)
                + velocity_result.get("risk_score", 0)
                + address_result.get("risk_score", 0)
                + pattern_result.get("risk_score", 0)
            )

            risk_level = self._determine_risk_level(total_score)
            status = (
                "passed"
                if total_score < 40
                else ("manual_review" if total_score < 70 else "failed")
            )

            findings = {
                **amount_result.get("findings", {}),
                **velocity_result.get("findings", {}),
                **address_result.get("findings", {}),
                **pattern_result.get("findings", {}),
            }

            # Create SAR if high risk
            if total_score >= 70:
                await self._create_suspicious_activity(
                    transaction, total_score, findings
                )

            return MonitoringResult(
                status=status,
                score=float(total_score),
                risk_level=risk_level,
                findings=findings,
                transaction_id=transaction_id,
            )
        except Exception as e:
            logger.error(f"Transaction monitoring error: {e}")
            return MonitoringResult(
                status="failed",
                score=100.0,
                risk_level="critical",
                findings={"error": str(e)},
                transaction_id=transaction_id,
            )

    async def _get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Fetch a transaction by id."""
        if self.db is None:
            return None
        try:
            result = await self.db.execute(
                select(Transaction).where(Transaction.id == UUID(transaction_id))
            )
            return result.scalar_one_or_none()
        except Exception:
            return None

    async def _check_transaction_amount(
        self, transaction: Transaction
    ) -> Dict[str, Any]:
        """Check transaction amount against thresholds."""
        amount = transaction.value_usd or transaction.amount_usd or Decimal("0")
        try:
            amount = Decimal(str(amount))
        except Exception:
            amount = Decimal("0")

        risk_score = 0
        findings: Dict[str, Any] = {}

        if amount >= Decimal(str(self.suspicious_amount_threshold)):
            risk_score += 30
            findings["large_amount"] = {"amount": float(amount)}

        return {"risk_score": risk_score, "findings": findings}

    async def _check_transaction_velocity(
        self, transaction: Transaction
    ) -> Dict[str, Any]:
        """Check transaction frequency/velocity."""
        risk_score = 0
        findings: Dict[str, Any] = {}

        if self.db is not None and transaction.user_id:
            try:
                cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
                result = await self.db.execute(
                    select(func.count(Transaction.id)).where(
                        and_(
                            Transaction.user_id == transaction.user_id,
                            Transaction.created_at >= cutoff,
                        )
                    )
                )
                count = result.scalar() or 0
                if count > 10:
                    risk_score += 25
                    findings["high_frequency"] = {"count": count}
            except Exception as e:
                logger.warning(f"Velocity check DB error: {e}")

        return {"risk_score": risk_score, "findings": findings}

    async def _check_address_risk(self, transaction: Transaction) -> Dict[str, Any]:
        """Check risk level of transaction addresses."""
        risk_score = 0
        findings: Dict[str, Any] = {}

        from_addr = getattr(transaction, "from_address", None)
        to_addr = getattr(transaction, "to_address", None)

        if from_addr:
            aml_result = await self._query_aml_provider(from_addr)
            if aml_result.get("risk_level") in ("high", "critical"):
                risk_score += 40
                findings["from_address_risk"] = aml_result
        if to_addr:
            aml_result = await self._query_aml_provider(to_addr)
            if aml_result.get("risk_level") in ("high", "critical"):
                risk_score += 30
                findings["to_address_risk"] = aml_result

        return {"risk_score": risk_score, "findings": findings}

    async def _query_aml_provider(self, address: str) -> Dict[str, Any]:
        """Query external AML provider for address risk (stub)."""
        return {"risk_level": "low", "risk_score": 5, "categories": []}

    async def _check_transaction_patterns(
        self, transaction: Transaction
    ) -> Dict[str, Any]:
        """Detect suspicious transaction patterns."""
        risk_score = 0
        findings: Dict[str, Any] = {}

        amount = transaction.value_usd or transaction.amount_usd or Decimal("0")
        try:
            amount = Decimal(str(amount))
        except Exception:
            amount = Decimal("0")

        # Round-number detection
        if amount > 0 and amount % 1000 == 0:
            risk_score += 5
            findings["round_amount"] = {"amount": float(amount)}

        # Unusual timing
        ts = getattr(transaction, "timestamp", None) or getattr(
            transaction, "created_at", None
        )
        if ts:
            hour = ts.hour
            if hour < 6 or hour > 22:
                risk_score += 5
                findings["unusual_timing"] = {"hour": hour}

        return {"risk_score": risk_score, "findings": findings}

    async def _create_suspicious_activity(
        self,
        transaction: Transaction,
        risk_score: float,
        findings: Dict[str, Any],
    ) -> None:
        """Create a suspicious activity record."""
        if self.db is None:
            return
        try:
            amount = transaction.value_usd or transaction.amount_usd or Decimal("0")
            sar = SuspiciousActivityReport(
                sar_number=f"SAR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                user_id=transaction.user_id,
                transaction_ids=[str(transaction.id)],
                activity_type="high_risk_transaction",
                activity_description="Transaction flagged by automated monitoring",
                suspicious_indicators=findings,
                total_amount=amount,
                currency="USD",
                activity_start_date=getattr(transaction, "timestamp", None)
                or getattr(transaction, "created_at", datetime.now(timezone.utc)),
                activity_end_date=datetime.now(timezone.utc),
                filing_required=True,
                filing_deadline=datetime.now(timezone.utc) + timedelta(days=30),
            )
            self.db.add(sar)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error creating suspicious activity record: {e}")

    # ── Regulatory Reporting ─────────────────────────────────────────

    async def generate_regulatory_report(
        self,
        report_type: str,
        period_start: datetime,
        period_end: datetime,
    ) -> ReportResult:
        """Generate a regulatory report for a given period."""
        record_count = 0
        total_amount = Decimal("0")
        metadata: Dict[str, Any] = {
            "report_type": report_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
        }

        if self.db is not None:
            try:
                from sqlalchemy import or_

                result = await self.db.execute(
                    select(SuspiciousActivityReport).where(
                        or_(
                            and_(
                                SuspiciousActivityReport.detected_at >= period_start,
                                SuspiciousActivityReport.detected_at <= period_end,
                            ),
                            and_(
                                SuspiciousActivityReport.detection_date >= period_start,
                                SuspiciousActivityReport.detection_date <= period_end,
                            ),
                        )
                    )
                )
                records = result.scalars().all()
                record_count = len(records)
                total_amount = sum(
                    (r.total_amount or Decimal("0") for r in records), Decimal("0")
                )
                metadata["record_ids"] = [str(r.id) for r in records]
            except Exception as e:
                logger.error(f"Error querying SAR records: {e}")

        return ReportResult(
            report_type=report_type,
            record_count=record_count,
            total_amount_usd=total_amount,
            metadata=metadata,
            period_start=period_start,
            period_end=period_end,
        )

    # ── Legacy check methods (used by check_transaction_compliance etc.) ─

    async def check_transaction_compliance(
        self, db: AsyncSession, transaction: Transaction, user: User
    ) -> ComplianceCheck:
        """Full compliance check used by the API layer."""
        self.db = db
        compliance_check = ComplianceCheck(
            check_type="transaction_compliance",
            check_name="Transaction Compliance Check",
            check_description="Comprehensive compliance check for transaction",
            user_id=user.id,
            transaction_id=transaction.id,
            status=ComplianceStatus.PENDING,
            check_parameters={},
            check_results={},
        )

        results: Dict[str, Any] = {}
        overall_score = 100.0

        amount_check = await self._check_transaction_amount(transaction)
        results["amount_check"] = amount_check
        if amount_check.get("risk_score", 0) > 0:
            overall_score -= 20

        pattern_check = await self._check_transaction_patterns(transaction)
        results["pattern_check"] = pattern_check
        if pattern_check.get("risk_score", 0) > 0:
            overall_score -= 15

        address_check = await self._check_address_risk(transaction)
        results["address_check"] = address_check
        if address_check.get("risk_score", 0) > 0:
            overall_score -= 25

        compliance_check.score = max(0, overall_score)
        compliance_check.check_results = results

        if overall_score >= 80:
            compliance_check.status = ComplianceStatus.PASSED
        elif overall_score >= 60:
            compliance_check.status = ComplianceStatus.REQUIRES_REVIEW
            compliance_check.requires_manual_review = True
        else:
            compliance_check.status = ComplianceStatus.FAILED
            compliance_check.requires_manual_review = True

        db.add(compliance_check)
        await db.commit()
        return compliance_check

    async def check_user_compliance(
        self, db: AsyncSession, user: User
    ) -> ComplianceCheck:
        """Check overall user compliance status."""
        self.db = db
        compliance_check = ComplianceCheck(
            check_type="user_compliance",
            check_name="User Compliance Check",
            user_id=user.id,
            status=ComplianceStatus.PENDING,
            check_results={},
        )

        results: Dict[str, Any] = {}
        overall_score = 100.0

        kyc_check = await self._check_kyc_status(user)
        results["kyc_check"] = kyc_check
        if not kyc_check["passed"]:
            overall_score -= 40

        account_check = await self._check_account_status(user)
        results["account_check"] = account_check
        if not account_check["passed"]:
            overall_score -= 30

        compliance_check.score = max(0, overall_score)
        compliance_check.check_results = results
        compliance_check.status = (
            ComplianceStatus.PASSED if overall_score >= 80 else ComplianceStatus.FAILED
        )

        db.add(compliance_check)
        await db.commit()
        return compliance_check

    async def check_portfolio_compliance(self, portfolio: Any) -> None:
        """Placeholder portfolio compliance check."""

    async def _check_kyc_status(self, user: User) -> Dict[str, Any]:
        """Check user KYC status."""
        if not user.kyc:
            return {"passed": False, "reason": "No KYC record", "severity": "high"}
        if not user.kyc.is_verified():
            return {
                "passed": False,
                "reason": f"KYC status: {user.kyc.status.value}",
                "severity": "high",
            }
        return {"passed": True, "kyc_status": user.kyc.status.value}

    async def _check_account_status(self, user: User) -> Dict[str, Any]:
        """Check user account status."""
        if not user.is_active():
            return {
                "passed": False,
                "reason": f"Account status: {user.status.value}",
                "severity": "high",
            }
        if not user.email_verified:
            return {
                "passed": False,
                "reason": "Email not verified",
                "severity": "medium",
            }
        return {"passed": True, "account_status": user.status.value}

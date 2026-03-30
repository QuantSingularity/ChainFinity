"""
Comprehensive compliance service for financial regulations
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List
from config.settings import settings
from models.compliance import (
    ComplianceCheck,
    ComplianceStatus,
    SuspiciousActivityReport,
)
from models.risk import RiskLevel
from models.transaction import Transaction, TransactionStatus
from models.user import User
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ComplianceService:
    """
    Main compliance service coordinating all compliance activities
    """

    def __init__(self) -> None:
        self.suspicious_amount_threshold = (
            settings.compliance.SUSPICIOUS_AMOUNT_THRESHOLD
        )
        self.daily_transaction_limit = settings.compliance.DAILY_TRANSACTION_LIMIT

    async def check_transaction_compliance(
        self, db: AsyncSession, transaction: Transaction, user: User
    ) -> ComplianceCheck:
        """
        Comprehensive transaction compliance check
        """
        try:
            compliance_check = ComplianceCheck(
                check_type="transaction_compliance",
                check_name="Transaction Compliance Check",
                check_description="Comprehensive compliance check for transaction",
                user_id=user.id,
                transaction_id=transaction.id,
                status=ComplianceStatus.PENDING,
                check_parameters={
                    "transaction_amount": str(transaction.amount_usd),
                    "transaction_type": transaction.transaction_type.value,
                    "user_risk_level": (
                        user.risk_profile.risk_level.value
                        if user.risk_profile
                        else "unknown"
                    ),
                },
                check_results={},
            )
            results = {}
            overall_score = 100.0
            amount_check = await self._check_transaction_amount(transaction, user)
            results["amount_check"] = amount_check
            if not amount_check["passed"]:
                overall_score -= 20
            frequency_check = await self._check_transaction_frequency(
                db, transaction, user
            )
            results["frequency_check"] = frequency_check
            if not frequency_check["passed"]:
                overall_score -= 15
            pattern_check = await self._check_transaction_patterns(
                db, transaction, user
            )
            results["pattern_check"] = pattern_check
            if not pattern_check["passed"]:
                overall_score -= 25
            sanctions_check = await self._check_sanctions_screening(transaction)
            results["sanctions_check"] = sanctions_check
            if not sanctions_check["passed"]:
                overall_score -= 40
            risk_check = await self._check_risk_based_rules(transaction, user)
            results["risk_check"] = risk_check
            if not risk_check["passed"]:
                overall_score -= 30
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
            if (
                overall_score < 50
                or transaction.amount_usd >= self.suspicious_amount_threshold
            ):
                await self._create_suspicious_activity_report(
                    db, transaction, user, results
                )
            db.add(compliance_check)
            await db.commit()
            return compliance_check
        except Exception as e:
            logger.error(f"Compliance check error: {e}")
            compliance_check = ComplianceCheck(
                check_type="transaction_compliance",
                check_name="Transaction Compliance Check",
                status=ComplianceStatus.FAILED,
                user_id=user.id,
                transaction_id=transaction.id,
                check_results={"error": str(e)},
            )
            db.add(compliance_check)
            await db.commit()
            return compliance_check

    async def check_user_compliance(
        self, db: AsyncSession, user: User
    ) -> ComplianceCheck:
        """
        Check user compliance status
        """
        try:
            compliance_check = ComplianceCheck(
                check_type="user_compliance",
                check_name="User Compliance Check",
                check_description="Comprehensive user compliance verification",
                user_id=user.id,
                status=ComplianceStatus.PENDING,
                check_results={},
            )
            results = {}
            overall_score = 100.0
            kyc_check = await self._check_kyc_status(user)
            results["kyc_check"] = kyc_check
            if not kyc_check["passed"]:
                overall_score -= 40
            risk_check = await self._check_user_risk_status(user)
            results["risk_check"] = risk_check
            if not risk_check["passed"]:
                overall_score -= 20
            account_check = await self._check_account_status(user)
            results["account_check"] = account_check
            if not account_check["passed"]:
                overall_score -= 30
            history_check = await self._check_compliance_history(db, user)
            results["history_check"] = history_check
            if not history_check["passed"]:
                overall_score -= 10
            compliance_check.score = max(0, overall_score)
            compliance_check.check_results = results
            if overall_score >= 90:
                compliance_check.status = ComplianceStatus.PASSED
            elif overall_score >= 70:
                compliance_check.status = ComplianceStatus.REQUIRES_REVIEW
                compliance_check.requires_manual_review = True
            else:
                compliance_check.status = ComplianceStatus.FAILED
                compliance_check.requires_manual_review = True
            db.add(compliance_check)
            await db.commit()
            return compliance_check
        except Exception as e:
            logger.error(f"User compliance check error: {e}")
            compliance_check = ComplianceCheck(
                check_type="user_compliance",
                check_name="User Compliance Check",
                status=ComplianceStatus.FAILED,
                user_id=user.id,
                check_results={"error": str(e)},
            )
            db.add(compliance_check)
            await db.commit()
            return compliance_check

    async def monitor_ongoing_compliance(
        self, db: AsyncSession, user: User
    ) -> Dict[str, Any]:
        """
        Ongoing compliance monitoring for user
        """
        try:
            monitoring_results = {
                "user_id": str(user.id),
                "monitoring_date": datetime.utcnow().isoformat(),
                "alerts": [],
                "recommendations": [],
            }
            if user.kyc and user.kyc.is_expired():
                monitoring_results["alerts"].append(
                    {
                        "type": "kyc_expired",
                        "severity": "high",
                        "message": "KYC verification has expired",
                        "action_required": "Renew KYC verification",
                    }
                )
            recent_transactions = await self._get_recent_transactions(db, user, days=30)
            if len(recent_transactions) > 100:
                monitoring_results["alerts"].append(
                    {
                        "type": "high_transaction_frequency",
                        "severity": "medium",
                        "message": f"High transaction frequency: {len(recent_transactions)} in 30 days",
                        "action_required": "Review transaction patterns",
                    }
                )
            large_transactions = [
                t for t in recent_transactions if t.amount_usd and t.amount_usd >= 10000
            ]
            if large_transactions:
                monitoring_results["alerts"].append(
                    {
                        "type": "large_transactions",
                        "severity": "medium",
                        "message": f"Large transactions detected: {len(large_transactions)}",
                        "action_required": "Review large transactions",
                    }
                )
            if user.risk_profile and user.risk_profile.is_high_risk():
                monitoring_results["alerts"].append(
                    {
                        "type": "high_risk_user",
                        "severity": "high",
                        "message": "User classified as high risk",
                        "action_required": "Enhanced monitoring required",
                    }
                )
            return monitoring_results
        except Exception as e:
            logger.error(f"Ongoing compliance monitoring error: {e}")
            return {
                "user_id": str(user.id),
                "error": str(e),
                "monitoring_date": datetime.utcnow().isoformat(),
            }

    async def _check_transaction_amount(
        self, transaction: Transaction, user: User
    ) -> Dict[str, Any]:
        """Check transaction amount against thresholds"""
        if not transaction.amount_usd:
            return {"passed": True, "reason": "No USD amount available"}
        amount = transaction.amount_usd
        if amount >= self.suspicious_amount_threshold:
            return {
                "passed": False,
                "reason": f"Amount {amount} exceeds suspicious threshold {self.suspicious_amount_threshold}",
                "severity": "high",
            }
        if user.risk_profile and user.risk_profile.daily_transaction_limit:
            if amount > user.risk_profile.daily_transaction_limit:
                return {
                    "passed": False,
                    "reason": f"Amount {amount} exceeds user daily limit {user.risk_profile.daily_transaction_limit}",
                    "severity": "medium",
                }
        return {"passed": True, "amount": str(amount)}

    async def _check_transaction_frequency(
        self, db: AsyncSession, transaction: Transaction, user: User
    ) -> Dict[str, Any]:
        """Check transaction frequency patterns"""
        try:
            yesterday = datetime.utcnow() - timedelta(days=1)
            result = await db.execute(
                select(Transaction).where(
                    and_(
                        Transaction.user_id == user.id,
                        Transaction.timestamp >= yesterday,
                        Transaction.status == TransactionStatus.CONFIRMED,
                    )
                )
            )
            recent_transactions = result.scalars().all()
            if len(recent_transactions) > 50:
                return {
                    "passed": False,
                    "reason": f"High frequency: {len(recent_transactions)} transactions in 24 hours",
                    "severity": "medium",
                }
            return {"passed": True, "daily_count": len(recent_transactions)}
        except Exception as e:
            logger.error(f"Frequency check error: {e}")
            return {"passed": True, "error": str(e)}

    async def _check_transaction_patterns(
        self, db: AsyncSession, transaction: Transaction, user: User
    ) -> Dict[str, Any]:
        """Analyze transaction patterns for suspicious activity"""
        try:
            recent_transactions = await self._get_recent_transactions(db, user, days=7)
            patterns = []
            if transaction.amount_usd and transaction.amount_usd % 1000 == 0:
                patterns.append("round_numbers")
            if len(recent_transactions) > 10:
                time_diffs = []
                for i in range(1, len(recent_transactions)):
                    diff = (
                        recent_transactions[i].timestamp
                        - recent_transactions[i - 1].timestamp
                    ).total_seconds()
                    time_diffs.append(diff)
                avg_diff = sum(time_diffs) / len(time_diffs)
                if avg_diff < 300:
                    patterns.append("rapid_succession")
            hour = transaction.timestamp.hour
            if hour < 6 or hour > 22:
                patterns.append("unusual_timing")
            if patterns:
                return {
                    "passed": False,
                    "reason": f"Suspicious patterns detected: {', '.join(patterns)}",
                    "patterns": patterns,
                    "severity": "medium",
                }
            return {
                "passed": True,
                "patterns_checked": [
                    "round_numbers",
                    "rapid_succession",
                    "unusual_timing",
                ],
            }
        except Exception as e:
            logger.error(f"Pattern check error: {e}")
            return {"passed": True, "error": str(e)}

    async def _check_sanctions_screening(
        self, transaction: Transaction
    ) -> Dict[str, Any]:
        """Check addresses against sanctions lists"""
        suspicious_addresses = []
        if (
            transaction.from_address in suspicious_addresses
            or transaction.to_address in suspicious_addresses
        ):
            return {
                "passed": False,
                "reason": "Address found in sanctions list",
                "severity": "critical",
            }
        return {
            "passed": True,
            "addresses_checked": [transaction.from_address, transaction.to_address],
        }

    async def _check_risk_based_rules(
        self, transaction: Transaction, user: User
    ) -> Dict[str, Any]:
        """Apply risk-based compliance rules"""
        if not user.risk_profile:
            return {"passed": True, "reason": "No risk profile available"}
        risk_level = user.risk_profile.risk_level
        if risk_level == RiskLevel.HIGH or risk_level == RiskLevel.CRITICAL:
            if transaction.amount_usd and transaction.amount_usd > 5000:
                return {
                    "passed": False,
                    "reason": f"High-risk user transaction exceeds limit: {transaction.amount_usd}",
                    "severity": "high",
                }
        return {"passed": True, "risk_level": risk_level.value}

    async def _check_kyc_status(self, user: User) -> Dict[str, Any]:
        """Check user KYC verification status"""
        if not user.kyc:
            return {
                "passed": False,
                "reason": "No KYC verification found",
                "severity": "high",
            }
        if not user.kyc.is_verified():
            return {
                "passed": False,
                "reason": f"KYC status: {user.kyc.status.value}",
                "severity": "high",
            }
        if user.kyc.is_expired():
            return {
                "passed": False,
                "reason": "KYC verification expired",
                "severity": "medium",
            }
        return {"passed": True, "kyc_status": user.kyc.status.value}

    async def _check_user_risk_status(self, user: User) -> Dict[str, Any]:
        """Check user risk assessment status"""
        if not user.risk_profile:
            return {
                "passed": False,
                "reason": "No risk assessment found",
                "severity": "medium",
            }
        if user.risk_profile.is_due_for_review():
            return {
                "passed": False,
                "reason": "Risk assessment due for review",
                "severity": "low",
            }
        return {"passed": True, "risk_level": user.risk_profile.risk_level.value}

    async def _check_account_status(self, user: User) -> Dict[str, Any]:
        """Check user account status"""
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

    async def _check_compliance_history(
        self, db: AsyncSession, user: User
    ) -> Dict[str, Any]:
        """Check user's compliance history"""
        try:
            result = await db.execute(
                select(ComplianceCheck)
                .where(
                    and_(
                        ComplianceCheck.user_id == user.id,
                        ComplianceCheck.created_at
                        >= datetime.utcnow() - timedelta(days=30),
                    )
                )
                .order_by(ComplianceCheck.created_at.desc())
            )
            recent_checks = result.scalars().all()
            failed_checks = [
                c for c in recent_checks if c.status == ComplianceStatus.FAILED
            ]
            if len(failed_checks) > 3:
                return {
                    "passed": False,
                    "reason": f"Multiple failed compliance checks: {len(failed_checks)}",
                    "severity": "medium",
                }
            return {
                "passed": True,
                "recent_checks": len(recent_checks),
                "failed_checks": len(failed_checks),
            }
        except Exception as e:
            logger.error(f"Compliance history check error: {e}")
            return {"passed": True, "error": str(e)}

    async def _get_recent_transactions(
        self, db: AsyncSession, user: User, days: int = 7
    ) -> List[Transaction]:
        """Get user's recent transactions"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            result = await db.execute(
                select(Transaction)
                .where(
                    and_(
                        Transaction.user_id == user.id,
                        Transaction.timestamp >= cutoff_date,
                    )
                )
                .order_by(Transaction.timestamp.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting recent transactions: {e}")
            return []

    async def _create_suspicious_activity_report(
        self,
        db: AsyncSession,
        transaction: Transaction,
        user: User,
        compliance_results: Dict[str, Any],
    ) -> None:
        """Create Suspicious Activity Report (SAR)"""
        try:
            sar_number = (
                f"SAR-{datetime.utcnow().strftime('%Y%m%d')}-{user.id.hex[:8].upper()}"
            )
            sar = SuspiciousActivityReport(
                sar_number=sar_number,
                user_id=user.id,
                transaction_ids=[str(transaction.id)],
                activity_type="suspicious_transaction",
                activity_description="Transaction flagged by compliance system",
                suspicious_indicators=compliance_results,
                total_amount=transaction.amount_usd,
                currency="USD",
                activity_start_date=transaction.timestamp,
                activity_end_date=transaction.timestamp,
                filing_required=True,
                filing_deadline=datetime.utcnow() + timedelta(days=30),
            )
            db.add(sar)
            await db.commit()
            logger.warning(f"SAR created: {sar_number} for user {user.id}")
        except Exception as e:
            logger.error(f"Error creating SAR: {e}")

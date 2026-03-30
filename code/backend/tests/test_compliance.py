"""
Comprehensive test suite for compliance services
Tests KYC, AML, transaction monitoring, and regulatory compliance
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from models.compliance import SuspiciousActivity
from models.transaction import Transaction, TransactionStatus, TransactionType
from models.user import KYCStatus, RiskLevel, User, UserKYC, UserRiskProfile
from services.compliance.compliance_service import ComplianceService
from services.compliance.kyc_service import KYCService
from services.risk.risk_service import RiskService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TestComplianceService:
    """Test compliance service functionality"""

    @pytest.fixture
    async def compliance_service(self, db_session: AsyncSession):
        """Create compliance service instance"""
        return ComplianceService(db_session)

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession):
        """Create test user with profile"""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            email_verified=True,
        )
        db_session.add(user)
        await db_session.flush()

        # Add KYC record
        kyc = UserKYC(
            user_id=user.id,
            status=KYCStatus.APPROVED,
            identity_verified=True,
            document_verified=True,
        )
        db_session.add(kyc)

        # Add risk profile
        risk_profile = UserRiskProfile(
            user_id=user.id,
            risk_level=RiskLevel.MEDIUM,
            assessment_date=datetime.utcnow(),
        )
        db_session.add(risk_profile)

        await db_session.commit()
        return user

    @pytest.fixture
    async def test_transaction(self, db_session: AsyncSession, test_user: User):
        """Create test transaction"""
        transaction = Transaction(
            user_id=test_user.id,
            transaction_type=TransactionType.TRANSFER,
            from_address="0x1234567890abcdef",
            to_address="0xfedcba0987654321",
            amount=Decimal("1000.00"),
            value_usd=Decimal("1000.00"),
            status=TransactionStatus.CONFIRMED,
            created_at=datetime.utcnow(),
        )
        db_session.add(transaction)
        await db_session.commit()
        return transaction

    async def test_kyc_verification_success(
        self, compliance_service: ComplianceService, test_user: User
    ):
        """Test successful KYC verification"""
        kyc_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "address_line1": "123 Main St",
            "city": "New York",
            "country": "US",
            "postal_code": "10001",
            "document_type": "passport",
            "document_number": "A12345678",
        }

        with patch.object(
            compliance_service, "_verify_identity"
        ) as mock_identity, patch.object(
            compliance_service, "_verify_documents"
        ) as mock_documents, patch.object(
            compliance_service, "_screen_sanctions"
        ) as mock_sanctions, patch.object(
            compliance_service, "_screen_pep"
        ) as mock_pep:

            # Mock successful responses
            mock_identity.return_value = {
                "verified": True,
                "confidence_score": 95,
                "reference_id": "ref123",
            }
            mock_documents.return_value = {"verified": True, "verification_score": 90}
            mock_sanctions.return_value = {"match_found": False, "confidence": 0}
            mock_pep.return_value = {"match_found": False, "confidence": 0}

            result = await compliance_service.perform_kyc_check(
                str(test_user.id), kyc_data
            )

            assert result.status == "passed"
            assert result.score >= 80.0
            assert result.findings is not None

    async def test_kyc_verification_failure(
        self, compliance_service: ComplianceService, test_user: User
    ):
        """Test KYC verification failure due to sanctions match"""
        kyc_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "country": "US",
        }

        with patch.object(
            compliance_service, "_verify_identity"
        ) as mock_identity, patch.object(
            compliance_service, "_verify_documents"
        ) as mock_documents, patch.object(
            compliance_service, "_screen_sanctions"
        ) as mock_sanctions, patch.object(
            compliance_service, "_screen_pep"
        ) as mock_pep:

            # Mock sanctions match
            mock_identity.return_value = {"verified": True, "confidence_score": 95}
            mock_documents.return_value = {"verified": True, "verification_score": 90}
            mock_sanctions.return_value = {"match_found": True, "confidence": 95}
            mock_pep.return_value = {"match_found": False, "confidence": 0}

            result = await compliance_service.perform_kyc_check(
                str(test_user.id), kyc_data
            )

            assert result.status == "failed"
            assert result.findings["sanctions"]["match_found"] is True

    async def test_transaction_monitoring_normal(
        self, compliance_service: ComplianceService, test_transaction: Transaction
    ):
        """Test transaction monitoring for normal transaction"""
        with patch.object(
            compliance_service, "_check_transaction_amount"
        ) as mock_amount, patch.object(
            compliance_service, "_check_transaction_velocity"
        ) as mock_velocity, patch.object(
            compliance_service, "_check_address_risk"
        ) as mock_address, patch.object(
            compliance_service, "_check_transaction_patterns"
        ) as mock_patterns:

            # Mock low-risk responses
            mock_amount.return_value = {"risk_score": 0, "findings": {}}
            mock_velocity.return_value = {"risk_score": 5, "findings": {}}
            mock_address.return_value = {"risk_score": 0, "findings": {}}
            mock_patterns.return_value = {"risk_score": 0, "findings": {}}

            result = await compliance_service.monitor_transaction(
                str(test_transaction.id)
            )

            assert result.status == "passed"
            assert result.score <= 30.0  # Low risk
            assert result.risk_level in ["low", "medium"]

    async def test_transaction_monitoring_suspicious(
        self, compliance_service: ComplianceService, test_transaction: Transaction
    ):
        """Test transaction monitoring for suspicious transaction"""
        with patch.object(
            compliance_service, "_check_transaction_amount"
        ) as mock_amount, patch.object(
            compliance_service, "_check_transaction_velocity"
        ) as mock_velocity, patch.object(
            compliance_service, "_check_address_risk"
        ) as mock_address, patch.object(
            compliance_service, "_check_transaction_patterns"
        ) as mock_patterns, patch.object(
            compliance_service, "_create_suspicious_activity"
        ) as mock_sar:

            # Mock high-risk responses
            mock_amount.return_value = {
                "risk_score": 30,
                "findings": {"large_amount": {"amount": 50000}},
            }
            mock_velocity.return_value = {
                "risk_score": 25,
                "findings": {"high_frequency": {"count": 15}},
            }
            mock_address.return_value = {
                "risk_score": 40,
                "findings": {"from_address_risk": {"risk_level": "high"}},
            }
            mock_patterns.return_value = {
                "risk_score": 10,
                "findings": {"round_amount": {"amount": 50000}},
            }

            mock_sar.return_value = None

            result = await compliance_service.monitor_transaction(
                str(test_transaction.id)
            )

            assert result.status in ["failed", "manual_review"]
            assert result.score >= 70.0  # High risk
            assert result.risk_level in ["high", "critical"]
            mock_sar.assert_called_once()

    async def test_large_amount_detection(self, compliance_service: ComplianceService):
        """Test detection of large transaction amounts"""
        # Create large transaction
        large_transaction = Transaction(
            user_id="test_user_id",
            transaction_type=TransactionType.TRANSFER,
            value_usd=Decimal("25000.00"),  # Above threshold
            created_at=datetime.utcnow(),
        )

        result = await compliance_service._check_transaction_amount(large_transaction)

        assert result["risk_score"] > 0
        assert "large_amount" in result["findings"]
        assert result["findings"]["large_amount"]["amount"] == 25000.0

    async def test_velocity_check(
        self,
        compliance_service: ComplianceService,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test transaction velocity checking"""
        # Create multiple recent transactions
        yesterday = datetime.utcnow() - timedelta(hours=12)

        for i in range(15):  # Create 15 transactions
            transaction = Transaction(
                user_id=test_user.id,
                transaction_type=TransactionType.TRANSFER,
                value_usd=Decimal("1000.00"),
                status=TransactionStatus.CONFIRMED,
                created_at=yesterday + timedelta(minutes=i * 30),
            )
            db_session.add(transaction)

        await db_session.commit()

        # Test velocity check
        test_transaction = Transaction(
            user_id=test_user.id,
            transaction_type=TransactionType.TRANSFER,
            value_usd=Decimal("1000.00"),
            created_at=datetime.utcnow(),
        )

        result = await compliance_service._check_transaction_velocity(test_transaction)

        assert result["risk_score"] > 0
        assert "high_frequency" in result["findings"]

    async def test_address_risk_assessment(self, compliance_service: ComplianceService):
        """Test address risk assessment"""
        transaction = Transaction(
            from_address="0x1234567890abcdef", to_address="0xfedcba0987654321"
        )

        with patch.object(compliance_service, "_query_aml_provider") as mock_aml:
            mock_aml.return_value = {
                "risk_level": "high",
                "risk_score": 85,
                "categories": ["mixer", "darknet"],
            }

            result = await compliance_service._check_address_risk(transaction)

            assert result["risk_score"] > 0
            assert (
                "from_address_risk" in result["findings"]
                or "to_address_risk" in result["findings"]
            )

    async def test_pattern_detection(self, compliance_service: ComplianceService):
        """Test suspicious pattern detection"""
        # Test round number detection
        round_transaction = Transaction(
            value_usd=Decimal("10000.00"),  # Round number
            created_at=datetime.utcnow().replace(hour=2),  # Unusual time
        )

        result = await compliance_service._check_transaction_patterns(round_transaction)

        assert result["risk_score"] > 0
        assert "round_amount" in result["findings"]
        assert "unusual_timing" in result["findings"]

    async def test_regulatory_report_generation(
        self, compliance_service: ComplianceService, db_session: AsyncSession
    ):
        """Test regulatory report generation"""
        period_start = datetime.utcnow() - timedelta(days=30)
        period_end = datetime.utcnow()

        # Create some suspicious activities
        for i in range(3):
            activity = SuspiciousActivity(
                user_id="test_user_id",
                activity_type="high_risk_transaction",
                severity="high",
                risk_score=Decimal("85.0"),
                amount_usd=Decimal("15000.00"),
                detected_at=period_start + timedelta(days=i * 10),
            )
            db_session.add(activity)

        await db_session.commit()

        # Generate SAR report
        report = await compliance_service.generate_regulatory_report(
            "sar", period_start, period_end
        )

        assert report.report_type == "sar"
        assert report.record_count >= 3
        assert report.total_amount_usd > 0
        assert report.metadata is not None

    async def test_compliance_score_calculation(
        self, compliance_service: ComplianceService
    ):
        """Test compliance score calculation"""
        # Test perfect score
        identity_result = {"verified": True, "confidence_score": 100}
        document_result = {"verified": True, "verification_score": 100}
        sanctions_result = {"match_found": False}
        pep_result = {"match_found": False}

        score = compliance_service._calculate_kyc_score(
            identity_result, document_result, sanctions_result, pep_result
        )

        assert score == 100.0

        # Test partial score
        identity_result = {"verified": True, "confidence_score": 80}
        document_result = {"verified": True, "verification_score": 70}

        score = compliance_service._calculate_kyc_score(
            identity_result, document_result, sanctions_result, pep_result
        )

        assert 80.0 <= score <= 90.0

    async def test_risk_level_determination(
        self, compliance_service: ComplianceService
    ):
        """Test risk level determination"""
        assert compliance_service._determine_risk_level(90.0) == "critical"
        assert compliance_service._determine_risk_level(70.0) == "high"
        assert compliance_service._determine_risk_level(40.0) == "medium"
        assert compliance_service._determine_risk_level(10.0) == "low"

    async def test_compliance_status_determination(
        self, compliance_service: ComplianceService
    ):
        """Test compliance status determination"""
        assert compliance_service._determine_compliance_status(80.0) == "failed"
        assert compliance_service._determine_compliance_status(60.0) == "manual_review"
        assert compliance_service._determine_compliance_status(30.0) == "passed"


class TestKYCService:
    """Test KYC service functionality"""

    @pytest.fixture
    async def kyc_service(self, db_session: AsyncSession):
        """Create KYC service instance"""
        return KYCService(db_session)

    async def test_kyc_submission(self, kyc_service: KYCService, test_user: User):
        """Test KYC submission process"""
        kyc_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "nationality": "US",
            "document_type": "passport",
            "document_number": "A12345678",
        }

        with patch.object(
            kyc_service, "_validate_kyc_data"
        ) as mock_validate, patch.object(
            kyc_service, "_submit_to_provider"
        ) as mock_submit:

            mock_validate.return_value = True
            mock_submit.return_value = {"status": "pending", "reference_id": "ref123"}

            result = await kyc_service.submit_kyc_verification(
                str(test_user.id), kyc_data
            )

            assert result.status == KYCStatus.PENDING_REVIEW
            assert result.provider_reference_id == "ref123"

    async def test_kyc_data_validation(self, kyc_service: KYCService):
        """Test KYC data validation"""
        # Valid data
        valid_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "nationality": "US",
        }

        assert kyc_service._validate_kyc_data(valid_data) is True

        # Invalid data - missing required fields
        invalid_data = {"first_name": "John"}

        with pytest.raises(ValueError):
            kyc_service._validate_kyc_data(invalid_data)

    async def test_document_verification(self, kyc_service: KYCService):
        """Test document verification process"""
        document_data = {
            "document_type": "passport",
            "document_number": "A12345678",
            "document_image": "base64_encoded_image",
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "verified": True,
                "confidence": 95,
                "document_valid": True,
            }
            mock_post.return_value = mock_response

            result = await kyc_service._verify_document(document_data)

            assert result["verified"] is True
            assert result["confidence"] == 95


class TestRiskService:
    """Test risk assessment service"""

    @pytest.fixture
    async def risk_service(self, db_session: AsyncSession):
        """Create risk service instance"""
        return RiskService(db_session)

    async def test_user_risk_assessment(
        self, risk_service: RiskService, test_user: User
    ):
        """Test user risk assessment"""
        assessment_data = {
            "annual_income": 100000,
            "investment_experience": "intermediate",
            "risk_tolerance": "medium",
            "investment_goals": ["growth", "income"],
        }

        result = await risk_service.perform_user_risk_assessment(
            str(test_user.id), assessment_data
        )

        assert result.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]
        assert result.assessment_date is not None
        assert result.assessment_data is not None

    async def test_portfolio_risk_assessment(self, risk_service: RiskService):
        """Test portfolio risk assessment"""

        result = await risk_service.assess_portfolio_risk("portfolio_id", "user_id")

        # Mock the assessment since we don't have actual portfolio data
        assert isinstance(result, dict)
        assert "risk_score" in result
        assert "risk_level" in result

    async def test_risk_score_calculation(self, risk_service: RiskService):
        """Test risk score calculation"""
        factors = {
            "age": 30,
            "income": 100000,
            "investment_experience": "intermediate",
            "risk_tolerance": "medium",
            "transaction_history": "normal",
        }

        score = risk_service._calculate_risk_score(factors)

        assert 0 <= score <= 100
        assert isinstance(score, (int, float))


@pytest.mark.asyncio
class TestComplianceIntegration:
    """Integration tests for compliance services"""

    async def test_end_to_end_kyc_process(self, db_session: AsyncSession):
        """Test complete KYC process from submission to approval"""
        # Create user
        user = User(email="integration@test.com", hashed_password="hashed_password")
        db_session.add(user)
        await db_session.flush()

        # Initialize services
        compliance_service = ComplianceService(db_session)

        # Submit KYC
        kyc_data = {
            "first_name": "Integration",
            "last_name": "Test",
            "date_of_birth": "1985-05-15",
            "nationality": "US",
            "document_type": "drivers_license",
            "document_number": "DL123456789",
        }

        with patch.object(
            compliance_service, "_verify_identity"
        ) as mock_identity, patch.object(
            compliance_service, "_verify_documents"
        ) as mock_documents, patch.object(
            compliance_service, "_screen_sanctions"
        ) as mock_sanctions, patch.object(
            compliance_service, "_screen_pep"
        ) as mock_pep:

            # Mock successful verification
            mock_identity.return_value = {"verified": True, "confidence_score": 95}
            mock_documents.return_value = {"verified": True, "verification_score": 90}
            mock_sanctions.return_value = {"match_found": False}
            mock_pep.return_value = {"match_found": False}

            # Perform KYC check
            compliance_check = await compliance_service.perform_kyc_check(
                str(user.id), kyc_data
            )

            # Verify results
            assert compliance_check.status == "passed"
            assert compliance_check.score >= 80.0

            # Check user KYC status updated
            stmt = select(UserKYC).where(UserKYC.user_id == user.id)
            result = await db_session.execute(stmt)
            user_kyc = result.scalar_one_or_none()

            assert user_kyc is not None
            assert user_kyc.status == KYCStatus.APPROVED

    async def test_transaction_compliance_workflow(self, db_session: AsyncSession):
        """Test complete transaction compliance workflow"""
        # Create user with approved KYC
        user = User(email="transaction@test.com", hashed_password="hashed_password")
        db_session.add(user)
        await db_session.flush()

        kyc = UserKYC(
            user_id=user.id, status=KYCStatus.APPROVED, identity_verified=True
        )
        db_session.add(kyc)

        # Create transaction
        transaction = Transaction(
            user_id=user.id,
            transaction_type=TransactionType.TRANSFER,
            from_address="0x1234567890abcdef",
            to_address="0xfedcba0987654321",
            amount=Decimal("5000.00"),
            value_usd=Decimal("5000.00"),
            status=TransactionStatus.PENDING,
        )
        db_session.add(transaction)
        await db_session.commit()

        # Initialize compliance service
        compliance_service = ComplianceService(db_session)

        # Monitor transaction
        with patch.object(compliance_service, "_query_aml_provider") as mock_aml:
            mock_aml.return_value = {"risk_level": "low", "risk_score": 10}

            compliance_check = await compliance_service.monitor_transaction(
                str(transaction.id)
            )

            # Verify compliance check
            assert compliance_check.status in ["passed", "manual_review"]
            assert compliance_check.score is not None
            assert compliance_check.risk_level is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

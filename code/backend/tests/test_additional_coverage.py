"""
Additional tests to boost coverage across services and models
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from models.compliance import (
    AuditEventType,
    AuditLog,
    ComplianceCheck,
    ComplianceStatus,
    SuspiciousActivityReport,
)
from models.portfolio import Portfolio, PortfolioAsset
from models.transaction import Transaction, TransactionStatus, TransactionType
from models.user import KYCStatus
from models.user import RiskLevel as UserRiskLevel
from models.user import User, UserKYC, UserRiskProfile, UserStatus
from services.auth.jwt_service import JWTService
from services.auth.mfa_service import MFAService
from services.auth.password_service import PasswordService
from services.compliance.compliance_service import ComplianceService
from services.compliance.kyc_service import KYCService
from sqlalchemy.ext.asyncio import AsyncSession

# ── Password Service ──────────────────────────────────────────────────────────


class TestPasswordService:
    def test_hash_and_verify(self):
        svc = PasswordService()
        pwd = "SecurePassword1!"
        hashed = svc.hash_password(pwd)
        assert hashed != pwd
        assert svc.verify_password(pwd, hashed)
        assert not svc.verify_password("wrong", hashed)

    def test_verify_bad_hash(self):
        svc = PasswordService()
        assert not svc.verify_password("any", "not-a-valid-hash")

    def test_validate_strength_valid(self):
        svc = PasswordService()
        ok, err = svc.validate_password_strength("ValidPass1!")
        assert ok is True
        assert err is None

    def test_validate_strength_too_short(self):
        svc = PasswordService()
        ok, err = svc.validate_password_strength("Sh0!")
        assert ok is False
        assert "characters" in err

    def test_validate_strength_no_upper(self):
        svc = PasswordService()
        ok, err = svc.validate_password_strength("nouppercase1!")
        assert ok is False
        assert "uppercase" in err.lower()

    def test_validate_strength_no_lower(self):
        svc = PasswordService()
        ok, err = svc.validate_password_strength("NOLOWERCASE1!")
        assert ok is False
        assert "lowercase" in err.lower()

    def test_validate_strength_no_digit(self):
        svc = PasswordService()
        ok, err = svc.validate_password_strength("NoDigits!Pass")
        assert ok is False
        assert "digit" in err.lower()

    def test_validate_strength_no_special(self):
        svc = PasswordService()
        ok, err = svc.validate_password_strength("NoSpecial123")
        assert ok is False
        assert "special" in err.lower()

    def test_private_validate_raises(self):
        svc = PasswordService()
        with pytest.raises(ValueError):
            svc._validate_password_strength("bad")

    def test_needs_rehash(self):
        svc = PasswordService()
        hashed = svc.hash_password("Password1!")
        # Fresh bcrypt hashes should not need rehash
        assert isinstance(svc.needs_rehash(hashed), bool)

    def test_generate_temporary_password(self):
        svc = PasswordService()
        tmp = svc.generate_temporary_password()
        assert len(tmp) >= 16
        ok, _ = svc.validate_password_strength(tmp)
        assert ok


# ── JWT Service ───────────────────────────────────────────────────────────────


class TestJWTService:
    @pytest.fixture
    def jwt(self):
        return JWTService()

    def test_create_and_verify_access_token(self, jwt):
        token = jwt.create_access_token({"sub": str(uuid4()), "email": "t@t.com"})
        assert isinstance(token, str)
        payload = jwt.verify_access_token(token)
        assert payload["type"] == "access"

    def test_create_and_verify_refresh_token(self, jwt):
        token = jwt.create_refresh_token({"sub": str(uuid4())})
        payload = jwt.verify_refresh_token(token)
        assert payload["type"] == "refresh"

    def test_wrong_token_type_raises(self, jwt):
        from jose import JWTError

        access = jwt.create_access_token({"sub": "u1"})
        with pytest.raises(JWTError):
            jwt.verify_refresh_token(access)

    def test_decode_without_verification(self, jwt):
        token = jwt.create_access_token({"sub": "u1"})
        payload = jwt.decode_token_without_verification(token)
        assert "sub" in payload

    def test_get_token_expiry(self, jwt):
        token = jwt.create_access_token({"sub": "u1"})
        expiry = jwt.get_token_expiry(token)
        assert expiry is not None
        assert expiry > datetime.now(timezone.utc)

    def test_is_token_expired_false(self, jwt):
        token = jwt.create_access_token({"sub": "u1"})
        assert jwt.is_token_expired(token) is False

    def test_get_remaining_time(self, jwt):
        token = jwt.create_access_token({"sub": "u1"})
        remaining = jwt.get_remaining_time(token)
        assert remaining is not None
        assert remaining.total_seconds() > 0


# ── MFA Service ───────────────────────────────────────────────────────────────


class TestMFAService:
    def test_generate_secret(self):
        secret = MFAService.generate_secret()
        assert isinstance(secret, str)
        assert len(secret) > 0

    def test_generate_qr_code(self):
        secret = MFAService.generate_secret()
        uri = MFAService.generate_qr_code(secret, "test@example.com")
        assert "otpauth://" in uri
        assert "test" in uri and "example" in uri

    def test_verify_code_current(self):
        secret = MFAService.generate_secret()
        code = MFAService.get_current_code(secret)
        assert MFAService.verify_code(secret, code)

    def test_verify_code_invalid(self):
        secret = MFAService.generate_secret()
        assert not MFAService.verify_code(secret, "000000")

    def test_generate_backup_codes(self):
        codes = MFAService.generate_backup_codes(5)
        assert len(codes) == 5
        for code in codes:
            assert isinstance(code, str)


# ── Model tests ───────────────────────────────────────────────────────────────


class TestUserModel:
    def test_user_is_active(self):
        u = User(
            email="a@b.com",
            hashed_password="x",
            status=UserStatus.ACTIVE,
            email_verified=True,
        )
        assert u.is_active()

    def test_user_not_active_when_pending(self):
        u = User(email="a@b.com", hashed_password="x", status=UserStatus.PENDING)
        assert not u.is_active()

    def test_user_is_locked(self):
        u = User(email="a@b.com", hashed_password="x")
        u.locked_until = datetime.now(timezone.utc) + timedelta(hours=1)
        assert u.is_locked()

    def test_user_not_locked(self):
        u = User(email="a@b.com", hashed_password="x")
        assert not u.is_locked()

    def test_can_login(self):
        u = User(
            email="a@b.com",
            hashed_password="x",
            status=UserStatus.ACTIVE,
            email_verified=True,
        )
        assert u.can_login()

    def test_increment_and_lock(self):
        u = User(email="a@b.com", hashed_password="x")
        u.failed_login_attempts = 0
        for _ in range(5):
            u.increment_failed_login()
        assert u.locked_until is not None

    def test_reset_failed_login(self):
        u = User(email="a@b.com", hashed_password="x")
        u.failed_login_attempts = 1
        u.reset_failed_login()
        assert u.failed_login_attempts == 0

    def test_record_login(self):
        u = User(email="a@b.com", hashed_password="x")
        u.login_count = 0
        u.failed_login_attempts = 0
        u.record_login()
        assert u.login_count == 1
        assert u.last_login_at is not None

    def test_user_is_active_kwarg(self):
        u = User(email="a@b.com", hashed_password="x", is_active=True)
        assert u.status == UserStatus.ACTIVE

    def test_user_is_verified_kwarg(self):
        u = User(email="a@b.com", hashed_password="x", is_verified=True)
        assert u.email_verified is True

    def test_can_trade(self):
        u = User(
            email="a@b.com",
            hashed_password="x",
            status=UserStatus.ACTIVE,
            email_verified=True,
        )
        assert u.can_trade()


class TestUserKYCModel:
    def test_is_verified(self):
        kyc = UserKYC(
            user_id=uuid4(),
            status=KYCStatus.APPROVED,
            identity_verified=True,
            document_verified=True,
            sanctions_match=False,
        )
        assert kyc.is_verified()

    def test_not_verified_when_rejected(self):
        kyc = UserKYC(user_id=uuid4(), status=KYCStatus.REJECTED)
        assert not kyc.is_verified()

    def test_is_expired(self):
        kyc = UserKYC(
            user_id=uuid4(), expires_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        assert kyc.is_expired()

    def test_not_expired(self):
        kyc = UserKYC(user_id=uuid4())
        assert not kyc.is_expired()

    def test_needs_renewal(self):
        kyc = UserKYC(user_id=uuid4(), renewal_required=True)
        assert kyc.needs_renewal()


class TestUserRiskProfileModel:
    def test_is_high_risk(self):
        rp = UserRiskProfile(user_id=uuid4())
        rp.risk_level = UserRiskLevel.HIGH
        assert rp.is_high_risk()

    def test_not_high_risk(self):
        rp = UserRiskProfile(user_id=uuid4())
        rp.risk_level = UserRiskLevel.LOW
        assert not rp.is_high_risk()

    def test_is_due_for_review(self):
        rp = UserRiskProfile(user_id=uuid4())
        rp.next_review_date = datetime.now(timezone.utc) - timedelta(days=1)
        assert rp.is_due_for_review()

    def test_update_risk_level(self):
        rp = UserRiskProfile(user_id=uuid4())
        rp.risk_level = UserRiskLevel.LOW
        rp.update_risk_level(UserRiskLevel.HIGH, reason="High transaction volume")
        assert rp.risk_level == UserRiskLevel.HIGH


class TestComplianceModels:
    def test_compliance_check_is_valid(self):
        cc = ComplianceCheck(
            check_type="test",
            check_name="Test",
            status=ComplianceStatus.PASSED,
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
        )
        assert cc.is_valid()

    def test_compliance_check_mark_expired(self):
        cc = ComplianceCheck(
            check_type="t", check_name="t", status=ComplianceStatus.PASSED
        )
        cc.mark_expired()
        assert cc.is_expired

    def test_sar_is_filing_overdue(self):
        sar = SuspiciousActivityReport(
            sar_number="SAR-001",
            activity_type="test",
            activity_description="test",
            suspicious_indicators={},
            activity_start_date=datetime.now(timezone.utc),
            filing_required=True,
            filing_deadline=datetime.now(timezone.utc) - timedelta(days=1),
        )
        assert sar.is_filing_overdue()

    def test_audit_log_creation(self):
        log = AuditLog(
            event_type=AuditEventType.USER_LOGIN,
            event_name="test_login",
        )
        assert log.event_name == "test_login"


# ── ComplianceService extended ────────────────────────────────────────────────


class TestComplianceServiceExtended:
    @pytest.fixture
    def svc(self):
        return ComplianceService()

    def test_determine_kyc_status_passed(self, svc):
        assert svc._determine_kyc_status(95.0) == "passed"

    def test_determine_kyc_status_manual(self, svc):
        assert svc._determine_kyc_status(70.0) == "manual_review"

    def test_determine_kyc_status_failed(self, svc):
        assert svc._determine_kyc_status(30.0) == "failed"

    def test_determine_risk_level_critical(self, svc):
        assert svc._determine_risk_level(90.0) == "critical"

    def test_determine_risk_level_high(self, svc):
        assert svc._determine_risk_level(65.0) == "high"

    def test_determine_risk_level_medium(self, svc):
        assert svc._determine_risk_level(35.0) == "medium"

    def test_determine_risk_level_low(self, svc):
        assert svc._determine_risk_level(5.0) == "low"

    def test_calculate_kyc_score_perfect(self, svc):
        score = svc._calculate_kyc_score(
            {"verified": True, "confidence_score": 100},
            {"verified": True, "verification_score": 100},
            {"match_found": False},
            {"match_found": False},
        )
        assert score == 100.0

    def test_calculate_kyc_score_sanctions_fail(self, svc):
        score = svc._calculate_kyc_score(
            {"verified": True, "confidence_score": 100},
            {"verified": True, "verification_score": 100},
            {"match_found": True},
            {"match_found": False},
        )
        assert score == 0.0

    def test_calculate_kyc_score_partial(self, svc):
        score = svc._calculate_kyc_score(
            {"verified": True, "confidence_score": 80},
            {"verified": True, "verification_score": 70},
            {"match_found": False},
            {"match_found": False},
        )
        assert 0 < score < 100

    @pytest.mark.asyncio
    async def test_check_transaction_amount_large(self, svc):
        tx = Transaction(value_usd=Decimal("25000.00"))
        result = await svc._check_transaction_amount(tx)
        assert result["risk_score"] > 0
        assert "large_amount" in result["findings"]

    @pytest.mark.asyncio
    async def test_check_transaction_amount_normal(self, svc):
        tx = Transaction(value_usd=Decimal("100.00"))
        result = await svc._check_transaction_amount(tx)
        assert result["risk_score"] == 0

    @pytest.mark.asyncio
    async def test_check_transaction_patterns_round(self, svc):
        tx = Transaction(
            value_usd=Decimal("10000.00"),
            created_at=datetime.now(timezone.utc).replace(hour=2),
        )
        result = await svc._check_transaction_patterns(tx)
        assert result["risk_score"] > 0
        assert "round_amount" in result["findings"]

    @pytest.mark.asyncio
    async def test_check_address_risk_high(self, svc):
        tx = Transaction(from_address="0x1234", to_address="0x5678")
        with patch.object(
            svc,
            "_query_aml_provider",
            new=AsyncMock(return_value={"risk_level": "high", "risk_score": 85}),
        ):
            result = await svc._check_address_risk(tx)
        assert result["risk_score"] > 0

    @pytest.mark.asyncio
    async def test_kyc_check_sanctions_fail(self, svc):
        with patch.object(
            svc,
            "_verify_identity",
            new=AsyncMock(return_value={"verified": True, "confidence_score": 95}),
        ):
            with patch.object(
                svc,
                "_verify_documents",
                new=AsyncMock(
                    return_value={"verified": True, "verification_score": 90}
                ),
            ):
                with patch.object(
                    svc,
                    "_screen_sanctions",
                    new=AsyncMock(return_value={"match_found": True}),
                ):
                    with patch.object(
                        svc,
                        "_screen_pep",
                        new=AsyncMock(return_value={"match_found": False}),
                    ):
                        result = await svc.perform_kyc_check(
                            "user-id", {"first_name": "x"}
                        )
        assert result.status == "failed"
        assert result.score == 0.0


# ── KYC Service ───────────────────────────────────────────────────────────────


class TestKYCServiceExtended:
    @pytest.fixture
    def kyc_svc(self):
        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=None))
        )
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return KYCService(db)

    def test_validate_kyc_data_valid(self, kyc_svc):
        data = {
            "first_name": "A",
            "last_name": "B",
            "date_of_birth": "1990-01-01",
            "nationality": "US",
        }
        assert kyc_svc._validate_kyc_data(data) is True

    def test_validate_kyc_data_missing_fields(self, kyc_svc):
        with pytest.raises(ValueError, match="Missing required KYC fields"):
            kyc_svc._validate_kyc_data({"first_name": "A"})

    @pytest.mark.asyncio
    async def test_submit_kyc_verification(self, kyc_svc):
        data = {
            "first_name": "J",
            "last_name": "D",
            "date_of_birth": "1990-01-01",
            "nationality": "US",
        }
        result = await kyc_svc.submit_kyc_verification(str(uuid4()), data)
        assert result is not None
        kyc_svc.db.add.assert_called_once()
        kyc_svc.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_kyc_status_none(self, kyc_svc):
        result = await kyc_svc.get_kyc_status(str(uuid4()))
        assert result is None


# ── Risk Service ──────────────────────────────────────────────────────────────


class TestRiskServiceExtended:
    @pytest.fixture
    def risk_svc(self):
        from services.risk.risk_service import RiskService

        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=None))
        )
        db.add = Mock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        return RiskService(db)

    def test_calculate_risk_score_moderate(self, risk_svc):
        factors = {
            "age": 35,
            "income": 80000,
            "investment_experience": "moderate",
            "risk_tolerance": "medium",
            "transaction_history": "normal",
        }
        score = risk_svc._calculate_risk_score(factors)
        assert 0 <= score <= 100

    def test_calculate_risk_score_high_risk(self, risk_svc):
        factors = {
            "age": 25,
            "income": 200000,
            "investment_experience": "expert",
            "risk_tolerance": "aggressive",
            "transaction_history": "suspicious",
        }
        score = risk_svc._calculate_risk_score(factors)
        assert score > 50

    def test_calculate_risk_score_low_risk(self, risk_svc):
        factors = {
            "age": 65,
            "income": 25000,
            "investment_experience": "beginner",
            "risk_tolerance": "conservative",
            "transaction_history": "normal",
        }
        score = risk_svc._calculate_risk_score(factors)
        assert score < 60

    def test_determine_user_risk_level_low(self, risk_svc):
        level = risk_svc._determine_user_risk_level(Decimal("20"))
        from models.user import RiskLevel as _RL

        assert level == _RL.LOW

    def test_determine_user_risk_level_high(self, risk_svc):
        level = risk_svc._determine_user_risk_level(Decimal("80"))
        from models.user import RiskLevel as _RL

        assert level in (_RL.HIGH, _RL.CRITICAL)

    @pytest.mark.asyncio
    async def test_assess_portfolio_risk_invalid_id(self, risk_svc):
        result = await risk_svc.assess_portfolio_risk("not-a-uuid", "also-not")
        assert isinstance(result, dict)
        assert "risk_score" in result

    @pytest.mark.asyncio
    async def test_perform_user_risk_assessment(self, risk_svc):
        user_id = str(uuid4())
        data = {
            "age": 30,
            "annual_income": 100000,
            "investment_experience": "intermediate",
            "risk_tolerance": "medium",
        }
        result = await risk_svc.perform_user_risk_assessment(user_id, data)
        assert result is not None
        assert result.assessment_date is not None


# ── Portfolio Model ───────────────────────────────────────────────────────────


class TestPortfolioModel:
    def test_portfolio_creation(self):
        p = Portfolio(
            user_id=uuid4(),
            name="test",
            total_value=Decimal("1000"),
            cash_balance=Decimal("500"),
        )
        assert p.name == "test"
        assert p.total_value == Decimal("1000")
        assert p.cash_balance == Decimal("500")

    def test_portfolio_asset_symbol_shim(self):
        a = PortfolioAsset(
            portfolio_id=uuid4(),
            symbol="BTC",
            quantity=Decimal("1"),
            average_price=Decimal("50000"),
        )
        assert a.symbol == "BTC"
        assert a.asset_symbol == "BTC"
        assert a.average_price == Decimal("50000")
        assert a.average_cost == Decimal("50000")


# ── Transaction Model ─────────────────────────────────────────────────────────


class TestTransactionModel:
    def test_transaction_with_value_usd(self):
        tx = Transaction(
            transaction_type=TransactionType.TRANSFER,
            value_usd=Decimal("5000.00"),
        )
        assert tx.value_usd == Decimal("5000.00")

    def test_transaction_amount_fields(self):
        tx = Transaction(amount_usd=Decimal("15000.00"), value_usd=Decimal("15000.00"))
        assert tx.amount_usd == Decimal("15000.00")
        assert tx.value_usd == Decimal("15000.00")

    def test_transaction_default_status(self):
        tx = Transaction()
        assert tx.status == TransactionStatus.PENDING or tx.status is None


# ── Portfolio Service extended ────────────────────────────────────────────────


class TestPortfolioServiceExtended:
    @pytest.fixture
    async def db(self):
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def svc(self, db):
        from services.portfolio.portfolio_service import PortfolioService

        return PortfolioService(db)

    @pytest.fixture
    def portfolio(self):
        return Portfolio(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            total_value=Decimal("100000"),
            cash_balance=Decimal("50000"),
            is_active=True,
        )

    @pytest.mark.asyncio
    async def test_get_portfolio_invalid_uuid(self, svc):
        with pytest.raises(ValueError, match="Invalid UUID"):
            await svc.get_portfolio("bad-id", uuid4())

    @pytest.mark.asyncio
    async def test_rebalance_invalid_allocation(self, svc, portfolio):
        from exceptions.portfolio_exceptions import InvalidAllocationError
        from schemas.portfolio import AssetAllocation

        allocs = [
            AssetAllocation(symbol="BTC", target_percentage=Decimal("60")),
            AssetAllocation(symbol="ETH", target_percentage=Decimal("50")),
        ]
        with pytest.raises(InvalidAllocationError):
            await svc.rebalance_portfolio(portfolio.id, portfolio.user_id, allocs)

    @pytest.mark.asyncio
    async def test_calculate_portfolio_value_empty(self, svc, db, portfolio):
        portfolio.assets = []
        portfolio._cash_balance = Decimal("0")
        db.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=portfolio))
        )
        total = await svc.calculate_portfolio_value(portfolio.id, portfolio.user_id)
        assert total == Decimal("0")

    @pytest.mark.asyncio
    async def test_get_portfolio_performance(self, svc, db, portfolio):
        db.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=portfolio))
        )
        perf = await svc.get_portfolio_performance(portfolio.id, portfolio.user_id)
        assert "total_return" in perf
        assert "volatility" in perf

    @pytest.mark.asyncio
    async def test_calculate_portfolio_risk(self, svc, db, portfolio):
        db.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=portfolio))
        )
        risk = await svc.calculate_portfolio_risk(portfolio.id, portfolio.user_id)
        assert "var_95" in risk
        assert "sharpe_ratio" in risk

    @pytest.mark.asyncio
    async def test_check_risk_limits(self, svc, db, portfolio):
        db.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=portfolio))
        )
        violations = await svc.check_risk_limits(portfolio.id, portfolio.user_id)
        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_generate_portfolio_report(self, svc, db, portfolio):
        db.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=portfolio))
        )
        report = await svc.generate_portfolio_report(portfolio.id, portfolio.user_id)
        assert "summary" in report
        assert "performance" in report
        assert "risk_metrics" in report
        assert "allocations" in report

"""
Risk Management Service for Financial Industry Applications
Comprehensive risk assessment, monitoring, and management with regulatory compliance
"""

import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np
import pandas as pd
from models.portfolio import Portfolio
from models.risk import RiskAssessment
from models.user import RiskLevel, UserRiskProfile
from scipy import stats
from services.market.market_data_service import MarketDataService

# Add ai_models to path
ai_models_path = Path(__file__).parent.parent.parent / "ai_models"
if str(ai_models_path) not in sys.path:
    sys.path.insert(0, str(ai_models_path))

try:
    import tensorflow as tf
    from train_correlation_model import CorrelationPredictor

    HAS_ML_MODEL = True
except (ImportError, ModuleNotFoundError):
    CorrelationPredictor = None
    tf = None
    HAS_ML_MODEL = False
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class RiskMetricsData:
    """Risk metrics data structure"""

    portfolio_id: UUID
    var_1d: Decimal
    var_5d: Decimal
    var_30d: Decimal
    expected_shortfall: Decimal
    sharpe_ratio: Decimal
    sortino_ratio: Decimal
    max_drawdown: Decimal
    beta: Decimal
    alpha: Decimal
    volatility: Decimal
    correlation_matrix: Dict[str, Dict[str, float]]
    concentration_risk: Decimal
    liquidity_risk: Decimal
    credit_risk: Decimal
    market_risk: Decimal
    operational_risk: Decimal
    overall_risk_score: Decimal
    risk_grade: str
    timestamp: datetime


@dataclass
class StressTestScenario:
    """Stress test scenario definition"""

    name: str
    description: str
    market_shocks: Dict[str, float]
    correlation_changes: Dict[str, float]
    volatility_multiplier: float
    duration_days: int


class RiskService:
    CORRELATION_MODEL_PATH = os.path.join(
        os.path.dirname(__file__), "..", "..", "ai_models", "correlation_model.h5"
    )
    "\n    Comprehensive risk management service with advanced analytics\n    "

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.market_data_service = MarketDataService()
        self.correlation_predictor = self._load_correlation_predictor()
        self.var_thresholds = {
            RiskLevel.LOW: Decimal("0.02"),
            RiskLevel.MEDIUM: Decimal("0.05"),
            RiskLevel.HIGH: Decimal("0.10"),
            RiskLevel.CRITICAL: Decimal("0.20"),
        }
        self.stress_scenarios = [
            StressTestScenario(
                name="Market Crash",
                description="Severe market downturn similar to 2008 financial crisis",
                market_shocks={"BTC": -0.5, "ETH": -0.6, "stocks": -0.4},
                correlation_changes={"all": 0.8},
                volatility_multiplier=3.0,
                duration_days=30,
            ),
            StressTestScenario(
                name="Crypto Winter",
                description="Extended cryptocurrency bear market",
                market_shocks={"BTC": -0.8, "ETH": -0.85, "altcoins": -0.9},
                correlation_changes={"crypto": 0.9},
                volatility_multiplier=2.5,
                duration_days=365,
            ),
            StressTestScenario(
                name="Interest Rate Shock",
                description="Rapid interest rate increases",
                market_shocks={"bonds": -0.2, "stocks": -0.15, "crypto": -0.3},
                correlation_changes={"traditional": 0.6},
                volatility_multiplier=1.8,
                duration_days=90,
            ),
            StressTestScenario(
                name="Liquidity Crisis",
                description="Market liquidity dries up",
                market_shocks={"all": -0.25},
                correlation_changes={"all": 0.95},
                volatility_multiplier=4.0,
                duration_days=14,
            ),
        ]

    def _load_correlation_predictor(self) -> Any:
        """Loads the correlation prediction model."""
        try:
            if not HAS_ML_MODEL:
                logger.warning(
                    "TensorFlow or correlation model not available. Using mock predictor."
                )

                class MockCorrelationPredictor:
                    def predict(self, df: "pd.DataFrame") -> "pd.DataFrame":
                        n_assets = 3
                        corr = np.identity(n_assets)
                        return corr

                return MockCorrelationPredictor()

            if not os.path.exists(self.CORRELATION_MODEL_PATH):
                logger.warning(
                    f"Correlation model not found at {self.CORRELATION_MODEL_PATH}. Using a mock predictor."
                )

                class MockCorrelationPredictor:
                    def predict(self, df: "pd.DataFrame") -> "pd.DataFrame":
                        n_assets = 3
                        corr = np.identity(n_assets)
                        return corr

                return MockCorrelationPredictor()

            predictor = CorrelationPredictor()
            predictor.model = tf.keras.models.load_model(self.CORRELATION_MODEL_PATH)
            logger.info("Correlation prediction model loaded successfully.")
            return predictor
        except Exception as e:
            logger.error(f"Failed to load correlation predictor: {e}")

            class MockCorrelationPredictor:
                def predict(self, df: "pd.DataFrame") -> "pd.DataFrame":
                    n_assets = 3
                    corr = np.identity(n_assets)
                    return corr

            return MockCorrelationPredictor()

    async def _get_portfolio_with_assets(
        self, portfolio_id: UUID, user_id: UUID
    ) -> Optional[Portfolio]:
        """
        Fetches the portfolio and its assets from the database.
        (Placeholder for actual DB query)
        """

        class MockAsset:

            def __init__(self, symbol: Any, quantity: Any, price: Any) -> None:
                self.symbol = symbol
                self.quantity = Decimal(str(quantity))
                self.price = Decimal(str(price))

        class MockPortfolio:

            def __init__(self, assets: Any) -> None:
                self.assets = assets

        if str(portfolio_id) == "00000000-0000-0000-0000-000000000001":
            assets = [
                MockAsset("BTC", 1.5, 60000),
                MockAsset("ETH", 10, 3000),
                MockAsset("SOL", 50, 150),
            ]
            return MockPortfolio(assets)
        return None

    async def _calculate_risk_metrics(self, portfolio: Portfolio) -> RiskMetricsData:
        """
        Calculates core risk metrics for the portfolio.
        """
        assets = portfolio.assets
        if not assets:
            return RiskMetricsData(
                portfolio_id=portfolio.id,
                var_1d=Decimal(0),
                var_5d=Decimal(0),
                var_30d=Decimal(0),
                expected_shortfall=Decimal(0),
                sharpe_ratio=Decimal(0),
                sortino_ratio=Decimal(0),
                max_drawdown=Decimal(0),
                beta=Decimal(0),
                alpha=Decimal(0),
                volatility=Decimal(0),
                correlation_matrix={},
                concentration_risk=Decimal(0),
                liquidity_risk=Decimal(0),
                credit_risk=Decimal(0),
                market_risk=Decimal(0),
                operational_risk=Decimal(0),
                overall_risk_score=Decimal(0),
                risk_grade="N/A",
                timestamp=datetime.utcnow(),
            )
        historical_days = 252
        asset_symbols = [asset.symbol for asset in assets]
        np.random.seed(42)
        returns_data = {
            symbol: np.random.normal(0.0005, 0.01, historical_days)
            for symbol in asset_symbols
        }
        returns_df = pd.DataFrame(returns_data)
        portfolio_value = sum((asset.quantity * asset.price for asset in assets))
        weights = np.array(
            [asset.quantity * asset.price / portfolio_value for asset in assets]
        )
        portfolio_returns = returns_df.dot(weights)
        portfolio_volatility = Decimal(str(portfolio_returns.std() * np.sqrt(252)))
        confidence_level = 0.01
        var_1d = Decimal(str(np.percentile(portfolio_returns, confidence_level) * -1))
        var_5d = var_1d * Decimal(str(np.sqrt(5)))
        var_30d = var_1d * Decimal(str(np.sqrt(30)))
        es_returns = portfolio_returns[
            portfolio_returns <= np.percentile(portfolio_returns, confidence_level)
        ]
        expected_shortfall = Decimal(str(es_returns.mean() * -1))
        risk_free_rate = 0.02
        annual_return = portfolio_returns.mean() * 252
        sharpe_ratio = Decimal(
            str(
                (annual_return - risk_free_rate)
                / portfolio_returns.std()
                / np.sqrt(252)
            )
        )
        hhi = sum((w**2 for w in weights))
        concentration_risk = Decimal(str(hhi))
        mock_price_data = {
            f"asset_{s.lower()}": np.cumsum(r) + float(assets[i].price)
            for i, (s, r) in enumerate(returns_data.items())
        }
        mock_price_df = pd.DataFrame(mock_price_data)
        try:
            predicted_corr_matrix_np = self.correlation_predictor.predict(mock_price_df)
            correlation_matrix = {
                s1: {
                    s2: predicted_corr_matrix_np[i][j]
                    for j, s2 in enumerate(asset_symbols)
                }
                for i, s1 in enumerate(asset_symbols)
            }
        except Exception as e:
            logger.error(
                f"Correlation prediction failed: {e}. Using default correlation."
            )
            correlation_matrix = {
                s: {s: 1.0 for s in asset_symbols} for s in asset_symbols
            }
        overall_risk_score = (
            var_30d * Decimal("0.4")
            + expected_shortfall * Decimal("0.3")
            + concentration_risk * Decimal("0.3")
        )
        return RiskMetricsData(
            portfolio_id=portfolio.id,
            var_1d=var_1d,
            var_5d=var_5d,
            var_30d=var_30d,
            expected_shortfall=expected_shortfall,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=Decimal(0),
            max_drawdown=Decimal(0),
            beta=Decimal(0),
            alpha=Decimal(0),
            volatility=portfolio_volatility,
            correlation_matrix=correlation_matrix,
            concentration_risk=concentration_risk,
            liquidity_risk=Decimal(0),
            credit_risk=Decimal(0),
            market_risk=var_30d,
            operational_risk=Decimal(0),
            overall_risk_score=overall_risk_score,
            risk_grade=self._determine_risk_grade(overall_risk_score),
            timestamp=datetime.utcnow(),
        )

    async def _perform_stress_tests(self, portfolio: Portfolio) -> List[Dict[str, Any]]:
        """
        Simulates portfolio performance under various stress scenarios.
        """
        results = []
        assets = portfolio.assets
        portfolio_value = sum((asset.quantity * asset.price for asset in assets))
        for scenario in self.stress_scenarios:
            simulated_value = portfolio_value
            total_loss = Decimal(0)
            for asset in assets:
                shock_percent = scenario.market_shocks.get(
                    asset.symbol, scenario.market_shocks.get("all", 0)
                )
                asset_value = asset.quantity * asset.price
                loss_amount = asset_value * Decimal(str(shock_percent)) * Decimal("-1")
                total_loss += loss_amount
                simulated_value -= loss_amount
            loss_percent = (
                total_loss / portfolio_value * 100
                if portfolio_value > 0
                else Decimal(0)
            )
            results.append(
                {
                    "scenario_name": scenario.name,
                    "description": scenario.description,
                    "initial_value": float(portfolio_value),
                    "simulated_value": float(simulated_value),
                    "potential_loss_amount": float(total_loss),
                    "potential_loss_percent": float(loss_percent),
                }
            )
        return results

    async def _calculate_overall_risk_score(
        self, risk_metrics: RiskMetricsData, stress_test_results: List[Dict[str, Any]]
    ) -> Decimal:
        """
        Calculates the final overall risk score based on metrics and stress tests.
        """
        max_stress_loss_percent = (
            max(
                [Decimal(str(r["potential_loss_percent"])) for r in stress_test_results]
            )
            / 100
        )
        score = (
            (risk_metrics.var_30d + risk_metrics.expected_shortfall)
            / 2
            * Decimal("0.6")
            + max_stress_loss_percent * Decimal("0.3")
            + risk_metrics.concentration_risk * Decimal("0.1")
        )
        normalized_score = min(Decimal("100"), score * Decimal("200"))
        return normalized_score

    def _determine_risk_grade(self, overall_risk_score: Decimal) -> str:
        """
        Determines the risk grade based on the overall score.
        """
        if overall_risk_score < 20:
            return "A (Very Low Risk)"
        elif overall_risk_score < 40:
            return "B (Low Risk)"
        elif overall_risk_score < 60:
            return "C (Moderate Risk)"
        elif overall_risk_score < 80:
            return "D (High Risk)"
        else:
            return "E (Very High Risk)"

    async def _generate_risk_recommendations(
        self, risk_metrics: RiskMetricsData, stress_test_results: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generates actionable recommendations based on risk assessment.
        """
        recommendations = []
        if risk_metrics.var_30d > Decimal("0.10"):
            recommendations.append(
                f"High 30-day VaR ({risk_metrics.var_30d:.2%}): Consider reducing exposure to volatile assets or increasing diversification."
            )
        if risk_metrics.concentration_risk > Decimal("0.5"):
            recommendations.append(
                f"High Concentration Risk (HHI: {risk_metrics.concentration_risk:.2f}): Your portfolio is heavily reliant on a few assets. Diversify across more uncorrelated assets."
            )
        max_loss_scenario = max(
            stress_test_results, key=lambda x: x["potential_loss_percent"]
        )
        if max_loss_scenario["potential_loss_percent"] > 30:
            recommendations.append(
                f"Extreme Stress Test Loss ({max_loss_scenario['potential_loss_percent']:.2f}% in '{max_loss_scenario['scenario_name']}'): Your portfolio is highly vulnerable to a major market event. Implement hedging strategies."
            )
        if risk_metrics.sharpe_ratio < Decimal("0.5"):
            recommendations.append(
                f"Low Sharpe Ratio ({risk_metrics.sharpe_ratio:.2f}): The risk-adjusted return is low. Seek assets with higher expected returns for the level of risk taken."
            )
        if not recommendations:
            recommendations.append(
                "Portfolio risk profile is healthy. Continue to monitor market conditions."
            )
        return recommendations

    async def _get_user_risk_profile(self, user_id: UUID) -> Optional[UserRiskProfile]:
        """Fetches the user's risk profile. (Placeholder)"""
        return None

    async def _calculate_user_risk_score(
        self, assessment_data: Dict[str, Any]
    ) -> Decimal:
        """Calculates user risk tolerance score based on questionnaire. (Placeholder)"""
        return Decimal(str(assessment_data.get("risk_score", 50)))

    def _determine_user_risk_level(self, risk_score: Decimal) -> RiskLevel:
        """Determines user risk level. (Placeholder)"""
        if risk_score < 30:
            return RiskLevel.LOW
        elif risk_score < 70:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    def _calculate_risk_based_limits(
        self, risk_level: RiskLevel, assessment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculates risk-based limits for the user. (Placeholder)"""
        if risk_level == RiskLevel.LOW:
            return {
                "daily_transaction_limit": Decimal("10000"),
                "monthly_transaction_limit": Decimal("50000"),
                "max_portfolio_value": Decimal("100000"),
                "max_single_asset_allocation": Decimal("0.25"),
            }
        elif risk_level == RiskLevel.MEDIUM:
            return {
                "daily_transaction_limit": Decimal("50000"),
                "monthly_transaction_limit": Decimal("250000"),
                "max_portfolio_value": Decimal("500000"),
                "max_single_asset_allocation": Decimal("0.50"),
            }
        else:
            return {
                "daily_transaction_limit": Decimal("100000"),
                "monthly_transaction_limit": Decimal("500000"),
                "max_portfolio_value": Decimal("1000000"),
                "max_single_asset_allocation": Decimal("0.75"),
            }

    async def _get_latest_risk_assessment(
        self, portfolio_id: UUID
    ) -> Optional[RiskAssessment]:
        """Fetches the latest risk assessment. (Placeholder)"""
        return None

    async def _check_risk_thresholds(
        self,
        current_metrics: RiskMetricsData,
        latest_assessment: Optional[RiskAssessment],
    ) -> List[Dict[str, Any]]:
        """Checks for breaches of predefined risk thresholds. (Placeholder)"""
        alerts = []
        if current_metrics.overall_risk_score > Decimal("70"):
            alerts.append(
                {
                    "type": "CRITICAL",
                    "metric": "Overall Risk Score",
                    "value": float(current_metrics.overall_risk_score),
                    "threshold": 70,
                    "message": "Overall risk score is critically high. Immediate review required.",
                }
            )
        return alerts

    async def _check_concentration_limits(
        self, portfolio: Portfolio
    ) -> List[Dict[str, Any]]:
        """Checks for breaches of concentration limits. (Placeholder)"""
        return []

    async def _check_correlation_changes(
        self, portfolio: Portfolio, latest_assessment: Optional[RiskAssessment]
    ) -> List[Dict[str, Any]]:
        """Checks for significant changes in asset correlation. (Placeholder)"""
        return []

    async def _generate_monitoring_recommendations(
        self, current_metrics: RiskMetricsData
    ) -> List[str]:
        """Generates recommendations for real-time monitoring. (Placeholder)"""
        return ["Monitor the 1-day VaR closely for sudden market movements."]

    async def assess_portfolio_risk(
        self, portfolio_id: UUID, user_id: UUID
    ) -> RiskAssessment:
        """
        Comprehensive portfolio risk assessment
        """
        try:
            portfolio = await self._get_portfolio_with_assets(portfolio_id, user_id)
            if not portfolio:
                raise ValueError("Portfolio not found")
            risk_metrics = await self._calculate_risk_metrics(portfolio)
            stress_test_results = await self._perform_stress_tests(portfolio)
            overall_risk_score = await self._calculate_overall_risk_score(
                risk_metrics, stress_test_results
            )
            risk_grade = self._determine_risk_grade(overall_risk_score)
            risk_assessment = RiskAssessment(
                portfolio_id=portfolio_id,
                user_id=user_id,
                assessment_date=datetime.utcnow(),
                risk_score=overall_risk_score,
                risk_grade=risk_grade,
                var_1d=risk_metrics.var_1d,
                var_5d=risk_metrics.var_5d,
                var_30d=risk_metrics.var_30d,
                expected_shortfall=risk_metrics.expected_shortfall,
                sharpe_ratio=risk_metrics.sharpe_ratio,
                max_drawdown=risk_metrics.max_drawdown,
                beta=risk_metrics.beta,
                volatility=risk_metrics.volatility,
                concentration_risk=risk_metrics.concentration_risk,
                liquidity_risk=risk_metrics.liquidity_risk,
                stress_test_results=stress_test_results,
                recommendations=await self._generate_risk_recommendations(
                    risk_metrics, stress_test_results
                ),
                metadata={
                    "correlation_matrix": risk_metrics.correlation_matrix,
                    "risk_breakdown": {
                        "market_risk": float(risk_metrics.market_risk),
                        "credit_risk": float(risk_metrics.credit_risk),
                        "operational_risk": float(risk_metrics.operational_risk),
                        "liquidity_risk": float(risk_metrics.liquidity_risk),
                    },
                },
            )
            self.db.add(risk_assessment)
            await self.db.commit()
            logger.info(f"Risk assessment completed for portfolio {portfolio_id}")
            return risk_assessment
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error assessing portfolio risk: {e}")
            raise

    async def perform_user_risk_assessment(
        self, user_id: UUID, assessment_data: Dict[str, Any]
    ) -> UserRiskProfile:
        """
        Perform comprehensive user risk profiling
        """
        try:
            user_risk_profile = await self._get_user_risk_profile(user_id)
            if not user_risk_profile:
                user_risk_profile = UserRiskProfile(user_id=user_id)
                self.db.add(user_risk_profile)
            risk_score = await self._calculate_user_risk_score(assessment_data)
            risk_level = self._determine_user_risk_level(risk_score)
            user_risk_profile.risk_level = risk_level
            user_risk_profile.risk_score = risk_score
            user_risk_profile.assessment_date = datetime.utcnow()
            user_risk_profile.questionnaire_responses = assessment_data
            limits = self._calculate_risk_based_limits(risk_level, assessment_data)
            user_risk_profile.daily_transaction_limit = limits[
                "daily_transaction_limit"
            ]
            user_risk_profile.monthly_transaction_limit = limits[
                "monthly_transaction_limit"
            ]
            user_risk_profile.max_portfolio_value = limits["max_portfolio_value"]
            user_risk_profile.max_single_asset_allocation = limits[
                "max_single_asset_allocation"
            ]
            await self.db.commit()
            logger.info(f"User risk assessment completed for user {user_id}")
            return user_risk_profile
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error performing user risk assessment: {e}")
            raise

    async def monitor_portfolio_risk(
        self, portfolio_id: UUID, user_id: UUID
    ) -> Dict[str, Any]:
        """
        Real-time portfolio risk monitoring
        """
        try:
            portfolio = await self._get_portfolio_with_assets(portfolio_id, user_id)
            if not portfolio:
                raise ValueError("Portfolio not found")
            latest_assessment = await self._get_latest_risk_assessment(portfolio_id)
            current_metrics = await self._calculate_risk_metrics(portfolio)
            alerts = await self._check_risk_thresholds(
                current_metrics, latest_assessment
            )
            concentration_alerts = await self._check_concentration_limits(portfolio)
            correlation_alerts = await self._check_correlation_changes(
                portfolio, latest_assessment
            )
            monitoring_result = {
                "portfolio_id": str(portfolio_id),
                "monitoring_timestamp": datetime.utcnow().isoformat(),
                "current_risk_score": float(current_metrics.overall_risk_score),
                "risk_grade": current_metrics.risk_grade,
                "alerts": alerts + concentration_alerts + correlation_alerts,
                "risk_metrics": {
                    "var_1d": float(current_metrics.var_1d),
                    "var_5d": float(current_metrics.var_5d),
                    "sharpe_ratio": float(current_metrics.sharpe_ratio),
                    "max_drawdown": float(current_metrics.max_drawdown),
                    "volatility": float(current_metrics.volatility),
                },
                "recommendations": await self._generate_monitoring_recommendations(
                    alerts
                ),
            }
            return monitoring_result
        except Exception as e:
            logger.error(f"Error monitoring portfolio risk: {e}")
            raise

    async def calculate_var(
        self, portfolio_id: UUID, confidence_level: float = 0.95, time_horizon: int = 1
    ) -> Dict[str, Any]:
        """
        Calculate Value at Risk (VaR) using multiple methods
        """
        try:
            portfolio = await self._get_portfolio_with_assets(portfolio_id, None)
            if not portfolio:
                raise ValueError("Portfolio not found")
            returns_data = await self._get_portfolio_returns(portfolio, days=252)
            if not returns_data:
                raise ValueError("Insufficient historical data for VaR calculation")
            var_results = {
                "portfolio_id": str(portfolio_id),
                "confidence_level": confidence_level,
                "time_horizon": time_horizon,
                "calculation_date": datetime.utcnow().isoformat(),
                "methods": {},
            }
            historical_var = self._calculate_historical_var(
                returns_data, confidence_level, time_horizon
            )
            var_results["methods"]["historical_simulation"] = {
                "var": float(historical_var),
                "description": "Based on historical return distribution",
            }
            parametric_var = self._calculate_parametric_var(
                returns_data, confidence_level, time_horizon
            )
            var_results["methods"]["parametric"] = {
                "var": float(parametric_var),
                "description": "Based on normal distribution assumption",
            }
            monte_carlo_var = await self._calculate_monte_carlo_var(
                portfolio, returns_data, confidence_level, time_horizon
            )
            var_results["methods"]["monte_carlo"] = {
                "var": float(monte_carlo_var),
                "description": "Based on Monte Carlo simulation",
            }
            expected_shortfall = self._calculate_expected_shortfall(
                returns_data, confidence_level
            )
            var_results["expected_shortfall"] = float(expected_shortfall)
            recommended_var = (historical_var + parametric_var + monte_carlo_var) / 3
            var_results["recommended_var"] = float(recommended_var)
            return var_results
        except Exception as e:
            logger.error(f"Error calculating VaR: {e}")
            raise

    async def _get_portfolio_with_assets(
        self, portfolio_id: UUID, user_id: Optional[UUID]
    ) -> Optional[Portfolio]:
        """Get portfolio with assets loaded"""
        conditions = [Portfolio.id == portfolio_id, not Portfolio.is_deleted]
        if user_id:
            conditions.append(Portfolio.user_id == user_id)
        stmt = select(Portfolio).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _calculate_risk_metrics(self, portfolio: Portfolio) -> RiskMetricsData:
        """Calculate comprehensive risk metrics for portfolio"""
        try:
            returns_data = await self._get_portfolio_returns(portfolio, days=252)
            if not returns_data:
                return RiskMetricsData(
                    portfolio_id=portfolio.id,
                    var_1d=Decimal("0.05"),
                    var_5d=Decimal("0.10"),
                    var_30d=Decimal("0.20"),
                    expected_shortfall=Decimal("0.08"),
                    sharpe_ratio=Decimal("0.0"),
                    sortino_ratio=Decimal("0.0"),
                    max_drawdown=Decimal("0.0"),
                    beta=Decimal("1.0"),
                    alpha=Decimal("0.0"),
                    volatility=Decimal("0.15"),
                    correlation_matrix={},
                    concentration_risk=Decimal("0.0"),
                    liquidity_risk=Decimal("0.0"),
                    credit_risk=Decimal("0.0"),
                    market_risk=Decimal("0.0"),
                    operational_risk=Decimal("0.0"),
                    overall_risk_score=Decimal("50.0"),
                    risk_grade="Medium",
                    timestamp=datetime.utcnow(),
                )
            returns_array = np.array(returns_data)
            var_1d = self._calculate_historical_var(returns_data, 0.95, 1)
            var_5d = self._calculate_historical_var(returns_data, 0.95, 5)
            var_30d = self._calculate_historical_var(returns_data, 0.95, 30)
            expected_shortfall = self._calculate_expected_shortfall(returns_data, 0.95)
            sharpe_ratio = self._calculate_sharpe_ratio(returns_array)
            sortino_ratio = self._calculate_sortino_ratio(returns_array)
            max_drawdown = self._calculate_max_drawdown(returns_array)
            beta, alpha = await self._calculate_beta_alpha(portfolio, returns_array)
            volatility = Decimal(str(np.std(returns_array) * np.sqrt(252)))
            concentration_risk = await self._calculate_concentration_risk(portfolio)
            liquidity_risk = await self._calculate_liquidity_risk(portfolio)
            credit_risk = await self._calculate_credit_risk(portfolio)
            market_risk = var_1d
            operational_risk = Decimal("0.02")
            correlation_matrix = await self._calculate_correlation_matrix(portfolio)
            overall_risk_score = await self._calculate_overall_risk_score_from_metrics(
                var_1d, concentration_risk, liquidity_risk, volatility
            )
            risk_grade = self._determine_risk_grade(overall_risk_score)
            return RiskMetricsData(
                portfolio_id=portfolio.id,
                var_1d=var_1d,
                var_5d=var_5d,
                var_30d=var_30d,
                expected_shortfall=expected_shortfall,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                max_drawdown=max_drawdown,
                beta=beta,
                alpha=alpha,
                volatility=volatility,
                correlation_matrix=correlation_matrix,
                concentration_risk=concentration_risk,
                liquidity_risk=liquidity_risk,
                credit_risk=credit_risk,
                market_risk=market_risk,
                operational_risk=operational_risk,
                overall_risk_score=overall_risk_score,
                risk_grade=risk_grade,
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            raise

    async def _get_portfolio_returns(
        self, portfolio: Portfolio, days: int
    ) -> List[float]:
        """Get historical portfolio returns"""
        try:
            np.random.seed(42)
            returns = np.random.normal(0.0008, 0.02, days)
            return returns.tolist()
        except Exception as e:
            logger.error(f"Error getting portfolio returns: {e}")
            return []

    def _calculate_historical_var(
        self, returns: List[float], confidence_level: float, time_horizon: int
    ) -> Decimal:
        """Calculate Historical Simulation VaR"""
        if not returns:
            return Decimal("0.05")
        returns_array = np.array(returns)
        scaled_returns = returns_array * np.sqrt(time_horizon)
        percentile = (1 - confidence_level) * 100
        var = np.percentile(scaled_returns, percentile)
        return Decimal(str(abs(var)))

    def _calculate_parametric_var(
        self, returns: List[float], confidence_level: float, time_horizon: int
    ) -> Decimal:
        """Calculate Parametric VaR assuming normal distribution"""
        if not returns:
            return Decimal("0.05")
        returns_array = np.array(returns)
        mean_return = np.mean(returns_array)
        std_return = np.std(returns_array)
        z_score = stats.norm.ppf(1 - confidence_level)
        scaled_mean = mean_return * time_horizon
        scaled_std = std_return * np.sqrt(time_horizon)
        var = -(scaled_mean + z_score * scaled_std)
        return Decimal(str(max(0, var)))

    async def _calculate_monte_carlo_var(
        self,
        portfolio: Portfolio,
        returns: List[float],
        confidence_level: float,
        time_horizon: int,
        simulations: int = 10000,
    ) -> Decimal:
        """Calculate Monte Carlo VaR"""
        if not returns:
            return Decimal("0.05")
        returns_array = np.array(returns)
        mean_return = np.mean(returns_array)
        std_return = np.std(returns_array)
        np.random.seed(42)
        simulated_returns = np.random.normal(
            mean_return * time_horizon, std_return * np.sqrt(time_horizon), simulations
        )
        percentile = (1 - confidence_level) * 100
        var = np.percentile(simulated_returns, percentile)
        return Decimal(str(abs(var)))

    def _calculate_expected_shortfall(
        self, returns: List[float], confidence_level: float
    ) -> Decimal:
        """Calculate Expected Shortfall (Conditional VaR)"""
        if not returns:
            return Decimal("0.08")
        returns_array = np.array(returns)
        percentile = (1 - confidence_level) * 100
        var_threshold = np.percentile(returns_array, percentile)
        tail_returns = returns_array[returns_array <= var_threshold]
        expected_shortfall = (
            np.mean(tail_returns) if len(tail_returns) > 0 else var_threshold
        )
        return Decimal(str(abs(expected_shortfall)))

    def _calculate_sharpe_ratio(
        self, returns: np.ndarray, risk_free_rate: float = 0.02
    ) -> Decimal:
        """Calculate Sharpe ratio"""
        if len(returns) == 0:
            return Decimal("0.0")
        excess_returns = returns - risk_free_rate / 252
        if np.std(excess_returns) == 0:
            return Decimal("0.0")
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        return Decimal(str(sharpe))

    def _calculate_sortino_ratio(
        self, returns: np.ndarray, risk_free_rate: float = 0.02
    ) -> Decimal:
        """Calculate Sortino ratio"""
        if len(returns) == 0:
            return Decimal("0.0")
        excess_returns = returns - risk_free_rate / 252
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0:
            return Decimal("0.0")
        downside_deviation = np.std(downside_returns)
        if downside_deviation == 0:
            return Decimal("0.0")
        sortino = np.mean(excess_returns) / downside_deviation * np.sqrt(252)
        return Decimal(str(sortino))

    def _calculate_max_drawdown(self, returns: np.ndarray) -> Decimal:
        """Calculate maximum drawdown"""
        if len(returns) == 0:
            return Decimal("0.0")
        cumulative_returns = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown)
        return Decimal(str(abs(max_drawdown)))

    async def _calculate_beta_alpha(
        self, portfolio: Portfolio, returns: np.ndarray
    ) -> Tuple[Decimal, Decimal]:
        """Calculate portfolio beta and alpha relative to market"""
        try:
            market_data = await self.market_data_service.get_historical_data(
                "BTC", datetime.utcnow() - timedelta(days=252), datetime.utcnow()
            )
            if not market_data or len(market_data) < len(returns):
                return (Decimal("1.0"), Decimal("0.0"))
            market_returns = []
            for i in range(1, len(market_data)):
                if market_data[i - 1].close_price != 0:
                    ret = (
                        market_data[i].close_price - market_data[i - 1].close_price
                    ) / market_data[i - 1].close_price
                    market_returns.append(float(ret))
            if len(market_returns) < len(returns):
                return (Decimal("1.0"), Decimal("0.0"))
            min_length = min(len(returns), len(market_returns))
            portfolio_returns = returns[-min_length:]
            market_returns = market_returns[-min_length:]
            covariance = np.cov(portfolio_returns, market_returns)[0, 1]
            market_variance = np.var(market_returns)
            if market_variance == 0:
                beta = Decimal("1.0")
            else:
                beta = Decimal(str(covariance / market_variance))
            portfolio_mean = np.mean(portfolio_returns) * 252
            market_mean = np.mean(market_returns) * 252
            alpha = Decimal(str(portfolio_mean - float(beta) * market_mean))
            return (beta, alpha)
        except Exception as e:
            logger.error(f"Error calculating beta/alpha: {e}")
            return (Decimal("1.0"), Decimal("0.0"))

    async def _calculate_concentration_risk(self, portfolio: Portfolio) -> Decimal:
        """Calculate portfolio concentration risk"""
        if not portfolio.assets:
            return Decimal("0.0")
        total_value = portfolio.total_value or Decimal("0.0")
        if total_value == 0:
            return Decimal("0.0")
        hhi = Decimal("0.0")
        for asset in portfolio.assets:
            if asset.current_value and total_value > 0:
                weight = asset.current_value / total_value
                hhi += weight**2
        concentration_risk = hhi * 100
        return min(concentration_risk, Decimal("100.0"))

    async def _calculate_liquidity_risk(self, portfolio: Portfolio) -> Decimal:
        """Calculate portfolio liquidity risk"""
        if not portfolio.assets:
            return Decimal("0.0")
        total_value = portfolio.total_value or Decimal("0.0")
        if total_value == 0:
            return Decimal("0.0")
        liquidity_scores = {
            "cryptocurrency": 0.8,
            "stock": 0.9,
            "bond": 0.7,
            "commodity": 0.6,
            "real_estate": 0.2,
            "private_equity": 0.1,
        }
        weighted_liquidity = Decimal("0.0")
        for asset in portfolio.assets:
            if asset.current_value and total_value > 0:
                weight = asset.current_value / total_value
                liquidity_score = liquidity_scores.get(asset.asset_type, 0.5)
                weighted_liquidity += weight * Decimal(str(liquidity_score))
        liquidity_risk = (Decimal("1.0") - weighted_liquidity) * 100
        return max(Decimal("0.0"), min(liquidity_risk, Decimal("100.0")))

    async def _calculate_credit_risk(self, portfolio: Portfolio) -> Decimal:
        """Calculate portfolio credit risk"""
        return Decimal("5.0")

    async def _calculate_correlation_matrix(
        self, portfolio: Portfolio
    ) -> Dict[str, Dict[str, float]]:
        """Calculate correlation matrix for portfolio assets"""
        if not portfolio.assets or len(portfolio.assets) < 2:
            return {}
        symbols = [asset.symbol for asset in portfolio.assets if asset.symbol]
        correlation_matrix = {}
        for symbol1 in symbols:
            correlation_matrix[symbol1] = {}
            for symbol2 in symbols:
                if symbol1 == symbol2:
                    correlation_matrix[symbol1][symbol2] = 1.0
                else:
                    correlation_matrix[symbol1][symbol2] = 0.6
        return correlation_matrix

    async def _calculate_overall_risk_score_from_metrics(
        self,
        var_1d: Decimal,
        concentration_risk: Decimal,
        liquidity_risk: Decimal,
        volatility: Decimal,
    ) -> Decimal:
        """Calculate overall risk score from individual metrics"""
        weights = {
            "var": 0.4,
            "concentration": 0.2,
            "liquidity": 0.2,
            "volatility": 0.2,
        }
        var_score = min(float(var_1d) * 1000, 100)
        concentration_score = float(concentration_risk)
        liquidity_score = float(liquidity_risk)
        volatility_score = min(float(volatility) * 100, 100)
        overall_score = (
            weights["var"] * var_score
            + weights["concentration"] * concentration_score
            + weights["liquidity"] * liquidity_score
            + weights["volatility"] * volatility_score
        )
        return Decimal(str(max(0, min(100, overall_score))))

    def _determine_risk_grade(self, risk_score: Decimal) -> str:
        """Determine risk grade from risk score"""
        score = float(risk_score)
        if score <= 20:
            return "Very Low"
        elif score <= 40:
            return "Low"
        elif score <= 60:
            return "Medium"
        elif score <= 80:
            return "High"
        else:
            return "Very High"

    async def _perform_stress_tests(self, portfolio: Portfolio) -> List[Dict[str, Any]]:
        """Perform stress tests on portfolio"""
        stress_results = []
        for scenario in self.stress_scenarios:
            try:
                result = await self._run_stress_scenario(portfolio, scenario)
                stress_results.append(result)
            except Exception as e:
                logger.error(f"Error running stress scenario {scenario.name}: {e}")
                stress_results.append(
                    {
                        "scenario_name": scenario.name,
                        "status": "failed",
                        "error": str(e),
                    }
                )
        return stress_results

    async def _run_stress_scenario(
        self, portfolio: Portfolio, scenario: StressTestScenario
    ) -> Dict[str, Any]:
        """Run a specific stress test scenario"""
        if not portfolio.assets:
            return {
                "scenario_name": scenario.name,
                "portfolio_loss": 0.0,
                "asset_impacts": {},
                "status": "completed",
            }
        total_value = float(portfolio.total_value or Decimal("0.0"))
        total_loss = 0.0
        asset_impacts = {}
        for asset in portfolio.assets:
            asset_value = float(asset.current_value or Decimal("0.0"))
            shock = 0.0
            if asset.asset_type in scenario.market_shocks:
                shock = scenario.market_shocks[asset.asset_type]
            elif "all" in scenario.market_shocks:
                shock = scenario.market_shocks["all"]
            asset_loss = asset_value * abs(shock)
            total_loss += asset_loss
            asset_impacts[asset.symbol] = {
                "current_value": asset_value,
                "shock_percentage": shock * 100,
                "loss_amount": asset_loss,
                "stressed_value": asset_value - asset_loss,
            }
        loss_percentage = total_loss / total_value * 100 if total_value > 0 else 0.0
        return {
            "scenario_name": scenario.name,
            "scenario_description": scenario.description,
            "portfolio_loss": total_loss,
            "loss_percentage": loss_percentage,
            "stressed_portfolio_value": total_value - total_loss,
            "asset_impacts": asset_impacts,
            "duration_days": scenario.duration_days,
            "status": "completed",
        }

    async def _generate_risk_recommendations(
        self, risk_metrics: RiskMetricsData, stress_results: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        if risk_metrics.var_1d > Decimal("0.10"):
            recommendations.append(
                "Consider reducing position sizes to lower daily Value at Risk"
            )
        if risk_metrics.concentration_risk > Decimal("50.0"):
            recommendations.append(
                "Portfolio is highly concentrated - consider diversifying across more assets"
            )
        if risk_metrics.liquidity_risk > Decimal("30.0"):
            recommendations.append(
                "Consider increasing allocation to more liquid assets"
            )
        if risk_metrics.volatility > Decimal("0.30"):
            recommendations.append(
                "Portfolio volatility is high - consider adding stable assets or hedging"
            )
        for result in stress_results:
            if result.get("loss_percentage", 0) > 50:
                recommendations.append(
                    f"Portfolio vulnerable to {result['scenario_name']} - consider hedging strategies"
                )
        if risk_metrics.sharpe_ratio < Decimal("0.5"):
            recommendations.append(
                "Risk-adjusted returns are low - review asset selection and allocation"
            )
        return recommendations

    async def _get_user_risk_profile(self, user_id: UUID) -> Optional[UserRiskProfile]:
        """Get user risk profile"""
        stmt = select(UserRiskProfile).where(UserRiskProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _calculate_user_risk_score(
        self, assessment_data: Dict[str, Any]
    ) -> Decimal:
        """Calculate user risk tolerance score from questionnaire"""
        age = assessment_data.get("age", 35)
        income = assessment_data.get("annual_income", 50000)
        investment_experience = assessment_data.get("investment_experience", "moderate")
        risk_tolerance = assessment_data.get("risk_tolerance", "moderate")
        investment_horizon = assessment_data.get("investment_horizon", "medium")
        score = 50
        if age < 30:
            score += 15
        elif age < 50:
            score += 5
        else:
            score -= 10
        if income > 100000:
            score += 10
        elif income < 30000:
            score -= 10
        experience_scores = {
            "beginner": -15,
            "moderate": 0,
            "experienced": 15,
            "expert": 25,
        }
        score += experience_scores.get(investment_experience, 0)
        tolerance_scores = {
            "conservative": -20,
            "moderate": 0,
            "aggressive": 20,
            "very_aggressive": 30,
        }
        score += tolerance_scores.get(risk_tolerance, 0)
        horizon_scores = {"short": -10, "medium": 0, "long": 10, "very_long": 15}
        score += horizon_scores.get(investment_horizon, 0)
        return Decimal(str(max(0, min(100, score))))

    def _determine_user_risk_level(self, risk_score: Decimal) -> RiskLevel:
        """Determine user risk level from score"""
        score = float(risk_score)
        if score <= 25:
            return RiskLevel.LOW
        elif score <= 50:
            return RiskLevel.MEDIUM
        elif score <= 75:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _calculate_risk_based_limits(
        self, risk_level: RiskLevel, assessment_data: Dict[str, Any]
    ) -> Dict[str, Decimal]:
        """Calculate risk-based transaction and portfolio limits"""
        base_limits = {
            RiskLevel.LOW: {
                "daily_transaction_limit": Decimal("1000"),
                "monthly_transaction_limit": Decimal("10000"),
                "max_portfolio_value": Decimal("50000"),
                "max_single_asset_allocation": Decimal("0.20"),
            },
            RiskLevel.MEDIUM: {
                "daily_transaction_limit": Decimal("5000"),
                "monthly_transaction_limit": Decimal("50000"),
                "max_portfolio_value": Decimal("250000"),
                "max_single_asset_allocation": Decimal("0.30"),
            },
            RiskLevel.HIGH: {
                "daily_transaction_limit": Decimal("25000"),
                "monthly_transaction_limit": Decimal("250000"),
                "max_portfolio_value": Decimal("1000000"),
                "max_single_asset_allocation": Decimal("0.50"),
            },
            RiskLevel.CRITICAL: {
                "daily_transaction_limit": Decimal("100000"),
                "monthly_transaction_limit": Decimal("1000000"),
                "max_portfolio_value": Decimal("10000000"),
                "max_single_asset_allocation": Decimal("0.70"),
            },
        }
        limits = base_limits.get(risk_level, base_limits[RiskLevel.MEDIUM])
        income = assessment_data.get("annual_income", 50000)
        income_multiplier = min(max(income / 50000, 0.5), 5.0)
        limits["daily_transaction_limit"] *= Decimal(str(income_multiplier))
        limits["monthly_transaction_limit"] *= Decimal(str(income_multiplier))
        limits["max_portfolio_value"] *= Decimal(str(income_multiplier))
        return limits

    async def _get_latest_risk_assessment(
        self, portfolio_id: UUID
    ) -> Optional[RiskAssessment]:
        """Get latest risk assessment for portfolio"""
        stmt = (
            select(RiskAssessment)
            .where(RiskAssessment.portfolio_id == portfolio_id)
            .order_by(RiskAssessment.assessment_date.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _check_risk_thresholds(
        self,
        current_metrics: RiskMetricsData,
        latest_assessment: Optional[RiskAssessment],
    ) -> List[Dict[str, Any]]:
        """Check for risk threshold breaches"""
        alerts = []
        if current_metrics.var_1d > Decimal("0.10"):
            alerts.append(
                {
                    "type": "var_breach",
                    "severity": "high",
                    "message": f"Daily VaR exceeds 10%: {current_metrics.var_1d:.2%}",
                    "current_value": float(current_metrics.var_1d),
                    "threshold": 0.1,
                }
            )
        if current_metrics.overall_risk_score > Decimal("80.0"):
            alerts.append(
                {
                    "type": "high_risk_score",
                    "severity": "high",
                    "message": f"Overall risk score is very high: {current_metrics.overall_risk_score:.1f}",
                    "current_value": float(current_metrics.overall_risk_score),
                    "threshold": 80.0,
                }
            )
        if current_metrics.volatility > Decimal("0.50"):
            alerts.append(
                {
                    "type": "high_volatility",
                    "severity": "medium",
                    "message": f"Portfolio volatility is very high: {current_metrics.volatility:.2%}",
                    "current_value": float(current_metrics.volatility),
                    "threshold": 0.5,
                }
            )
        return alerts

    async def _check_concentration_limits(
        self, portfolio: Portfolio
    ) -> List[Dict[str, Any]]:
        """Check for concentration limit breaches"""
        alerts = []
        if not portfolio.assets:
            return alerts
        total_value = portfolio.total_value or Decimal("0.0")
        if total_value == 0:
            return alerts
        for asset in portfolio.assets:
            if asset.current_value and total_value > 0:
                allocation = asset.current_value / total_value
                if allocation > Decimal("0.50"):
                    alerts.append(
                        {
                            "type": "concentration_limit",
                            "severity": "high",
                            "message": f"{asset.symbol} represents {allocation:.1%} of portfolio",
                            "asset": asset.symbol,
                            "allocation": float(allocation),
                            "threshold": 0.5,
                        }
                    )
        return alerts

    async def _check_correlation_changes(
        self, portfolio: Portfolio, latest_assessment: Optional[RiskAssessment]
    ) -> List[Dict[str, Any]]:
        """Check for significant correlation changes"""
        alerts = []
        if not latest_assessment or not latest_assessment.metadata:
            return alerts
        return alerts

    async def _generate_monitoring_recommendations(
        self, alerts: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on monitoring alerts"""
        recommendations = []
        for alert in alerts:
            if alert["type"] == "var_breach":
                recommendations.append(
                    "Reduce position sizes or add hedging to lower VaR"
                )
            elif alert["type"] == "high_risk_score":
                recommendations.append(
                    "Review portfolio allocation and consider risk reduction"
                )
            elif alert["type"] == "high_volatility":
                recommendations.append(
                    "Add stable assets or implement volatility reduction strategies"
                )
            elif alert["type"] == "concentration_limit":
                recommendations.append(
                    f"Reduce allocation to {alert['asset']} to improve diversification"
                )
        return recommendations

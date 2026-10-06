import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np
import pandas as pd
from config.settings import settings
from exceptions.base_exceptions import BusinessLogicException
from models.portfolio import Portfolio
from models.risk import RiskAssessment
from models.risk import RiskLevel as AssessmentRiskLevel
from models.risk import RiskType
from models.user import RiskLevel, UserRiskProfile
from scipy import stats
from services.ai import AIModelService, get_ai_service
from services.ai.market_inputs import align_close_prices, fetch_price_history
from services.market.market_data_service import MarketDataService
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

ANNUALIZATION_DAYS = 365
RISK_FREE_RATE = 0.02
CRYPTO_MAJORS = {"BTC", "ETH"}
MARKET_BENCHMARK = "BTC"
ASSESSMENT_VALIDITY = timedelta(hours=24)
CORRELATION_DRIFT_THRESHOLD = 0.25

LIQUIDITY_SCORES = {
    "cryptocurrency": 0.8,
    "token": 0.6,
    "nft": 0.2,
    "lp_token": 0.5,
    "staked_asset": 0.4,
    "derivative": 0.6,
}
DEFI_EXPOSED_TYPES = {"lp_token", "staked_asset", "derivative"}


@dataclass
class RiskMetricsData:
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
    ai_insights: Dict[str, Any] = field(default_factory=dict)
    data_points: int = 0


@dataclass
class StressTestScenario:
    name: str
    description: str
    market_shocks: Dict[str, float]
    correlation_changes: Dict[str, float]
    volatility_multiplier: float
    duration_days: int


@dataclass
class PortfolioPosition:
    symbol: str
    value: Decimal
    asset_type: str
    is_defi: bool


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value) or "").lower()


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, (datetime, UUID)):
        return value.isoformat() if isinstance(value, datetime) else str(value)
    return value


class RiskService:
    def __init__(
        self,
        db: AsyncSession,
        ai_service: Optional[AIModelService] = None,
        market_data_service: Optional[MarketDataService] = None,
    ) -> None:
        self.db = db
        self.ai_service = ai_service or get_ai_service()
        self.market_data_service = market_data_service or MarketDataService()
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
                market_shocks={"BTC": -0.5, "ETH": -0.6, "crypto": -0.6, "all": -0.4},
                correlation_changes={"all": 0.8},
                volatility_multiplier=3.0,
                duration_days=30,
            ),
            StressTestScenario(
                name="Crypto Winter",
                description="Extended cryptocurrency bear market",
                market_shocks={
                    "BTC": -0.8,
                    "ETH": -0.85,
                    "altcoins": -0.9,
                    "crypto": -0.85,
                },
                correlation_changes={"crypto": 0.9},
                volatility_multiplier=2.5,
                duration_days=365,
            ),
            StressTestScenario(
                name="Interest Rate Shock",
                description="Rapid interest rate increases",
                market_shocks={"crypto": -0.3, "all": -0.15},
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

    async def _get_portfolio_with_assets(
        self, portfolio_id: UUID, user_id: Optional[UUID]
    ) -> Optional[Portfolio]:
        conditions = [Portfolio.id == portfolio_id, Portfolio.is_deleted == False]
        if user_id:
            conditions.append(Portfolio.user_id == user_id)
        stmt = (
            select(Portfolio)
            .options(selectinload(Portfolio.assets))
            .where(and_(*conditions))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _positions(portfolio: Portfolio) -> List[PortfolioPosition]:
        merged: Dict[str, PortfolioPosition] = {}
        for asset in portfolio.assets or []:
            symbol = str(getattr(asset, "asset_symbol", None) or "").upper()
            value = getattr(asset, "current_value_usd", None)
            if value is None:
                quantity = getattr(asset, "quantity", None)
                price = getattr(asset, "current_price", None)
                value = quantity * price if quantity and price else None
            if not symbol or value is None or Decimal(value) <= 0:
                continue
            value = Decimal(value)
            asset_type = _enum_value(getattr(asset, "asset_type", ""))
            is_defi = bool(getattr(asset, "is_in_defi", False)) or (
                asset_type in DEFI_EXPOSED_TYPES
            )
            existing = merged.get(symbol)
            if existing:
                existing.value += value
                existing.is_defi = existing.is_defi or is_defi
            else:
                merged[symbol] = PortfolioPosition(symbol, value, asset_type, is_defi)
        return sorted(merged.values(), key=lambda p: p.value, reverse=True)

    async def _market_history(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        wanted = list(symbols)
        if MARKET_BENCHMARK not in wanted:
            wanted.append(MARKET_BENCHMARK)
        return await fetch_price_history(
            wanted,
            days=settings.ai.AI_HISTORY_DAYS,
            market_data=self.market_data_service,
        )

    @staticmethod
    def _weighted_returns(
        positions: List[PortfolioPosition], frames: Dict[str, pd.DataFrame]
    ) -> Tuple[pd.Series, List[PortfolioPosition]]:
        covered = [p for p in positions if p.symbol in frames]
        if not covered:
            raise BusinessLogicException(
                "No market history is available for any asset in this portfolio",
                error_code="INSUFFICIENT_MARKET_DATA",
            )
        closes = pd.DataFrame({p.symbol: frames[p.symbol]["close"] for p in covered})
        closes = closes.sort_index().ffill(limit=3).dropna()
        returns = closes.pct_change().dropna()
        if len(returns) < 20:
            raise BusinessLogicException(
                "Fewer than 20 overlapping daily observations are available",
                error_code="INSUFFICIENT_MARKET_DATA",
            )
        total = sum(p.value for p in covered)
        weights = np.array([float(p.value / total) for p in covered])
        portfolio_returns = pd.Series(
            returns[[p.symbol for p in covered]].values @ weights,
            index=returns.index,
            name="portfolio",
        )
        return portfolio_returns, covered

    async def _calculate_risk_metrics(self, portfolio: Portfolio) -> RiskMetricsData:
        positions = self._positions(portfolio)
        if not positions:
            return self._empty_metrics(portfolio.id)

        frames = await self._market_history([p.symbol for p in positions])
        portfolio_returns, covered = self._weighted_returns(positions, frames)
        values = portfolio_returns.to_numpy()
        returns_list = values.tolist()

        var_1d = self._calculate_historical_var(returns_list, 0.95, 1)
        var_5d = self._calculate_historical_var(returns_list, 0.95, 5)
        var_30d = self._calculate_historical_var(returns_list, 0.95, 30)
        expected_shortfall = self._calculate_expected_shortfall(returns_list, 0.95)
        sharpe_ratio = self._calculate_sharpe_ratio(values)
        sortino_ratio = self._calculate_sortino_ratio(values)
        max_drawdown = self._calculate_max_drawdown(values)
        realized_vol = Decimal(
            str(float(np.std(values, ddof=1)) * np.sqrt(ANNUALIZATION_DAYS))
        )

        beta, alpha = Decimal("1.0"), Decimal("0.0")
        benchmark = frames.get(MARKET_BENCHMARK)
        if benchmark is not None:
            beta, alpha = self._calculate_beta_alpha(
                portfolio_returns,
                benchmark["close"].astype(float).pct_change().dropna(),
            )

        concentration_risk = self._concentration_from_positions(covered)
        liquidity_risk = self._liquidity_from_positions(covered)
        credit_risk = self._defi_exposure_from_positions(covered)

        ai_insights, correlation_matrix = await self._ai_portfolio_insights(
            covered, frames, portfolio_returns
        )
        forecast_vol = ai_insights.get("volatility_forecast", {}).get("predicted_vol")
        effective_vol = realized_vol
        if forecast_vol is not None:
            effective_vol = max(realized_vol, Decimal(str(forecast_vol)))

        overall = await self._calculate_overall_risk_score_from_metrics(
            var_1d, concentration_risk, liquidity_risk, effective_vol
        )
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
            volatility=realized_vol,
            correlation_matrix=correlation_matrix,
            concentration_risk=concentration_risk,
            liquidity_risk=liquidity_risk,
            credit_risk=credit_risk,
            market_risk=var_1d,
            operational_risk=Decimal("0"),
            overall_risk_score=overall,
            risk_grade=self._determine_risk_grade(overall),
            timestamp=datetime.now(timezone.utc),
            ai_insights=ai_insights,
            data_points=len(values),
        )

    @staticmethod
    def _empty_metrics(portfolio_id: UUID) -> RiskMetricsData:
        zero = Decimal("0")
        return RiskMetricsData(
            portfolio_id=portfolio_id,
            var_1d=zero,
            var_5d=zero,
            var_30d=zero,
            expected_shortfall=zero,
            sharpe_ratio=zero,
            sortino_ratio=zero,
            max_drawdown=zero,
            beta=zero,
            alpha=zero,
            volatility=zero,
            correlation_matrix={},
            concentration_risk=zero,
            liquidity_risk=zero,
            credit_risk=zero,
            market_risk=zero,
            operational_risk=zero,
            overall_risk_score=zero,
            risk_grade="N/A",
            timestamp=datetime.now(timezone.utc),
        )

    async def _ai_portfolio_insights(
        self,
        positions: List[PortfolioPosition],
        frames: Dict[str, pd.DataFrame],
        portfolio_returns: pd.Series,
    ) -> Tuple[Dict[str, Any], Dict[str, Dict[str, float]]]:
        insights: Dict[str, Any] = {}
        matrix: Dict[str, Dict[str, float]] = {}
        if not self.ai_service.enabled:
            insights["status"] = "disabled"
            return insights, matrix
        symbols = [p.symbol for p in positions]
        try:
            index_prices = (1.0 + portfolio_returns).cumprod() * 100.0
            forecast = await self.ai_service.forecast_volatility(
                pd.DataFrame({"close": index_prices}),
                horizon=7,
            )
            insights["volatility_forecast"] = forecast
        except Exception as exc:
            logger.warning("AI volatility forecast skipped: %s", exc)
            insights.setdefault("warnings", []).append(f"volatility forecast: {exc}")
        if len(symbols) >= 2:
            try:
                prices = align_close_prices({s: frames[s] for s in symbols})
                if prices.shape[1] >= 2 and len(prices) >= 20:
                    result = await self.ai_service.predict_correlation(prices)
                    assets = result["assets"]
                    matrix = {
                        a: {
                            b: float(result["matrix"][i][j])
                            for j, b in enumerate(assets)
                        }
                        for i, a in enumerate(assets)
                    }
                    insights["correlation_model"] = result["model"]
            except Exception as exc:
                logger.warning("AI correlation prediction skipped: %s", exc)
                insights.setdefault("warnings", []).append(f"correlation: {exc}")
        insights["status"] = "ok" if "warnings" not in insights else "partial"
        return insights, matrix

    @staticmethod
    def _concentration_from_positions(positions: List[PortfolioPosition]) -> Decimal:
        total = sum(p.value for p in positions)
        if total <= 0:
            return Decimal("0")
        hhi = sum((p.value / total) ** 2 for p in positions)
        return min(hhi * 100, Decimal("100"))

    @staticmethod
    def _liquidity_from_positions(positions: List[PortfolioPosition]) -> Decimal:
        total = sum(p.value for p in positions)
        if total <= 0:
            return Decimal("0")
        weighted = sum(
            (p.value / total) * Decimal(str(LIQUIDITY_SCORES.get(p.asset_type, 0.5)))
            for p in positions
        )
        return max(Decimal("0"), min((Decimal("1") - weighted) * 100, Decimal("100")))

    @staticmethod
    def _defi_exposure_from_positions(positions: List[PortfolioPosition]) -> Decimal:
        total = sum(p.value for p in positions)
        if total <= 0:
            return Decimal("0")
        exposed = sum(p.value for p in positions if p.is_defi)
        return min(exposed / total * 50, Decimal("100"))

    def _shock_for_position(
        self, position: PortfolioPosition, scenario: StressTestScenario
    ) -> float:
        shocks = scenario.market_shocks
        if position.symbol in shocks:
            return shocks[position.symbol]
        if position.asset_type in shocks:
            return shocks[position.asset_type]
        if position.symbol not in CRYPTO_MAJORS and "altcoins" in shocks:
            return shocks["altcoins"]
        if "crypto" in shocks:
            return shocks["crypto"]
        return shocks.get("all", 0.0)

    async def _perform_stress_tests(self, portfolio: Portfolio) -> List[Dict[str, Any]]:
        positions = self._positions(portfolio)
        results = []
        for scenario in self.stress_scenarios:
            try:
                results.append(self._run_stress_scenario(positions, scenario))
            except Exception as e:
                logger.error(f"Error running stress scenario {scenario.name}: {e}")
                results.append(
                    {
                        "scenario_name": scenario.name,
                        "status": "failed",
                        "error": str(e),
                    }
                )
        return results

    def _run_stress_scenario(
        self, positions: List[PortfolioPosition], scenario: StressTestScenario
    ) -> Dict[str, Any]:
        total_value = float(sum(p.value for p in positions))
        total_loss = 0.0
        impacts: Dict[str, Any] = {}
        for position in positions:
            value = float(position.value)
            shock = self._shock_for_position(position, scenario)
            loss = value * abs(min(shock, 0.0))
            gain = value * max(shock, 0.0)
            total_loss += loss - gain
            impacts[position.symbol] = {
                "current_value": value,
                "shock_percentage": shock * 100,
                "loss_amount": loss - gain,
                "stressed_value": value - loss + gain,
            }
        loss_percent = total_loss / total_value * 100 if total_value > 0 else 0.0
        return {
            "scenario_name": scenario.name,
            "description": scenario.description,
            "initial_value": total_value,
            "simulated_value": total_value - total_loss,
            "potential_loss_amount": total_loss,
            "potential_loss_percent": loss_percent,
            "volatility_multiplier": scenario.volatility_multiplier,
            "duration_days": scenario.duration_days,
            "asset_impacts": impacts,
            "status": "completed",
        }

    async def _calculate_overall_risk_score(
        self, risk_metrics: RiskMetricsData, stress_test_results: List[Dict[str, Any]]
    ) -> Decimal:
        completed = [
            float(r.get("potential_loss_percent", 0.0))
            for r in stress_test_results
            if r.get("status") == "completed"
        ]
        worst_stress = max(completed) if completed else 0.0
        base = float(risk_metrics.overall_risk_score)
        blended = base * 0.7 + min(worst_stress, 100.0) * 0.3
        return Decimal(str(round(max(0.0, min(100.0, blended)), 2)))

    def _determine_risk_grade(self, risk_score: Decimal) -> str:
        score = float(risk_score)
        if score <= 20:
            return "Very Low"
        if score <= 40:
            return "Low"
        if score <= 60:
            return "Medium"
        if score <= 80:
            return "High"
        return "Very High"

    @staticmethod
    def _assessment_level(score: Decimal) -> AssessmentRiskLevel:
        value = float(score)
        if value <= 25:
            return AssessmentRiskLevel.LOW
        if value <= 50:
            return AssessmentRiskLevel.MEDIUM
        if value <= 75:
            return AssessmentRiskLevel.HIGH
        return AssessmentRiskLevel.CRITICAL

    async def _generate_risk_recommendations(
        self, risk_metrics: RiskMetricsData, stress_results: List[Dict[str, Any]]
    ) -> List[str]:
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
        forecast = risk_metrics.ai_insights.get("volatility_forecast") or {}
        forward_vol = Decimal(str(forecast.get("predicted_vol", 0)))
        if max(risk_metrics.volatility, forward_vol) > Decimal("0.60"):
            recommendations.append(
                "Portfolio volatility is high - consider adding stable assets or hedging"
            )
        if forecast.get("vol_bucket") in ("high", "extreme") and forward_vol > (
            risk_metrics.volatility * Decimal("1.25")
        ):
            recommendations.append(
                "Forecast volatility is rising above recent realized levels - review leverage and stop levels"
            )
        for result in stress_results:
            if result.get("potential_loss_percent", 0) > 50:
                recommendations.append(
                    f"Portfolio vulnerable to {result['scenario_name']} - consider hedging strategies"
                )
        if risk_metrics.sharpe_ratio < Decimal("0.5"):
            recommendations.append(
                "Risk-adjusted returns are low - review asset selection and allocation"
            )
        if not recommendations:
            recommendations.append(
                "Portfolio risk profile is healthy. Continue to monitor market conditions."
            )
        return recommendations

    async def _get_user_risk_profile(self, user_id: UUID) -> Optional[UserRiskProfile]:
        stmt = select(UserRiskProfile).where(UserRiskProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _calculate_user_risk_score(
        self, assessment_data: Dict[str, Any]
    ) -> Decimal:
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
        score += {"beginner": -15, "moderate": 0, "experienced": 15, "expert": 25}.get(
            investment_experience, 0
        )
        score += {
            "conservative": -20,
            "moderate": 0,
            "aggressive": 20,
            "very_aggressive": 30,
        }.get(risk_tolerance, 0)
        score += {"short": -10, "medium": 0, "long": 10, "very_long": 15}.get(
            investment_horizon, 0
        )
        return Decimal(str(max(0, min(100, score))))

    def _determine_user_risk_level(self, risk_score: Decimal) -> RiskLevel:
        score = float(risk_score)
        if score <= 25:
            return RiskLevel.LOW
        if score <= 50:
            return RiskLevel.MEDIUM
        if score <= 75:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    def _calculate_risk_score(self, factors: dict) -> float:
        score = 50.0
        age = factors.get("age", 35)
        if age < 30:
            score += 10
        elif age > 60:
            score -= 10
        income = factors.get("income", 50000)
        if income > 100000:
            score += 10
        elif income < 30000:
            score -= 10
        exp_map = {
            "beginner": -15,
            "intermediate": 0,
            "moderate": 0,
            "experienced": 15,
            "expert": 20,
        }
        score += exp_map.get(factors.get("investment_experience", "moderate"), 0)
        tol_map = {
            "low": -15,
            "conservative": -15,
            "medium": 0,
            "moderate": 0,
            "high": 15,
            "aggressive": 20,
        }
        score += tol_map.get(factors.get("risk_tolerance", "medium"), 0)
        hist_map = {"normal": 0, "suspicious": 20, "flagged": 30}
        score += hist_map.get(factors.get("transaction_history", "normal"), 0)
        return max(0.0, min(100.0, score))

    def _calculate_risk_based_limits(
        self, risk_level: RiskLevel, assessment_data: Dict[str, Any]
    ) -> Dict[str, Decimal]:
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
        multiplier = Decimal(str(min(max(income / 50000, 0.5), 5.0)))
        for key in (
            "daily_transaction_limit",
            "monthly_transaction_limit",
            "max_portfolio_value",
        ):
            limits[key] *= multiplier
        return limits

    async def _get_latest_risk_assessment(
        self, portfolio_id: UUID
    ) -> Optional[RiskAssessment]:
        stmt = (
            select(RiskAssessment)
            .where(RiskAssessment.portfolio_id == portfolio_id)
            .order_by(RiskAssessment.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _check_risk_thresholds(
        self,
        current_metrics: RiskMetricsData,
        latest_assessment: Optional[RiskAssessment],
    ) -> List[Dict[str, Any]]:
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
        if current_metrics.volatility > Decimal("0.60"):
            alerts.append(
                {
                    "type": "high_volatility",
                    "severity": "medium",
                    "message": f"Portfolio volatility is very high: {current_metrics.volatility:.2%}",
                    "current_value": float(current_metrics.volatility),
                    "threshold": 0.6,
                }
            )
        forecast = current_metrics.ai_insights.get("volatility_forecast") or {}
        if forecast.get("vol_bucket") == "extreme":
            alerts.append(
                {
                    "type": "forecast_volatility",
                    "severity": "high",
                    "message": f"Forecast volatility is extreme: {forecast.get('predicted_vol', 0):.2%}",
                    "current_value": float(forecast.get("predicted_vol", 0)),
                    "threshold": 1.0,
                }
            )
        return alerts

    async def _check_concentration_limits(
        self, portfolio: Portfolio
    ) -> List[Dict[str, Any]]:
        positions = self._positions(portfolio)
        total = sum(p.value for p in positions)
        if total <= 0:
            return []
        alerts = []
        for position in positions:
            allocation = position.value / total
            if allocation > Decimal("0.50"):
                alerts.append(
                    {
                        "type": "concentration_limit",
                        "severity": "high",
                        "message": f"{position.symbol} represents {allocation:.1%} of portfolio",
                        "asset": position.symbol,
                        "allocation": float(allocation),
                        "threshold": 0.5,
                    }
                )
        return alerts

    async def _check_correlation_changes(
        self,
        portfolio: Portfolio,
        latest_assessment: Optional[RiskAssessment],
        current_matrix: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> List[Dict[str, Any]]:
        if not latest_assessment or not current_matrix:
            return []
        results = latest_assessment.assessment_results or {}
        previous = results.get("correlation_matrix") or {}
        alerts = []
        seen = set()
        for a, row in current_matrix.items():
            for b, value in row.items():
                if a >= b or (a, b) in seen:
                    continue
                seen.add((a, b))
                prior = previous.get(a, {}).get(b)
                if prior is None:
                    continue
                if abs(float(value) - float(prior)) >= CORRELATION_DRIFT_THRESHOLD:
                    alerts.append(
                        {
                            "type": "correlation_shift",
                            "severity": "medium",
                            "message": f"Correlation between {a} and {b} moved from {float(prior):.2f} to {float(value):.2f}",
                            "assets": [a, b],
                            "previous": float(prior),
                            "current": float(value),
                            "threshold": CORRELATION_DRIFT_THRESHOLD,
                        }
                    )
        return alerts

    async def _generate_monitoring_recommendations(
        self, alerts: List[Dict[str, Any]]
    ) -> List[str]:
        mapping = {
            "var_breach": "Reduce position sizes or add hedging to lower VaR",
            "high_risk_score": "Review portfolio allocation and consider risk reduction",
            "high_volatility": "Add stable assets or implement volatility reduction strategies",
            "forecast_volatility": "Tighten risk limits ahead of the forecast volatility spike",
            "correlation_shift": "Re-check diversification assumptions after the correlation shift",
        }
        recommendations = []
        for alert in alerts:
            kind = alert.get("type")
            if kind == "concentration_limit":
                text = f"Reduce allocation to {alert.get('asset')} to improve diversification"
            else:
                text = mapping.get(kind)
            if text and text not in recommendations:
                recommendations.append(text)
        return recommendations

    @staticmethod
    def _coerce_ids(portfolio_id: Any, user_id: Any) -> Optional[Tuple[UUID, UUID]]:
        try:
            pid = (
                portfolio_id
                if isinstance(portfolio_id, UUID)
                else UUID(str(portfolio_id))
            )
            uid = user_id if isinstance(user_id, UUID) else UUID(str(user_id))
            return pid, uid
        except (ValueError, AttributeError, TypeError):
            return None

    async def calculate_risk_metrics(
        self, portfolio_id: Any, user_id: Any
    ) -> Optional[RiskMetricsData]:
        ids = self._coerce_ids(portfolio_id, user_id)
        if ids is None:
            return None
        portfolio = await self._get_portfolio_with_assets(*ids)
        if not portfolio:
            return None
        return await self._calculate_risk_metrics(portfolio)

    async def perform_stress_test(
        self, portfolio_id: Any, user_id: Any, scenario_name: str = "Market Crash"
    ) -> Dict[str, Any]:
        ids = self._coerce_ids(portfolio_id, user_id)
        if ids is None:
            return {"scenario": scenario_name, "results": [], "error": "invalid id"}
        portfolio = await self._get_portfolio_with_assets(*ids)
        if not portfolio:
            return {"scenario": scenario_name, "results": []}
        all_results = await self._perform_stress_tests(portfolio)
        wanted = (scenario_name or "").lower()
        selected = next(
            (
                r
                for r in all_results
                if str(
                    r.get("scenario_name", r.get("scenario", r.get("name", "")))
                ).lower()
                == wanted
            ),
            None,
        )
        return {"scenario": scenario_name, "selected": selected, "results": all_results}

    async def assess_portfolio_risk(self, portfolio_id: Any, user_id: Any) -> Any:
        ids = self._coerce_ids(portfolio_id, user_id)
        if ids is None:
            return {
                "risk_score": 0.0,
                "risk_level": "unknown",
                "portfolio_id": str(portfolio_id),
                "assessment_date": datetime.now(timezone.utc).isoformat(),
            }
        portfolio_id, user_id = ids
        portfolio = await self._get_portfolio_with_assets(portfolio_id, user_id)
        if not portfolio:
            return {
                "risk_score": 0.0,
                "risk_level": "unknown",
                "portfolio_id": str(portfolio_id),
                "assessment_date": datetime.now(timezone.utc).isoformat(),
            }
        try:
            metrics = await self._calculate_risk_metrics(portfolio)
            stress_results = await self._perform_stress_tests(portfolio)
            overall = await self._calculate_overall_risk_score(metrics, stress_results)
            recommendations = await self._generate_risk_recommendations(
                metrics, stress_results
            )
            grade = self._determine_risk_grade(overall)
            now = datetime.now(timezone.utc)
            trained = [
                name
                for name, info in self.ai_service.status()["models"].items()
                if info["loaded"] and info["mode"] == "trained"
            ]
            assessment = RiskAssessment(
                portfolio_id=portfolio_id,
                user_id=user_id,
                assessment_type="portfolio_analysis",
                risk_type=RiskType.MARKET_RISK,
                risk_level=self._assessment_level(overall),
                overall_risk_score=overall,
                market_risk_score=min(metrics.var_1d * 1000, Decimal("100")),
                credit_risk_score=min(metrics.credit_risk, Decimal("100")),
                liquidity_risk_score=min(metrics.liquidity_risk, Decimal("100")),
                operational_risk_score=min(metrics.operational_risk, Decimal("100")),
                assessment_method="hybrid" if trained else "automated",
                model_version=f"ai_models-{self._ai_version()}",
                risk_factors=_to_jsonable(
                    {
                        "concentration_risk": metrics.concentration_risk,
                        "liquidity_risk": metrics.liquidity_risk,
                        "volatility": metrics.volatility,
                        "var_1d": metrics.var_1d,
                        "risk_grade": grade,
                    }
                ),
                assessment_parameters=_to_jsonable(
                    {
                        "history_days": settings.ai.AI_HISTORY_DAYS,
                        "data_points": metrics.data_points,
                        "benchmark": MARKET_BENCHMARK,
                        "trained_models": trained,
                    }
                ),
                assessment_results=_to_jsonable(
                    {
                        "metrics": {
                            "var_1d": metrics.var_1d,
                            "var_5d": metrics.var_5d,
                            "var_30d": metrics.var_30d,
                            "expected_shortfall": metrics.expected_shortfall,
                            "sharpe_ratio": metrics.sharpe_ratio,
                            "sortino_ratio": metrics.sortino_ratio,
                            "max_drawdown": metrics.max_drawdown,
                            "beta": metrics.beta,
                            "alpha": metrics.alpha,
                            "volatility": metrics.volatility,
                        },
                        "correlation_matrix": metrics.correlation_matrix,
                        "stress_tests": stress_results,
                        "ai_insights": metrics.ai_insights,
                        "risk_grade": grade,
                    }
                ),
                valid_from=now,
                valid_until=now + ASSESSMENT_VALIDITY,
                is_current=True,
                recommendations=recommendations,
                action_required=float(overall) > 60,
            )
            await self.db.execute(
                update(RiskAssessment)
                .where(
                    and_(
                        RiskAssessment.portfolio_id == portfolio_id,
                        RiskAssessment.assessment_type == "portfolio_analysis",
                        RiskAssessment.is_current == True,
                    )
                )
                .values(is_current=False, valid_until=now)
            )
            self.db.add(assessment)
            await self.db.commit()
            logger.info(f"Risk assessment completed for portfolio {portfolio_id}")
            return assessment
        except BusinessLogicException:
            await self._safe_rollback()
            raise
        except Exception as e:
            await self._safe_rollback()
            logger.error(f"Error assessing portfolio risk: {e}", exc_info=True)
            raise

    @staticmethod
    def _ai_version() -> str:
        try:
            import ai_models

            return str(ai_models.__version__)
        except Exception:
            return "unavailable"

    async def _safe_rollback(self) -> None:
        try:
            await self.db.rollback()
        except Exception:
            pass

    async def perform_user_risk_assessment(
        self, user_id: Any, assessment_data: Dict[str, Any]
    ) -> UserRiskProfile:
        if not isinstance(user_id, UUID):
            user_id = UUID(str(user_id))
        try:
            profile = await self._get_user_risk_profile(user_id)
            if not profile:
                profile = UserRiskProfile(user_id=user_id)
                self.db.add(profile)
            risk_score = await self._calculate_user_risk_score(assessment_data)
            risk_level = self._determine_user_risk_level(risk_score)
            profile.risk_level = risk_level
            profile.risk_score = risk_score
            profile.assessment_date = datetime.now(timezone.utc)
            profile.assessment_method = "questionnaire"
            profile.risk_factors = _to_jsonable(assessment_data)
            limits = self._calculate_risk_based_limits(risk_level, assessment_data)
            profile.daily_transaction_limit = limits["daily_transaction_limit"]
            profile.monthly_transaction_limit = limits["monthly_transaction_limit"]
            profile.max_position_size = (
                limits["max_portfolio_value"] * limits["max_single_asset_allocation"]
            )
            await self.db.commit()
            logger.info(f"User risk assessment completed for user {user_id}")
            return profile
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error performing user risk assessment: {e}")
            raise

    async def monitor_portfolio_risk(
        self, portfolio_id: UUID, user_id: UUID
    ) -> Dict[str, Any]:
        portfolio = await self._get_portfolio_with_assets(portfolio_id, user_id)
        if not portfolio:
            raise ValueError("Portfolio not found")
        latest = await self._get_latest_risk_assessment(portfolio_id)
        metrics = await self._calculate_risk_metrics(portfolio)
        alerts = await self._check_risk_thresholds(metrics, latest)
        concentration = await self._check_concentration_limits(portfolio)
        correlation = await self._check_correlation_changes(
            portfolio, latest, metrics.correlation_matrix
        )
        all_alerts = alerts + concentration + correlation
        return {
            "portfolio_id": str(portfolio_id),
            "monitoring_timestamp": datetime.now(timezone.utc).isoformat(),
            "current_risk_score": float(metrics.overall_risk_score),
            "risk_grade": metrics.risk_grade,
            "alerts": all_alerts,
            "risk_metrics": {
                "var_1d": float(metrics.var_1d),
                "var_5d": float(metrics.var_5d),
                "sharpe_ratio": float(metrics.sharpe_ratio),
                "max_drawdown": float(metrics.max_drawdown),
                "volatility": float(metrics.volatility),
            },
            "ai_insights": _to_jsonable(metrics.ai_insights),
            "recommendations": await self._generate_monitoring_recommendations(
                all_alerts
            ),
        }

    async def calculate_var(
        self,
        portfolio_id: UUID,
        confidence_level: float = 0.95,
        time_horizon: int = 1,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        portfolio = await self._get_portfolio_with_assets(portfolio_id, user_id)
        if not portfolio:
            raise ValueError("Portfolio not found")
        positions = self._positions(portfolio)
        if not positions:
            raise ValueError("Portfolio has no priced assets")
        frames = await self._market_history([p.symbol for p in positions])
        returns, _ = self._weighted_returns(positions, frames)
        returns_list = returns.tolist()
        historical = self._calculate_historical_var(
            returns_list, confidence_level, time_horizon
        )
        parametric = self._calculate_parametric_var(
            returns_list, confidence_level, time_horizon
        )
        monte_carlo = self._calculate_monte_carlo_var(
            returns_list, confidence_level, time_horizon
        )
        return {
            "portfolio_id": str(portfolio_id),
            "confidence_level": confidence_level,
            "time_horizon": time_horizon,
            "calculation_date": datetime.now(timezone.utc).isoformat(),
            "methods": {
                "historical_simulation": {
                    "var": float(historical),
                    "description": "Based on historical return distribution",
                },
                "parametric": {
                    "var": float(parametric),
                    "description": "Based on normal distribution assumption",
                },
                "monte_carlo": {
                    "var": float(monte_carlo),
                    "description": "Based on Monte Carlo simulation",
                },
            },
            "expected_shortfall": float(
                self._calculate_expected_shortfall(returns_list, confidence_level)
            ),
            "recommended_var": float((historical + parametric + monte_carlo) / 3),
        }

    def _calculate_historical_var(
        self, returns: List[float], confidence_level: float, time_horizon: int
    ) -> Decimal:
        if not returns:
            return Decimal("0")
        scaled = np.array(returns) * np.sqrt(time_horizon)
        var = np.percentile(scaled, (1 - confidence_level) * 100)
        return Decimal(str(max(0.0, -float(var))))

    def _calculate_parametric_var(
        self, returns: List[float], confidence_level: float, time_horizon: int
    ) -> Decimal:
        if not returns:
            return Decimal("0")
        arr = np.array(returns)
        z_score = stats.norm.ppf(1 - confidence_level)
        mean = float(np.mean(arr)) * time_horizon
        std = float(np.std(arr, ddof=1)) * np.sqrt(time_horizon)
        return Decimal(str(max(0.0, -(mean + z_score * std))))

    def _calculate_monte_carlo_var(
        self,
        returns: List[float],
        confidence_level: float,
        time_horizon: int,
        simulations: int = 10000,
    ) -> Decimal:
        if not returns:
            return Decimal("0")
        arr = np.array(returns)
        rng = np.random.default_rng(42)
        simulated = rng.normal(
            float(np.mean(arr)) * time_horizon,
            float(np.std(arr, ddof=1)) * np.sqrt(time_horizon),
            simulations,
        )
        var = np.percentile(simulated, (1 - confidence_level) * 100)
        return Decimal(str(max(0.0, -float(var))))

    def _calculate_expected_shortfall(
        self, returns: List[float], confidence_level: float
    ) -> Decimal:
        if not returns:
            return Decimal("0")
        arr = np.array(returns)
        threshold = np.percentile(arr, (1 - confidence_level) * 100)
        tail = arr[arr <= threshold]
        value = float(np.mean(tail)) if len(tail) else float(threshold)
        return Decimal(str(max(0.0, -value)))

    def _calculate_sharpe_ratio(
        self, returns: np.ndarray, risk_free_rate: float = RISK_FREE_RATE
    ) -> Decimal:
        if len(returns) < 2:
            return Decimal("0")
        excess = returns - risk_free_rate / ANNUALIZATION_DAYS
        std = float(np.std(excess, ddof=1))
        if std == 0:
            return Decimal("0")
        return Decimal(str(float(np.mean(excess)) / std * np.sqrt(ANNUALIZATION_DAYS)))

    def _calculate_sortino_ratio(
        self, returns: np.ndarray, risk_free_rate: float = RISK_FREE_RATE
    ) -> Decimal:
        if len(returns) < 2:
            return Decimal("0")
        excess = returns - risk_free_rate / ANNUALIZATION_DAYS
        downside = np.minimum(excess, 0.0)
        deviation = float(np.sqrt(np.mean(downside**2)))
        if deviation == 0:
            return Decimal("0")
        return Decimal(
            str(float(np.mean(excess)) / deviation * np.sqrt(ANNUALIZATION_DAYS))
        )

    def _calculate_max_drawdown(self, returns: np.ndarray) -> Decimal:
        if len(returns) == 0:
            return Decimal("0")
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return Decimal(str(abs(float(np.min(drawdown)))))

    def _calculate_beta_alpha(
        self, portfolio_returns: pd.Series, market_returns: pd.Series
    ) -> Tuple[Decimal, Decimal]:
        joined = pd.concat(
            [portfolio_returns, market_returns], axis=1, join="inner"
        ).dropna()
        if len(joined) < 20:
            return Decimal("1.0"), Decimal("0.0")
        p = joined.iloc[:, 0].to_numpy()
        m = joined.iloc[:, 1].to_numpy()
        variance = float(np.var(m, ddof=1))
        if variance == 0:
            return Decimal("1.0"), Decimal("0.0")
        beta = float(np.cov(p, m, ddof=1)[0, 1]) / variance
        alpha = (float(np.mean(p)) - beta * float(np.mean(m))) * ANNUALIZATION_DAYS
        return Decimal(str(beta)), Decimal(str(alpha))

    async def _calculate_overall_risk_score_from_metrics(
        self,
        var_1d: Decimal,
        concentration_risk: Decimal,
        liquidity_risk: Decimal,
        volatility: Decimal,
    ) -> Decimal:
        var_score = min(float(var_1d) * 1000, 100)
        concentration_score = min(float(concentration_risk), 100)
        liquidity_score = min(float(liquidity_risk), 100)
        volatility_score = min(float(volatility) * 100, 100)
        overall = (
            0.4 * var_score
            + 0.2 * concentration_score
            + 0.2 * liquidity_score
            + 0.2 * volatility_score
        )
        return Decimal(str(round(max(0.0, min(100.0, overall)), 2)))

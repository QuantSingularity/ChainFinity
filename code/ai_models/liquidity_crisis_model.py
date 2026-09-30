"""
Liquidity Crisis Alert System
Early-warning system for DeFi liquidity crises using a multi-signal
ensemble approach:
  1. TVL Velocity Monitor  - detects rapid TVL drain (bank-run signature)
  2. Bid-Ask Spread Model  - widens before illiquidity events
  3. Depeg Detector        - stablecoin / LST depeg probability
  4. Contagion Scorer      - cross-protocol correlation spike detection
  5. Ensemble aggregator   - weighted combination with configurable weights
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Alert dataclass
# ---------------------------------------------------------------------------


@dataclass
class LiquidityAlert:
    timestamp: str
    protocol_id: str
    overall_risk: float  # 0-1
    tvl_velocity_score: float
    spread_score: float
    depeg_score: float
    contagion_score: float
    alert_level: str  # watch / warning / critical
    recommended_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "protocol": self.protocol_id,
            "overall_risk": round(self.overall_risk, 4),
            "component_scores": {
                "tvl_velocity": round(self.tvl_velocity_score, 4),
                "spread": round(self.spread_score, 4),
                "depeg": round(self.depeg_score, 4),
                "contagion": round(self.contagion_score, 4),
            },
            "alert_level": self.alert_level,
            "recommended_actions": self.recommended_actions,
        }


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class TVLVelocityMonitor:
    """
    Flags rapid TVL outflows using z-score of rolling percentage change.
    A bank-run typically shows a 20–60% TVL drain within 24–48 hours.
    """

    def __init__(self, window: int = 24, z_threshold: float = 3.0) -> None:
        self.window = window
        self.z_threshold = z_threshold

    def score(self, tvl_series: pd.Series) -> pd.Series:
        """Return risk scores in [0, 1] for each timestep."""
        pct_change = tvl_series.pct_change()
        roll_mean = pct_change.rolling(self.window, min_periods=1).mean()
        roll_std = pct_change.rolling(self.window, min_periods=1).std().replace(0, 1e-9)
        z = (pct_change - roll_mean) / roll_std
        # Negative z = outflow; large magnitude = crisis signal
        risk = np.clip(-z / self.z_threshold, 0, 1)
        return risk.fillna(0.0)


class SpreadModel:
    """
    Estimates illiquidity risk from bid-ask spread widening.
    Uses exponential smoothing to detect sustained spread elevation.
    """

    def __init__(self, ema_span: int = 12, baseline_window: int = 168) -> None:
        self.ema_span = ema_span
        self.baseline_window = baseline_window

    def score(self, spread_series: pd.Series) -> pd.Series:
        """
        Returns risk score in [0, 1].
        spread_series should be fractional (e.g. 0.002 = 0.2%).
        """
        ema_spread = spread_series.ewm(span=self.ema_span, adjust=False).mean()
        baseline = spread_series.rolling(self.baseline_window, min_periods=1).median()
        ratio = (ema_spread / baseline.replace(0, 1e-9)).clip(0, 10)
        # Normalise: ratio of 1 = normal, ratio ≥ 5 = crisis
        risk = np.clip((ratio - 1) / 4, 0, 1)
        return risk.fillna(0.0)


class DepegDetector:
    """
    Detects stablecoin / liquid-staking token depeg using:
      - Absolute deviation from peg
      - Rate of change of deviation
      - Duration above threshold
    """

    def __init__(self, peg_value: float = 1.0, warning_band: float = 0.005) -> None:
        self.peg_value = peg_value
        self.warning_band = warning_band  # 0.5% = normal band

    def score(self, price_series: pd.Series) -> pd.Series:
        """Returns depeg risk score in [0, 1]."""
        deviation = (price_series - self.peg_value).abs()
        # Normalise: warning_band → 0, 10× warning_band → 1
        risk = np.clip(deviation / (10 * self.warning_band), 0, 1)
        # Weight by rate of change - fast depeg is worse
        rate_of_change = deviation.diff().abs().fillna(0)
        roc_weight = np.clip(rate_of_change / self.warning_band, 0, 1)
        combined = 0.7 * risk + 0.3 * roc_weight
        return combined.fillna(0.0)


class ContagionScorer:
    """
    Detects cross-protocol correlation spikes that precede contagion events.
    A sudden jump in rolling pairwise correlation indicates systemic risk.
    """

    def __init__(self, window: int = 24, spike_threshold: float = 0.3) -> None:
        self.window = window
        self.spike_threshold = spike_threshold

    def score(self, returns_df: pd.DataFrame) -> pd.Series:
        """
        Parameters
        ----------
        returns_df : DataFrame of per-timestep returns for multiple protocols
                     (columns = protocol IDs, rows = timesteps).

        Returns
        -------
        pd.Series of contagion risk scores aligned to returns_df.index.
        """
        if returns_df.shape[1] < 2:
            return pd.Series(0.0, index=returns_df.index)

        avg_corrs = []
        for i in range(len(returns_df)):
            start = max(0, i - self.window + 1)
            window_data = returns_df.iloc[start : i + 1]
            if len(window_data) < 3:
                avg_corrs.append(0.0)
                continue
            corr_matrix = window_data.corr()
            # Upper triangle only (exclude diagonal)
            upper = corr_matrix.where(
                np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
            )
            avg_corr = upper.stack().mean()
            avg_corrs.append(float(avg_corr) if not np.isnan(avg_corr) else 0.0)

        corr_series = pd.Series(avg_corrs, index=returns_df.index)
        # Detect spikes vs rolling baseline
        baseline = corr_series.rolling(self.window * 4, min_periods=1).mean()
        spike = (corr_series - baseline).clip(0)
        risk = np.clip(spike / self.spike_threshold, 0, 1)
        return risk.fillna(0.0)


# ---------------------------------------------------------------------------
# Ensemble
# ---------------------------------------------------------------------------


class LiquidityCrisisDetector:
    """
    Ensemble early-warning system combining all four sub-models.

    Alert levels:
        watch    : overall_risk in [0.30, 0.55)
        warning  : overall_risk in [0.55, 0.75)
        critical : overall_risk ≥ 0.75
    """

    ALERT_LEVELS = [
        ("critical", 0.75),
        ("warning", 0.55),
        ("watch", 0.30),
        ("normal", 0.0),
    ]

    RECOMMENDED_ACTIONS: Dict[str, List[str]] = {
        "critical": [
            "Immediately reduce exposure to affected protocol",
            "Move assets to audited stable vault",
            "Enable automated liquidation protection",
            "Notify risk management team",
        ],
        "warning": [
            "Reduce position size by 50%",
            "Set tighter stop-loss thresholds",
            "Monitor on-chain TVL every 15 minutes",
        ],
        "watch": [
            "Increase monitoring frequency",
            "Review collateral ratios",
        ],
        "normal": [],
    }

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        tvl_window: int = 24,
        spread_ema: int = 12,
        peg_value: float = 1.0,
        corr_window: int = 24,
    ) -> None:
        default_weights = {
            "tvl_velocity": 0.35,
            "spread": 0.25,
            "depeg": 0.25,
            "contagion": 0.15,
        }
        self.weights = weights or default_weights
        if abs(sum(self.weights.values()) - 1.0) > 1e-6:
            raise ValueError("Weights must sum to 1.0")

        self.tvl_monitor = TVLVelocityMonitor(window=tvl_window)
        self.spread_model = SpreadModel(ema_span=spread_ema)
        self.depeg_detector = DepegDetector(peg_value=peg_value)
        self.contagion_scorer = ContagionScorer(window=corr_window)

    @staticmethod
    def _classify(score: float, levels: List[Tuple[str, float]]) -> str:
        for label, threshold in levels:
            if score >= threshold:
                return label
        return "normal"

    def analyze(
        self,
        tvl_series: pd.Series,
        spread_series: Optional[pd.Series] = None,
        price_series: Optional[pd.Series] = None,
        protocol_returns: Optional[pd.DataFrame] = None,
        protocol_id: str = "unknown",
    ) -> pd.DataFrame:
        """
        Run all sub-models and return a per-timestep risk DataFrame.

        Required: tvl_series (index = timestamp, values = USD TVL).
        Optional: spread_series, price_series, protocol_returns.
        """
        idx = tvl_series.index

        tvl_scores = self.tvl_monitor.score(tvl_series)

        spread_scores = (
            self.spread_model.score(spread_series.reindex(idx).ffill())
            if spread_series is not None
            else pd.Series(0.0, index=idx)
        )

        depeg_scores = (
            self.depeg_detector.score(price_series.reindex(idx).ffill())
            if price_series is not None
            else pd.Series(0.0, index=idx)
        )

        contagion_scores = (
            self.contagion_scorer.score(protocol_returns.reindex(idx).fillna(0))
            if protocol_returns is not None
            else pd.Series(0.0, index=idx)
        )

        w = self.weights
        overall = (
            w["tvl_velocity"] * tvl_scores
            + w["spread"] * spread_scores
            + w["depeg"] * depeg_scores
            + w["contagion"] * contagion_scores
        )

        result = pd.DataFrame(
            {
                "protocol_id": protocol_id,
                "overall_risk": overall.clip(0, 1),
                "tvl_velocity_score": tvl_scores,
                "spread_score": spread_scores,
                "depeg_score": depeg_scores,
                "contagion_score": contagion_scores,
            },
            index=idx,
        )
        result["alert_level"] = result["overall_risk"].apply(
            lambda s: self._classify(s, self.ALERT_LEVELS)
        )
        return result

    def get_alerts(
        self,
        tvl_series: pd.Series,
        spread_series: Optional[pd.Series] = None,
        price_series: Optional[pd.Series] = None,
        protocol_returns: Optional[pd.DataFrame] = None,
        protocol_id: str = "unknown",
        min_level: str = "watch",
    ) -> List[LiquidityAlert]:
        """
        Return LiquidityAlert objects for timesteps at or above `min_level`.
        """
        level_order = {"watch": 0, "warning": 1, "critical": 2}
        min_order = level_order.get(min_level, 0)

        df = self.analyze(
            tvl_series, spread_series, price_series, protocol_returns, protocol_id
        )
        alerts = []
        for ts, row in df[
            df["alert_level"].map(level_order).fillna(-1) >= min_order
        ].iterrows():
            level = str(row["alert_level"])
            alerts.append(
                LiquidityAlert(
                    timestamp=str(ts),
                    protocol_id=protocol_id,
                    overall_risk=float(row["overall_risk"]),
                    tvl_velocity_score=float(row["tvl_velocity_score"]),
                    spread_score=float(row["spread_score"]),
                    depeg_score=float(row["depeg_score"]),
                    contagion_score=float(row["contagion_score"]),
                    alert_level=level,
                    recommended_actions=self.RECOMMENDED_ACTIONS.get(level, []),
                )
            )
        return alerts

    def latest_status(
        self,
        tvl_series: pd.Series,
        spread_series: Optional[pd.Series] = None,
        price_series: Optional[pd.Series] = None,
        protocol_returns: Optional[pd.DataFrame] = None,
        protocol_id: str = "unknown",
    ) -> Dict[str, Any]:
        """Return the risk assessment for the most recent timestep only."""
        df = self.analyze(
            tvl_series, spread_series, price_series, protocol_returns, protocol_id
        )
        last = df.iloc[-1]
        level = str(last["alert_level"])
        return {
            "protocol": protocol_id,
            "timestamp": str(df.index[-1]),
            "overall_risk": round(float(last["overall_risk"]), 4),
            "alert_level": level,
            "component_scores": {
                "tvl_velocity": round(float(last["tvl_velocity_score"]), 4),
                "spread": round(float(last["spread_score"]), 4),
                "depeg": round(float(last["depeg_score"]), 4),
                "contagion": round(float(last["contagion_score"]), 4),
            },
            "recommended_actions": self.RECOMMENDED_ACTIONS.get(level, []),
        }

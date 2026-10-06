import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

EPSILON = 1e-9
WEIGHT_KEYS = ("tvl_velocity", "spread", "depeg", "contagion")


@dataclass
class LiquidityAlert:
    timestamp: str
    protocol_id: str
    overall_risk: float
    tvl_velocity_score: float
    spread_score: float
    depeg_score: float
    contagion_score: float
    alert_level: str
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


def _clean(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype(float)


class TVLVelocityMonitor:
    def __init__(
        self,
        window: int = 24,
        z_threshold: float = 3.0,
        drain_full_scale: float = 0.30,
        drain_gate: float = 0.05,
    ) -> None:
        if window < 2:
            raise ValueError("window must be >= 2")
        self.window = window
        self.z_threshold = z_threshold
        self.drain_full_scale = drain_full_scale
        self.drain_gate = drain_gate

    def score(self, tvl_series: pd.Series) -> pd.Series:
        tvl = _clean(tvl_series)
        pct_change = tvl.pct_change().replace([np.inf, -np.inf], np.nan)
        history = pct_change.shift(1)
        min_periods = max(3, self.window // 4)
        mean = history.rolling(self.window, min_periods=min_periods).mean()
        std = history.rolling(self.window, min_periods=min_periods).std()
        z = (pct_change - mean) / std.where(std > EPSILON)
        z_risk = np.clip(-z / self.z_threshold, 0.0, 1.0)

        peak = tvl.rolling(self.window, min_periods=1).max()
        drawdown = (1.0 - tvl / peak.replace(0, np.nan)).clip(0.0, 1.0)
        drain_risk = np.clip(drawdown / self.drain_full_scale, 0.0, 1.0)
        gate = np.clip(drawdown / self.drain_gate, 0.0, 1.0)

        risk = np.maximum(drain_risk, z_risk * gate)
        return pd.Series(risk, index=tvl.index).fillna(0.0).clip(0.0, 1.0)


class SpreadModel:
    def __init__(self, ema_span: int = 12, baseline_window: int = 168) -> None:
        self.ema_span = ema_span
        self.baseline_window = baseline_window

    def score(self, spread_series: pd.Series) -> pd.Series:
        spread = _clean(spread_series)
        ema_spread = spread.ewm(span=self.ema_span, adjust=False).mean()
        baseline = spread.rolling(self.baseline_window, min_periods=1).median().shift(1)
        baseline = baseline.fillna(spread.iloc[0] if len(spread) else np.nan)
        ratio = (ema_spread / baseline.replace(0, np.nan)).clip(0, 10)
        risk = np.clip((ratio - 1.0) / 4.0, 0.0, 1.0)
        return pd.Series(risk, index=spread.index).fillna(0.0)


class DepegDetector:
    def __init__(self, peg_value: float = 1.0, warning_band: float = 0.005) -> None:
        if peg_value <= 0 or warning_band <= 0:
            raise ValueError("peg_value and warning_band must be positive")
        self.peg_value = peg_value
        self.warning_band = warning_band

    def score(self, price_series: pd.Series) -> pd.Series:
        price = _clean(price_series)
        deviation = (price - self.peg_value).abs() / self.peg_value
        level = np.clip(
            (deviation - self.warning_band) / (9.0 * self.warning_band), 0.0, 1.0
        )
        rate_of_change = np.clip(
            deviation.diff().abs().fillna(0.0) / self.warning_band, 0.0, 1.0
        )
        beyond_band = (deviation > self.warning_band).astype(float)
        combined = 0.7 * level + 0.3 * rate_of_change * beyond_band
        return pd.Series(combined, index=price.index).fillna(0.0).clip(0.0, 1.0)


class ContagionScorer:
    MAX_ASSETS = 25

    def __init__(self, window: int = 24, spike_threshold: float = 0.3) -> None:
        if window < 3:
            raise ValueError("window must be >= 3")
        self.window = window
        self.spike_threshold = spike_threshold

    def score(self, returns_df: pd.DataFrame) -> pd.Series:
        if returns_df.shape[1] < 2:
            return pd.Series(0.0, index=returns_df.index)
        returns = returns_df.apply(pd.to_numeric, errors="coerce")
        if returns.shape[1] > self.MAX_ASSETS:
            keep = returns.var().nlargest(self.MAX_ASSETS).index
            returns = returns[keep]
        columns = list(returns.columns)
        pair_series = [
            returns[columns[i]]
            .rolling(self.window, min_periods=3)
            .corr(returns[columns[j]])
            for i in range(len(columns))
            for j in range(i + 1, len(columns))
        ]
        avg_corr = (
            pd.concat(pair_series, axis=1)
            .replace([np.inf, -np.inf], np.nan)
            .mean(axis=1)
            .fillna(0.0)
        )
        baseline = (
            avg_corr.rolling(self.window * 4, min_periods=1)
            .mean()
            .shift(1)
            .fillna(avg_corr)
        )
        spike = (avg_corr - baseline).clip(lower=0.0)
        risk = np.clip(spike / self.spike_threshold, 0.0, 1.0)
        return pd.Series(risk, index=returns.index).fillna(0.0)


class LiquidityCrisisDetector:
    ALERT_LEVELS = [
        ("critical", 0.75),
        ("warning", 0.55),
        ("watch", 0.30),
        ("normal", 0.0),
    ]

    LEVEL_ORDER = {"normal": -1, "watch": 0, "warning": 1, "critical": 2}

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
        self.weights = dict(weights) if weights else default_weights
        missing = [k for k in WEIGHT_KEYS if k not in self.weights]
        if missing:
            raise ValueError(f"Weights missing required keys: {missing}")
        if any(self.weights[k] < 0 for k in WEIGHT_KEYS):
            raise ValueError("Weights must be non-negative")
        if abs(sum(self.weights[k] for k in WEIGHT_KEYS) - 1.0) > 1e-6:
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
        if len(tvl_series) == 0:
            raise ValueError("tvl_series must not be empty")
        idx = tvl_series.index

        tvl_scores = self.tvl_monitor.score(tvl_series)
        zero = pd.Series(0.0, index=idx)

        spread_scores = (
            self.spread_model.score(spread_series.reindex(idx).ffill().bfill())
            if spread_series is not None and len(spread_series)
            else zero
        )
        depeg_scores = (
            self.depeg_detector.score(price_series.reindex(idx).ffill().bfill())
            if price_series is not None and len(price_series)
            else zero
        )
        contagion_scores = (
            self.contagion_scorer.score(protocol_returns.reindex(idx).fillna(0.0))
            if protocol_returns is not None and protocol_returns.shape[1] >= 2
            else zero
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
        result["alert_level"] = [
            self._classify(s, self.ALERT_LEVELS) for s in result["overall_risk"]
        ]
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
        if min_level not in self.LEVEL_ORDER:
            raise ValueError(f"min_level must be one of {list(self.LEVEL_ORDER)}")
        min_order = self.LEVEL_ORDER[min_level]
        df = self.analyze(
            tvl_series, spread_series, price_series, protocol_returns, protocol_id
        )
        selected = df[df["alert_level"].map(self.LEVEL_ORDER) >= min_order]
        alerts = []
        for ts, row in selected.iterrows():
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
                    recommended_actions=list(self.RECOMMENDED_ACTIONS.get(level, [])),
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
            "recommended_actions": list(self.RECOMMENDED_ACTIONS.get(level, [])),
        }

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from ...core.persistence import load_artifact, save_artifact

logger = logging.getLogger(__name__)

MODEL_TYPE = "smart_money_tracker"
INBOUND_DIRECTIONS = ("buy", "bridge_in")


@dataclass
class WalletProfile:
    address: str
    cluster_id: int
    cluster_label: str
    smart_money_score: float
    pnl_30d: float
    pnl_90d: float
    win_rate: float
    avg_trade_size_usd: float
    chains_active: List[str] = field(default_factory=list)
    top_protocols: List[str] = field(default_factory=list)
    centrality_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "cluster": self.cluster_label,
            "smart_money_score": round(self.smart_money_score, 2),
            "pnl_30d_pct": round(self.pnl_30d, 4),
            "pnl_90d_pct": round(self.pnl_90d, 4),
            "win_rate": round(self.win_rate, 4),
            "avg_trade_size_usd": round(self.avg_trade_size_usd, 2),
            "chains_active": self.chains_active,
            "top_protocols": self.top_protocols,
            "centrality_score": round(self.centrality_score, 4),
        }


@dataclass
class MovementSignal:
    wallet_address: str
    smart_money_score: float
    chain: str
    protocol: str
    direction: str
    amount_usd: float
    token_symbol: str
    timestamp: str
    signal_strength: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wallet": self.wallet_address,
            "score": round(self.smart_money_score, 2),
            "chain": self.chain,
            "protocol": self.protocol,
            "direction": self.direction,
            "amount_usd": round(self.amount_usd, 2),
            "token": self.token_symbol,
            "timestamp": self.timestamp,
            "signal_strength": round(self.signal_strength, 4),
        }


WALLET_FEATURE_COLS = [
    "total_volume_usd_30d",
    "tx_count_30d",
    "unique_protocols_30d",
    "unique_chains",
    "avg_hold_days",
    "pnl_30d_pct",
    "pnl_90d_pct",
    "win_rate",
    "max_single_trade_usd",
    "avg_trade_size_usd",
    "early_entry_ratio",
    "exit_timing_score",
    "bridge_frequency",
    "flash_loan_usage",
]

VOLUME_COLS = ["total_volume_usd_30d", "max_single_trade_usd", "avg_trade_size_usd"]


def engineer_wallet_features(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for col in WALLET_FEATURE_COLS:
        if col in df.columns:
            out[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            out[col] = 0.0
    out = out.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    for col in VOLUME_COLS:
        out[f"log_{col}"] = np.log1p(out[col].clip(lower=0.0))
    return out


def _infer_cluster_label(centroid: np.ndarray, feature_names: List[str]) -> str:
    feat = dict(zip(feature_names, centroid))
    vol = feat.get("log_total_volume_usd_30d", 0)
    win_rate = feat.get("win_rate", 0)
    tx_count = feat.get("tx_count_30d", 0)
    flash = feat.get("flash_loan_usage", 0)
    bridge = feat.get("bridge_frequency", 0)

    if flash > 0.5:
        return "arbitrageur"
    if tx_count > 500 and win_rate < 0.4:
        return "bot"
    if vol > 16:
        return "whale"
    if win_rate > 0.55 and bridge > 0.3:
        return "smart_trader"
    return "retail"


def compute_smart_money_scores(wallets: pd.DataFrame) -> pd.Series:
    feats = engineer_wallet_features(wallets)
    score = (
        (feats["win_rate"] * 40).clip(0, 40)
        + (feats["pnl_90d_pct"] * 20).clip(-20, 20)
        + (feats["early_entry_ratio"] * 20).clip(0, 20)
        + (feats["exit_timing_score"] * 10).clip(0, 10)
        + feats["unique_chains"].clip(0, 5)
        + (feats["unique_protocols_30d"] / 20 * 5).clip(0, 5)
    )
    return score.clip(0, 100)


def compute_wallet_centrality(
    transfers: pd.DataFrame,
    damping: float = 0.85,
    iterations: int = 100,
    tolerance: float = 1e-8,
) -> pd.Series:
    required = {"from_address", "to_address"}
    if not required.issubset(transfers.columns):
        raise ValueError(f"transfers must contain columns: {sorted(required)}")
    if transfers.empty:
        return pd.Series(dtype=float)

    sender = transfers["from_address"].astype(str)
    receiver = transfers["to_address"].astype(str)
    weight = (
        pd.to_numeric(transfers["amount_usd"], errors="coerce")
        .fillna(0.0)
        .clip(lower=0.0)
        if "amount_usd" in transfers.columns
        else pd.Series(1.0, index=transfers.index)
    )
    weight = weight.where(weight > 0, 1.0).to_numpy()

    nodes = pd.Index(
        pd.unique(np.concatenate([sender.to_numpy(), receiver.to_numpy()]))
    )
    n = len(nodes)
    src = nodes.get_indexer(sender)
    dst = nodes.get_indexer(receiver)

    adjacency = sparse.csr_matrix((weight, (src, dst)), shape=(n, n))
    out_strength = np.asarray(adjacency.sum(axis=1)).ravel()
    inverse = np.divide(1.0, out_strength, out=np.zeros(n), where=out_strength > 0)
    transition = sparse.diags(inverse) @ adjacency
    dangling = out_strength == 0

    rank = np.full(n, 1.0 / n)
    for _ in range(iterations):
        spread = transition.T @ rank
        leaked = rank[dangling].sum() / n
        updated = damping * (spread + leaked) + (1.0 - damping) / n
        if np.abs(updated - rank).sum() < tolerance:
            rank = updated
            break
        rank = updated

    peak = rank.max()
    normalised = rank / peak if peak > 0 else rank
    return pd.Series(normalised, index=nodes)


def _as_str_list(value: Any) -> List[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(v) for v in value]
    if isinstance(value, str) and value:
        return [value]
    return []


class SmartMoneyTracker:
    SIGNAL_THRESHOLD: float = 60.0

    def __init__(self, n_clusters: int = 5, random_state: int = 42) -> None:
        if n_clusters < 2:
            raise ValueError("n_clusters must be >= 2")
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.kmeans: Optional[KMeans] = None
        self._cluster_labels: Dict[int, str] = {}
        self._feature_names: List[str] = []
        self._is_fitted = False

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    def fit(self, wallet_df: pd.DataFrame) -> "SmartMoneyTracker":
        if len(wallet_df) < self.n_clusters:
            raise ValueError(
                f"Need at least {self.n_clusters} wallets to fit {self.n_clusters} clusters, "
                f"got {len(wallet_df)}."
            )
        feat_df = engineer_wallet_features(wallet_df)
        self._feature_names = list(feat_df.columns)
        X = self.scaler.fit_transform(feat_df.values)

        self.kmeans = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init=10,
        )
        self.kmeans.fit(X)

        self._cluster_labels = {}
        for cid in range(self.n_clusters):
            centroid_raw = self.scaler.inverse_transform(
                self.kmeans.cluster_centers_[cid].reshape(1, -1)
            )[0]
            self._cluster_labels[cid] = _infer_cluster_label(
                centroid_raw, self._feature_names
            )

        logger.info(
            "SmartMoneyTracker fitted on %d wallets, %d clusters: %s",
            len(wallet_df),
            self.n_clusters,
            self._cluster_labels,
        )
        self._is_fitted = True
        return self

    def _compute_smart_money_score(self, row: pd.Series) -> float:
        return float(compute_smart_money_scores(row.to_frame().T).iloc[0])

    def profile_wallets(
        self,
        wallet_df: pd.DataFrame,
        centrality: Optional[pd.Series] = None,
    ) -> List[WalletProfile]:
        if not self._is_fitted:
            raise RuntimeError("Call fit() before profile_wallets().")

        feat_df = engineer_wallet_features(wallet_df)
        feat_df = feat_df.reindex(columns=self._feature_names, fill_value=0.0)
        cluster_ids = self.kmeans.predict(self.scaler.transform(feat_df.values))
        scores = compute_smart_money_scores(wallet_df).to_numpy()
        addresses = [str(a) for a in wallet_df.index]
        central = (
            centrality.reindex(addresses).fillna(0.0).to_numpy()
            if centrality is not None
            else np.zeros(len(addresses))
        )
        chains = wallet_df["chains_active"] if "chains_active" in wallet_df else None
        protocols = wallet_df["top_protocols"] if "top_protocols" in wallet_df else None

        profiles = []
        for i, address in enumerate(addresses):
            cid = int(cluster_ids[i])
            profiles.append(
                WalletProfile(
                    address=address,
                    cluster_id=cid,
                    cluster_label=self._cluster_labels.get(cid, "unknown"),
                    smart_money_score=float(scores[i]),
                    pnl_30d=float(feat_df["pnl_30d_pct"].iloc[i]),
                    pnl_90d=float(feat_df["pnl_90d_pct"].iloc[i]),
                    win_rate=float(feat_df["win_rate"].iloc[i]),
                    avg_trade_size_usd=float(feat_df["avg_trade_size_usd"].iloc[i]),
                    chains_active=(
                        _as_str_list(chains.iloc[i]) if chains is not None else []
                    ),
                    top_protocols=(
                        _as_str_list(protocols.iloc[i]) if protocols is not None else []
                    ),
                    centrality_score=float(central[i]),
                )
            )
        return profiles

    def get_smart_money_wallets(
        self,
        wallet_df: pd.DataFrame,
        top_n: int = 50,
        centrality: Optional[pd.Series] = None,
    ) -> List[WalletProfile]:
        profiles = self.profile_wallets(wallet_df, centrality=centrality)
        return sorted(profiles, key=lambda p: p.smart_money_score, reverse=True)[:top_n]

    @staticmethod
    def _require_columns(df: pd.DataFrame, columns: List[str]) -> None:
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise ValueError(f"Transaction data is missing required columns: {missing}")

    def generate_signals(
        self,
        tx_df: pd.DataFrame,
        wallet_profiles: List[WalletProfile],
        min_amount_usd: float = 10_000,
    ) -> List[MovementSignal]:
        self._require_columns(tx_df, ["wallet_address", "amount_usd"])
        score_map = {p.address: p.smart_money_score for p in wallet_profiles}

        frame = tx_df.copy()
        frame["_address"] = frame["wallet_address"].astype(str)
        frame["_score"] = frame["_address"].map(score_map).fillna(0.0)
        frame["_amount"] = pd.to_numeric(frame["amount_usd"], errors="coerce").fillna(
            0.0
        )
        selected = frame[
            (frame["_score"] >= self.SIGNAL_THRESHOLD)
            & (frame["_amount"] >= min_amount_usd)
        ]

        def text(row: pd.Series, key: str) -> str:
            value = row.get(key, "")
            return "" if pd.isna(value) else str(value)

        signals = []
        for _, tx in selected.iterrows():
            score = float(tx["_score"])
            amount = float(tx["_amount"])
            strength = (score / 100) * min(np.log1p(amount) / np.log1p(1e7), 1.0)
            signals.append(
                MovementSignal(
                    wallet_address=str(tx["_address"]),
                    smart_money_score=score,
                    chain=text(tx, "chain"),
                    protocol=text(tx, "protocol"),
                    direction=text(tx, "direction"),
                    amount_usd=amount,
                    token_symbol=text(tx, "token_symbol"),
                    timestamp=text(tx, "timestamp"),
                    signal_strength=float(np.clip(strength, 0, 1)),
                )
            )

        signals.sort(key=lambda s: s.signal_strength, reverse=True)
        logger.info("Generated %d smart-money signals.", len(signals))
        return signals

    def cross_chain_flow_summary(
        self,
        tx_df: pd.DataFrame,
        wallet_profiles: List[WalletProfile],
    ) -> pd.DataFrame:
        self._require_columns(
            tx_df, ["wallet_address", "amount_usd", "chain", "token_symbol"]
        )
        empty = pd.DataFrame(columns=["chain", "token", "net_flow_usd", "tx_count"])
        smart_addrs = {
            p.address
            for p in wallet_profiles
            if p.smart_money_score >= self.SIGNAL_THRESHOLD
        }
        smart_txs = tx_df[tx_df["wallet_address"].astype(str).isin(smart_addrs)].copy()
        if smart_txs.empty:
            return empty

        amount = pd.to_numeric(smart_txs["amount_usd"], errors="coerce").fillna(0.0)
        direction = (
            smart_txs["direction"]
            if "direction" in smart_txs.columns
            else pd.Series("", index=smart_txs.index)
        )
        smart_txs["signed_amount"] = np.where(
            direction.isin(INBOUND_DIRECTIONS), amount, -amount
        )
        return (
            smart_txs.groupby(["chain", "token_symbol"])
            .agg(
                net_flow_usd=("signed_amount", "sum"),
                tx_count=("signed_amount", "count"),
            )
            .reset_index()
            .rename(columns={"token_symbol": "token"})
            .sort_values("net_flow_usd", ascending=False)
            .reset_index(drop=True)
        )

    def save(self, directory: Union[str, Path]) -> Path:
        if not self._is_fitted:
            raise RuntimeError("Call fit() before saving.")
        state = {
            "config": {
                "n_clusters": self.n_clusters,
                "random_state": self.random_state,
            },
            "scaler": self.scaler,
            "kmeans": self.kmeans,
            "cluster_labels": self._cluster_labels,
            "feature_names": self._feature_names,
        }
        return save_artifact(directory, MODEL_TYPE, state)

    @classmethod
    def load(cls, directory: Union[str, Path]) -> "SmartMoneyTracker":
        state, _ = load_artifact(directory, MODEL_TYPE)
        instance = cls(**state["config"])
        instance.scaler = state["scaler"]
        instance.kmeans = state["kmeans"]
        instance._cluster_labels = dict(state["cluster_labels"])
        instance._feature_names = list(state["feature_names"])
        instance._is_fitted = True
        return instance

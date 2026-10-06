from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_RECORDS = 20000


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PricePoint(BaseModel):
    model_config = ConfigDict(extra="allow")

    timestamp: datetime
    close: float = Field(gt=0)
    open: Optional[float] = Field(default=None, gt=0)
    high: Optional[float] = Field(default=None, gt=0)
    low: Optional[float] = Field(default=None, gt=0)
    volume: Optional[float] = Field(default=None, ge=0)


class VolatilityRequest(_Strict):
    symbol: Optional[str] = Field(default=None, min_length=1, max_length=20)
    prices: Optional[List[PricePoint]] = Field(default=None, max_length=MAX_RECORDS)
    horizon_days: int = Field(default=7, ge=2, le=90)

    @model_validator(mode="after")
    def require_source(self) -> "VolatilityRequest":
        if not self.symbol and not self.prices:
            raise ValueError("Provide either 'symbol' or 'prices'")
        return self


class VolatilityResponse(BaseModel):
    symbol: Optional[str] = None
    predicted_vol: float
    predicted_vol_std: Optional[float] = None
    confidence_interval: Optional[List[float]] = None
    vol_bucket: str
    confidence: Optional[float] = None
    recent_realized_vol: float
    forecast_horizon_days: int
    model: str


class CorrelationRequest(_Strict):
    symbols: Optional[List[str]] = Field(default=None, min_length=2, max_length=25)
    prices: Optional[Dict[str, List[PricePoint]]] = None

    @model_validator(mode="after")
    def require_source(self) -> "CorrelationRequest":
        if not self.symbols and not self.prices:
            raise ValueError("Provide either 'symbols' or 'prices'")
        if self.prices and not 2 <= len(self.prices) <= 25:
            raise ValueError("'prices' must contain between 2 and 25 assets")
        return self


class CorrelationResponse(BaseModel):
    assets: List[str]
    matrix: List[List[float]]
    model: str


class OnChainObservation(BaseModel):
    model_config = ConfigDict(extra="allow")

    timestamp: datetime


class ExploitRequest(_Strict):
    protocol_id: str = Field(default="unknown", max_length=100)
    threshold: float = Field(default=0.40, ge=0.0, le=1.0)
    observations: List[OnChainObservation] = Field(min_length=1, max_length=MAX_RECORDS)


class ExploitResponse(BaseModel):
    protocol_id: str
    mode: str
    observations: int
    max_risk_score: float
    latest_risk_score: float
    latest_severity: str
    alerts: List[Dict[str, Any]]


class SeriesPoint(BaseModel):
    timestamp: datetime
    value: float


class LiquidityRequest(_Strict):
    protocol_id: str = Field(default="unknown", max_length=100)
    min_level: Literal["watch", "warning", "critical"] = "watch"
    include_alerts: bool = True
    tvl: List[SeriesPoint] = Field(min_length=5, max_length=MAX_RECORDS)
    spread: Optional[List[SeriesPoint]] = Field(default=None, max_length=MAX_RECORDS)
    peg_price: Optional[List[SeriesPoint]] = Field(default=None, max_length=MAX_RECORDS)
    peg_value: float = Field(default=1.0, gt=0)
    protocol_returns: Optional[Dict[str, List[SeriesPoint]]] = None

    @field_validator("protocol_returns")
    @classmethod
    def limit_protocols(
        cls, value: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        if value is not None and len(value) > 25:
            raise ValueError("protocol_returns supports at most 25 protocols")
        return value


class LiquidityResponse(BaseModel):
    status: Dict[str, Any]
    alerts: List[Dict[str, Any]]


class WalletRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    address: str = Field(min_length=1, max_length=128)


class TransactionRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    wallet_address: str = Field(min_length=1, max_length=128)
    amount_usd: float = Field(ge=0)
    chain: str = ""
    protocol: str = ""
    direction: str = ""
    token_symbol: str = ""
    timestamp: Optional[datetime] = None


class TransferRecord(BaseModel):
    from_address: str = Field(min_length=1, max_length=128)
    to_address: str = Field(min_length=1, max_length=128)
    amount_usd: float = Field(default=1.0, ge=0)


class SmartMoneyRequest(_Strict):
    wallets: List[WalletRecord] = Field(min_length=2, max_length=MAX_RECORDS)
    transactions: Optional[List[TransactionRecord]] = Field(
        default=None, max_length=MAX_RECORDS
    )
    transfers: Optional[List[TransferRecord]] = Field(
        default=None, max_length=MAX_RECORDS
    )
    top_n: int = Field(default=50, ge=1, le=500)
    min_amount_usd: float = Field(default=10_000, ge=0)


class SmartMoneyResponse(BaseModel):
    mode: str
    wallets_analyzed: int
    top_wallets: List[Dict[str, Any]]
    signals: List[Dict[str, Any]]
    flows: List[Dict[str, Any]]


class ModelStatus(BaseModel):
    loaded: bool
    mode: str
    fallback: Optional[str] = None
    source: Optional[str] = None
    loaded_at: Optional[str] = None


class AIStatusResponse(BaseModel):
    enabled: bool
    package_available: bool
    tensorflow_available: bool
    models: Dict[str, ModelStatus]


class TrainRequest(_Strict):
    records: List[Dict[str, Any]] = Field(min_length=10, max_length=MAX_RECORDS)
    index_field: Optional[str] = Field(default="timestamp", max_length=50)
    params: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("params")
    @classmethod
    def bounded_params(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        allowed = {
            "epochs",
            "sequence_length",
            "forecast_horizon",
            "target_window",
            "contamination",
            "n_clusters",
            "use_autoencoder",
        }
        unknown = set(value) - allowed
        if unknown:
            raise ValueError(f"Unsupported training parameters: {sorted(unknown)}")
        if "epochs" in value and not 1 <= int(value["epochs"]) <= 200:
            raise ValueError("epochs must be between 1 and 200")
        return value


class TrainingJob(BaseModel):
    job_id: UUID
    model: str
    status: str
    created_at: str
    finished_at: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class ReloadResponse(BaseModel):
    results: Dict[str, str]


class PortfolioAIInsights(BaseModel):
    portfolio_id: UUID
    generated_at: str
    assets: List[str]
    correlation: Optional[CorrelationResponse] = None
    volatility: Dict[str, VolatilityResponse] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)

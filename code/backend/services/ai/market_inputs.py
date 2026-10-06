import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Sequence

import pandas as pd
from config.settings import settings
from exceptions.base_exceptions import ValidationException
from services.market.market_data_service import HistoricalData, MarketDataService

from .ai_service import AIModelsUnavailable

logger = logging.getLogger(__name__)

MAX_CONCURRENT_FETCHES = 5


def normalize_symbol(symbol: str) -> str:
    cleaned = "".join(ch for ch in str(symbol).strip().upper() if ch.isalnum())
    if not cleaned or len(cleaned) > 20:
        raise ValidationException(f"Invalid asset symbol: {symbol!r}")
    return cleaned


def history_to_frame(history: Sequence[HistoricalData]) -> pd.DataFrame:
    if not history:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    frame = pd.DataFrame(
        {
            "open": [float(h.open_price) for h in history],
            "high": [float(h.high_price) for h in history],
            "low": [float(h.low_price) for h in history],
            "close": [float(h.close_price) for h in history],
            "volume": [float(h.volume) for h in history],
        },
        index=pd.DatetimeIndex([h.timestamp for h in history], name="timestamp"),
    )
    frame.index = frame.index.tz_convert("UTC") if frame.index.tz else frame.index
    frame = frame[~frame.index.duplicated(keep="last")].sort_index()
    return frame


async def fetch_price_history(
    symbols: Sequence[str],
    days: Optional[int] = None,
    market_data: Optional[MarketDataService] = None,
) -> Dict[str, pd.DataFrame]:
    window = days or settings.ai.AI_HISTORY_DAYS
    service = market_data or MarketDataService()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=window)
    unique: List[str] = []
    for raw in symbols:
        symbol = normalize_symbol(raw)
        if symbol not in unique:
            unique.append(symbol)
    if len(unique) > settings.ai.AI_MAX_ASSETS:
        raise ValidationException(
            f"At most {settings.ai.AI_MAX_ASSETS} assets are supported per request"
        )
    gate = asyncio.Semaphore(MAX_CONCURRENT_FETCHES)

    async def one(symbol: str) -> pd.DataFrame:
        async with gate:
            history = await service.get_historical_data(symbol, start, end, "1d")
        return history_to_frame(history)

    frames = await asyncio.gather(*(one(s) for s in unique))
    result = dict(zip(unique, frames))
    minimum = settings.ai.AI_MIN_HISTORY_DAYS
    usable = {s: f for s, f in result.items() if len(f) >= minimum}
    if not usable:
        raise AIModelsUnavailable(
            f"Insufficient market history (need at least {minimum} daily rows) "
            f"for: {', '.join(unique)}"
        )
    return usable


def align_close_prices(frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    closes = {
        f"asset_{symbol.lower()}": frame["close"].astype(float)
        for symbol, frame in frames.items()
    }
    combined = pd.DataFrame(closes).sort_index()
    combined = combined.ffill(limit=3).dropna()
    return combined

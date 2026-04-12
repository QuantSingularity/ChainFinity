"""
Market Data Service for Financial Industry Applications
Real-time and historical market data with advanced analytics and caching
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import TracebackType
from typing import Any, Dict, List, Optional

import aiohttp
from config.database import cache
from services.external.price_feeds import PriceFeedAggregator

logger = logging.getLogger(__name__)


@dataclass
class MarketData:
    """Market data structure"""

    symbol: str
    price: Decimal
    volume_24h: Optional[Decimal]
    change_24h: Optional[Decimal]
    change_24h_pct: Optional[Decimal]
    market_cap: Optional[Decimal]
    timestamp: datetime
    source: str


@dataclass
class HistoricalData:
    """Historical price data structure"""

    symbol: str
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal


@dataclass
class TechnicalIndicators:
    """Technical analysis indicators"""

    symbol: str
    timestamp: datetime
    sma_20: Optional[Decimal]
    sma_50: Optional[Decimal]
    sma_200: Optional[Decimal]
    ema_12: Optional[Decimal]
    ema_26: Optional[Decimal]
    rsi: Optional[Decimal]
    macd: Optional[Decimal]
    macd_signal: Optional[Decimal]
    bollinger_upper: Optional[Decimal]
    bollinger_lower: Optional[Decimal]
    volatility: Optional[Decimal]


class MarketDataService:
    """
    Comprehensive market data service with multiple data sources and caching
    """

    def __init__(self) -> None:
        self.price_feed_aggregator = PriceFeedAggregator()
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache_ttl = {
            "current_price": 30,
            "historical_data": 300,
            "market_stats": 60,
            "technical_indicators": 120,
        }

    async def __aenter__(self) -> "MarketDataService":
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            self.session = None

    async def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """
        Get current price for a symbol with caching and fallback sources
        """
        try:
            cache_key = f"price:{symbol}"
            cached_price = await cache.get(cache_key)
            if cached_price:
                return Decimal(cached_price)
            price = await self.price_feed_aggregator.get_price(symbol)
            if price:
                await cache.set(
                    cache_key, str(price), ttl=self.cache_ttl["current_price"]
                )
                return price
            return None
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None

    async def get_multiple_prices(
        self, symbols: List[str]
    ) -> Dict[str, Optional[Decimal]]:
        """
        Get current prices for multiple symbols efficiently
        """
        try:
            tasks = [self.get_current_price(symbol) for symbol in symbols]
            prices = await asyncio.gather(*tasks, return_exceptions=True)
            result = {}
            for symbol, price in zip(symbols, prices):
                if isinstance(price, Exception):
                    logger.error(f"Error getting price for {symbol}: {price}")
                    result[symbol] = None
                else:
                    result[symbol] = price
            return result
        except Exception as e:
            logger.error(f"Error getting multiple prices: {e}")
            return {symbol: None for symbol in symbols}

    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """
        Get comprehensive market data for a symbol
        """
        try:
            cache_key = f"market_data:{symbol}"
            cached_data = await cache.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                return MarketData(
                    symbol=data["symbol"],
                    price=Decimal(data["price"]),
                    volume_24h=(
                        Decimal(data["volume_24h"]) if data["volume_24h"] else None
                    ),
                    change_24h=(
                        Decimal(data["change_24h"]) if data["change_24h"] else None
                    ),
                    change_24h_pct=(
                        Decimal(data["change_24h_pct"])
                        if data["change_24h_pct"]
                        else None
                    ),
                    market_cap=(
                        Decimal(data["market_cap"]) if data["market_cap"] else None
                    ),
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    source=data["source"],
                )
            market_data = await self._fetch_market_data(symbol)
            if market_data:
                cache_data = {
                    "symbol": market_data.symbol,
                    "price": str(market_data.price),
                    "volume_24h": (
                        str(market_data.volume_24h) if market_data.volume_24h else None
                    ),
                    "change_24h": (
                        str(market_data.change_24h) if market_data.change_24h else None
                    ),
                    "change_24h_pct": (
                        str(market_data.change_24h_pct)
                        if market_data.change_24h_pct
                        else None
                    ),
                    "market_cap": (
                        str(market_data.market_cap) if market_data.market_cap else None
                    ),
                    "timestamp": market_data.timestamp.isoformat(),
                    "source": market_data.source,
                }
                await cache.set(
                    cache_key,
                    json.dumps(cache_data),
                    ttl=self.cache_ttl["market_stats"],
                )
                return market_data
            return None
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None

    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> List[HistoricalData]:
        """
        Get historical price data for a symbol
        """
        try:
            cache_key = (
                f"historical:{symbol}:{start_date.date()}:{end_date.date()}:{interval}"
            )
            cached_data = await cache.get(cache_key)
            if cached_data:
                data_list = json.loads(cached_data)
                return [
                    HistoricalData(
                        symbol=data["symbol"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        open_price=Decimal(data["open_price"]),
                        high_price=Decimal(data["high_price"]),
                        low_price=Decimal(data["low_price"]),
                        close_price=Decimal(data["close_price"]),
                        volume=Decimal(data["volume"]),
                    )
                    for data in data_list
                ]
            historical_data = await self._fetch_historical_data(
                symbol, start_date, end_date, interval
            )
            if historical_data:
                cache_data = [
                    {
                        "symbol": data.symbol,
                        "timestamp": data.timestamp.isoformat(),
                        "open_price": str(data.open_price),
                        "high_price": str(data.high_price),
                        "low_price": str(data.low_price),
                        "close_price": str(data.close_price),
                        "volume": str(data.volume),
                    }
                    for data in historical_data
                ]
                await cache.set(
                    cache_key,
                    json.dumps(cache_data),
                    ttl=self.cache_ttl["historical_data"],
                )
                return historical_data
            return []
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return []

    async def get_technical_indicators(
        self, symbol: str
    ) -> Optional[TechnicalIndicators]:
        """
        Calculate and return technical indicators for a symbol
        """
        try:
            cache_key = f"technical:{symbol}"
            cached_data = await cache.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                return TechnicalIndicators(
                    symbol=data["symbol"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    sma_20=Decimal(data["sma_20"]) if data["sma_20"] else None,
                    sma_50=Decimal(data["sma_50"]) if data["sma_50"] else None,
                    sma_200=Decimal(data["sma_200"]) if data["sma_200"] else None,
                    ema_12=Decimal(data["ema_12"]) if data["ema_12"] else None,
                    ema_26=Decimal(data["ema_26"]) if data["ema_26"] else None,
                    rsi=Decimal(data["rsi"]) if data["rsi"] else None,
                    macd=Decimal(data["macd"]) if data["macd"] else None,
                    macd_signal=(
                        Decimal(data["macd_signal"]) if data["macd_signal"] else None
                    ),
                    bollinger_upper=(
                        Decimal(data["bollinger_upper"])
                        if data["bollinger_upper"]
                        else None
                    ),
                    bollinger_lower=(
                        Decimal(data["bollinger_lower"])
                        if data["bollinger_lower"]
                        else None
                    ),
                    volatility=(
                        Decimal(data["volatility"]) if data["volatility"] else None
                    ),
                )
            indicators = await self._calculate_technical_indicators(symbol)
            if indicators:
                cache_data = {
                    "symbol": indicators.symbol,
                    "timestamp": indicators.timestamp.isoformat(),
                    "sma_20": str(indicators.sma_20) if indicators.sma_20 else None,
                    "sma_50": str(indicators.sma_50) if indicators.sma_50 else None,
                    "sma_200": str(indicators.sma_200) if indicators.sma_200 else None,
                    "ema_12": str(indicators.ema_12) if indicators.ema_12 else None,
                    "ema_26": str(indicators.ema_26) if indicators.ema_26 else None,
                    "rsi": str(indicators.rsi) if indicators.rsi else None,
                    "macd": str(indicators.macd) if indicators.macd else None,
                    "macd_signal": (
                        str(indicators.macd_signal) if indicators.macd_signal else None
                    ),
                    "bollinger_upper": (
                        str(indicators.bollinger_upper)
                        if indicators.bollinger_upper
                        else None
                    ),
                    "bollinger_lower": (
                        str(indicators.bollinger_lower)
                        if indicators.bollinger_lower
                        else None
                    ),
                    "volatility": (
                        str(indicators.volatility) if indicators.volatility else None
                    ),
                }
                await cache.set(
                    cache_key,
                    json.dumps(cache_data),
                    ttl=self.cache_ttl["technical_indicators"],
                )
                return indicators
            return None
        except Exception as e:
            logger.error(f"Error getting technical indicators for {symbol}: {e}")
            return None

    async def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol is supported
        """
        try:
            price = await self.get_current_price(symbol)
            return price is not None
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {e}")
            return False

    async def get_market_overview(self) -> Dict[str, Any]:
        """
        Get market overview with key metrics
        """
        try:
            cache_key = "market_overview"
            cached_data = await cache.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            major_symbols = ["BTC", "ETH", "BNB", "ADA", "SOL", "DOT", "MATIC", "LINK"]
            market_data_tasks = [
                self.get_market_data(symbol) for symbol in major_symbols
            ]
            market_data_results = await asyncio.gather(
                *market_data_tasks, return_exceptions=True
            )
            total_market_cap = Decimal("0")
            total_volume = Decimal("0")
            gainers = []
            losers = []
            for symbol, data in zip(major_symbols, market_data_results):
                if isinstance(data, MarketData):
                    if data.market_cap:
                        total_market_cap += data.market_cap
                    if data.volume_24h:
                        total_volume += data.volume_24h
                    if data.change_24h_pct is not None:
                        if data.change_24h_pct > 0:
                            gainers.append(
                                {
                                    "symbol": symbol,
                                    "change_pct": float(data.change_24h_pct),
                                }
                            )
                        else:
                            losers.append(
                                {
                                    "symbol": symbol,
                                    "change_pct": float(data.change_24h_pct),
                                }
                            )
            gainers.sort(key=lambda x: x["change_pct"], reverse=True)
            losers.sort(key=lambda x: x["change_pct"])
            overview = {
                "total_market_cap": float(total_market_cap),
                "total_volume_24h": float(total_volume),
                "top_gainers": gainers[:5],
                "top_losers": losers[:5],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "market_sentiment": self._calculate_market_sentiment(gainers, losers),
            }
            await cache.set(cache_key, json.dumps(overview), ttl=300)
            return overview
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return {}

    async def _fetch_market_data(self, symbol: str) -> Optional[MarketData]:
        """Fetch market data from external API"""
        try:
            return MarketData(
                symbol=symbol,
                price=Decimal("45000.00"),
                volume_24h=Decimal("1000000000"),
                change_24h=Decimal("500.00"),
                change_24h_pct=Decimal("1.12"),
                market_cap=Decimal("850000000000"),
                timestamp=datetime.now(timezone.utc),
                source="mock_api",
            )
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return None

    async def _fetch_historical_data(
        self, symbol: str, start_date: datetime, end_date: datetime, interval: str
    ) -> List[HistoricalData]:
        """Fetch historical data from external API"""
        try:
            data = []
            current_date = start_date
            base_price = Decimal("45000.00")
            while current_date <= end_date:
                open_price = base_price
                high_price = open_price * Decimal("1.02")
                low_price = open_price * Decimal("0.98")
                close_price = open_price * Decimal("1.001")
                volume = Decimal("1000000")
                data.append(
                    HistoricalData(
                        symbol=symbol,
                        timestamp=current_date,
                        open_price=open_price,
                        high_price=high_price,
                        low_price=low_price,
                        close_price=close_price,
                        volume=volume,
                    )
                )
                current_date += timedelta(days=1)
                base_price = close_price
            return data
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return []

    async def _calculate_technical_indicators(
        self, symbol: str
    ) -> Optional[TechnicalIndicators]:
        """Calculate technical indicators from historical data"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=250)
            historical_data = await self.get_historical_data(
                symbol, start_date, end_date
            )
            if len(historical_data) < 20:
                return None
            closes = [data.close_price for data in historical_data]
            indicators = TechnicalIndicators(
                symbol=symbol,
                timestamp=datetime.now(timezone.utc),
                sma_20=self._calculate_sma(closes, 20),
                sma_50=self._calculate_sma(closes, 50),
                sma_200=self._calculate_sma(closes, 200),
                ema_12=self._calculate_ema(closes, 12),
                ema_26=self._calculate_ema(closes, 26),
                rsi=self._calculate_rsi(closes, 14),
                macd=None,
                macd_signal=None,
                bollinger_upper=None,
                bollinger_lower=None,
                volatility=self._calculate_volatility(closes, 30),
            )
            if indicators.ema_12 is not None and indicators.ema_26 is not None:
                indicators.macd = indicators.ema_12 - indicators.ema_26
            sma_20 = indicators.sma_20
            if sma_20 is not None:
                std_dev = self._calculate_std_dev(closes[-20:], sma_20)
                indicators.bollinger_upper = sma_20 + std_dev * 2
                indicators.bollinger_lower = sma_20 - std_dev * 2
            return indicators
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {symbol}: {e}")
            return None

    def _calculate_sma(self, prices: List[Decimal], period: int) -> Optional[Decimal]:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return None
        recent_prices = prices[-period:]
        return sum(recent_prices) / len(recent_prices)

    def _calculate_ema(self, prices: List[Decimal], period: int) -> Optional[Decimal]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        multiplier = Decimal(2) / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = price * multiplier + ema * (1 - multiplier)
        return ema

    def _calculate_rsi(
        self, prices: List[Decimal], period: int = 14
    ) -> Optional[Decimal]:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return None
        gains = []
        losses = []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(Decimal("0"))
            else:
                gains.append(Decimal("0"))
                losses.append(abs(change))
        if len(gains) < period:
            return None
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return Decimal("100")
        rs = avg_gain / avg_loss
        rsi = Decimal("100") - Decimal("100") / (1 + rs)
        return rsi

    def _calculate_volatility(
        self, prices: List[Decimal], period: int
    ) -> Optional[Decimal]:
        """Calculate price volatility (standard deviation of returns)"""
        if len(prices) < period + 1:
            return None
        returns = []
        for i in range(1, len(prices)):
            if prices[i - 1] != 0:
                return_pct = (prices[i] - prices[i - 1]) / prices[i - 1]
                returns.append(return_pct)
        if len(returns) < period:
            return None
        recent_returns = returns[-period:]
        mean_return = sum(recent_returns) / len(recent_returns)
        variance = sum((r - mean_return) ** 2 for r in recent_returns) / len(
            recent_returns
        )
        volatility = variance ** Decimal("0.5")
        return volatility * Decimal("100")

    def _calculate_std_dev(self, prices: List[Decimal], mean: Decimal) -> Decimal:
        """Calculate standard deviation"""
        variance = sum((price - mean) ** 2 for price in prices) / len(prices)
        return variance ** Decimal("0.5")

    def _calculate_market_sentiment(
        self, gainers: List[Dict], losers: List[Dict]
    ) -> str:
        """Calculate overall market sentiment"""
        if len(gainers) > len(losers) * 1.5:
            return "bullish"
        elif len(losers) > len(gainers) * 1.5:
            return "bearish"
        else:
            return "neutral"

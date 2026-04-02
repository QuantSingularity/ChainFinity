"""
Price Feed Aggregator for Multiple Data Sources
Aggregates price data from multiple sources with failover and validation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from types import TracebackType
from typing import Any, Dict, List, Optional

import aiohttp
from config.database import cache
from config.settings import settings

logger = logging.getLogger(__name__)


class PriceFeedAggregator:
    """
    Aggregates price data from multiple sources with failover
    """

    def __init__(self) -> None:
        self.sources = [
            CoinGeckoPriceFeed(),
            CoinMarketCapPriceFeed(),
            BinancePriceFeed(),
            CryptoComparePriceFeed(),
        ]
        self.cache_ttl = 30

    async def get_price(self, symbol: str) -> Optional[Decimal]:
        """
        Get price from multiple sources with failover
        """
        try:
            cache_key = f"aggregated_price:{symbol}"
            cached_price = await cache.get(cache_key)
            if cached_price:
                return Decimal(cached_price)
            prices = []
            for source in self.sources:
                try:
                    price = await source.get_price(symbol)
                    if price and price > 0:
                        prices.append(price)
                except Exception as e:
                    logger.warning(
                        f"Error getting price from {source.__class__.__name__}: {e}"
                    )
                    continue
            if not prices:
                return None
            prices.sort()
            if len(prices) % 2 == 0:
                median_price = (
                    prices[len(prices) // 2 - 1] + prices[len(prices) // 2]
                ) / 2
            else:
                median_price = prices[len(prices) // 2]
            await cache.set(cache_key, str(median_price), ttl=self.cache_ttl)
            return median_price
        except Exception as e:
            logger.error(f"Error in price aggregator: {e}")
            return None

    async def get_multiple_prices(
        self, symbols: List[str]
    ) -> Dict[str, Optional[Decimal]]:
        """
        Get prices for multiple symbols efficiently
        """
        tasks = [self.get_price(symbol) for symbol in symbols]
        prices = await asyncio.gather(*tasks, return_exceptions=True)
        result = {}
        for symbol, price in zip(symbols, prices):
            if isinstance(price, Exception):
                result[symbol] = None
            else:
                result[symbol] = price
        return result


class BasePriceFeed:
    """Base class for price feed sources"""

    def __init__(self) -> None:
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = ""
        self.api_key = None
        self.rate_limit = 1.0
        self.last_request = 0.0

    async def __aenter__(self) -> "BasePriceFeed":
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self.session:
            await self.session.close()
            self.session = None

    async def get_price(self, symbol: str) -> Optional[Decimal]:
        """Get price for symbol - to be implemented by subclasses"""
        raise NotImplementedError

    async def _make_request(
        self, url: str, params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make HTTP request with rate limiting"""
        try:
            now = datetime.now().timestamp()
            if now - self.last_request < self.rate_limit:
                await asyncio.sleep(self.rate_limit - (now - self.last_request))
            if not self.session:
                self.session = aiohttp.ClientSession()
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            async with self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                self.last_request = datetime.now().timestamp()
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"HTTP {response.status} from {url}")
                    return None
        except Exception as e:
            logger.error(f"Request error for {url}: {e}")
            return None


class CoinGeckoPriceFeed(BasePriceFeed):
    """CoinGecko price feed"""

    def __init__(self) -> None:
        super().__init__()
        self.base_url = "https://api.coingecko.com/api/v3"
        self.rate_limit = 1.2
        self.symbol_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binancecoin",
            "ADA": "cardano",
            "SOL": "solana",
            "DOT": "polkadot",
            "MATIC": "polygon",
            "LINK": "chainlink",
            "AVAX": "avalanche-2",
            "UNI": "uniswap",
        }

    async def get_price(self, symbol: str) -> Optional[Decimal]:
        """Get price from CoinGecko"""
        try:
            coin_id = self.symbol_map.get(symbol.upper())
            if not coin_id:
                return None
            url = f"{self.base_url}/simple/price"
            params = {"ids": coin_id, "vs_currencies": "usd"}
            data = await self._make_request(url, params)
            if data and coin_id in data and "usd" in data[coin_id]:
                price = data[coin_id]["usd"]
                return Decimal(str(price))
            return None
        except Exception as e:
            logger.error(f"CoinGecko price error for {symbol}: {e}")
            return None


class CoinMarketCapPriceFeed(BasePriceFeed):
    """CoinMarketCap price feed"""

    def __init__(self) -> None:
        super().__init__()
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.api_key = settings.external_apis.COINMARKETCAP_API_KEY
        self.rate_limit = 1.0

    async def get_price(self, symbol: str) -> Optional[Decimal]:
        """Get price from CoinMarketCap"""
        try:
            if not self.api_key:
                return None
            url = f"{self.base_url}/cryptocurrency/quotes/latest"
            params = {"symbol": symbol.upper(), "convert": "USD"}
            data = await self._make_request(url, params)
            if (
                data
                and "data" in data
                and symbol.upper() in data["data"]
                and "quote" in data["data"][symbol.upper()]
                and "USD" in data["data"][symbol.upper()]["quote"]
            ):
                price = data["data"][symbol.upper()]["quote"]["USD"]["price"]
                return Decimal(str(price))
            return None
        except Exception as e:
            logger.error(f"CoinMarketCap price error for {symbol}: {e}")
            return None


class BinancePriceFeed(BasePriceFeed):
    """Binance price feed"""

    def __init__(self) -> None:
        super().__init__()
        self.base_url = "https://api.binance.com/api/v3"
        self.rate_limit = 0.1

    async def get_price(self, symbol: str) -> Optional[Decimal]:
        """Get price from Binance"""
        try:
            trading_pair = f"{symbol.upper()}USDT"
            url = f"{self.base_url}/ticker/price"
            params = {"symbol": trading_pair}
            data = await self._make_request(url, params)
            if data and "price" in data:
                price = data["price"]
                return Decimal(str(price))
            return None
        except Exception as e:
            logger.error(f"Binance price error for {symbol}: {e}")
            return None


class CryptoComparePriceFeed(BasePriceFeed):
    """CryptoCompare price feed"""

    def __init__(self) -> None:
        super().__init__()
        self.base_url = "https://min-api.cryptocompare.com/data"
        self.api_key = settings.external_apis.CRYPTOCOMPARE_API_KEY
        self.rate_limit = 1.0

    async def get_price(self, symbol: str) -> Optional[Decimal]:
        """Get price from CryptoCompare"""
        try:
            url = f"{self.base_url}/price"
            params = {"fsym": symbol.upper(), "tsyms": "USD"}
            if self.api_key:
                headers = {"authorization": f"Apikey {self.api_key}"}
                data = await self._make_request(url, params)
            else:
                data = await self._make_request(url, params)
            if data and "USD" in data:
                price = data["USD"]
                return Decimal(str(price))
            return None
        except Exception as e:
            logger.error(f"CryptoCompare price error for {symbol}: {e}")
            return None


class AlphaPriceFeed(BasePriceFeed):
    """Alpha Vantage price feed for traditional assets"""

    def __init__(self) -> None:
        super().__init__()
        self.base_url = "https://www.alphavantage.co/query"
        self.api_key = settings.external_apis.ALPHA_VANTAGE_API_KEY
        self.rate_limit = 12.0

    async def get_price(self, symbol: str) -> Optional[Decimal]:
        """Get price from Alpha Vantage"""
        try:
            if not self.api_key:
                return None
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol.upper(),
                "apikey": self.api_key,
            }
            data = await self._make_request(self.base_url, params)
            if data and "Global Quote" in data and "05. price" in data["Global Quote"]:
                price = data["Global Quote"]["05. price"]
                return Decimal(str(price))
            return None
        except Exception as e:
            logger.error(f"Alpha Vantage price error for {symbol}: {e}")
            return None


class YahooPriceFeed(BasePriceFeed):
    """Yahoo Finance price feed"""

    def __init__(self) -> None:
        super().__init__()
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.rate_limit = 0.5

    async def get_price(self, symbol: str) -> Optional[Decimal]:
        """Get price from Yahoo Finance"""
        try:
            url = f"{self.base_url}/{symbol.upper()}"
            data = await self._make_request(url)
            if (
                data
                and "chart" in data
                and "result" in data["chart"]
                and data["chart"]["result"]
                and "meta" in data["chart"]["result"][0]
                and "regularMarketPrice" in data["chart"]["result"][0]["meta"]
            ):
                price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
                return Decimal(str(price))
            return None
        except Exception as e:
            logger.error(f"Yahoo Finance price error for {symbol}: {e}")
            return None


class PriceValidator:
    """Validates price data for accuracy and consistency"""

    @staticmethod
    def validate_price(
        symbol: str, price: Decimal, historical_prices: List[Decimal]
    ) -> bool:
        """
        Validate price against historical data and reasonable bounds
        """
        try:
            if price <= 0:
                return False
            if historical_prices:
                recent = historical_prices[-10:]
                recent_avg = sum(recent) / len(recent)
                deviation = abs(price - recent_avg) / recent_avg
                if deviation > Decimal("0.5"):
                    logger.warning(
                        f"Price deviation too high for {symbol}: {deviation:.2%}"
                    )
                    return False
            if symbol.upper() == "BTC":
                if not (Decimal("1000") <= price <= Decimal("1000000")):
                    return False
            elif symbol.upper() == "ETH":
                if not (Decimal("10") <= price <= Decimal("50000")):
                    return False
            return True
        except Exception as e:
            logger.error(f"Price validation error: {e}")
            return False

    @staticmethod
    def detect_outliers(prices: List[Decimal], threshold: float = 2.0) -> List[bool]:
        """
        Detect outliers using z-score method
        """
        if len(prices) < 3:
            return [False] * len(prices)
        try:
            prices_float = [float(p) for p in prices]
            mean_price = sum(prices_float) / len(prices_float)
            variance = sum((p - mean_price) ** 2 for p in prices_float) / len(
                prices_float
            )
            std_dev = variance**0.5
            if std_dev == 0:
                return [False] * len(prices)
            z_scores = [(p - mean_price) / std_dev for p in prices_float]
            outliers = [abs(z) > threshold for z in z_scores]
            return outliers
        except Exception as e:
            logger.error(f"Outlier detection error: {e}")
            return [False] * len(prices)


class PriceFeedManager:
    """
    Manages multiple price feeds with health monitoring and failover
    """

    def __init__(self) -> None:
        self.aggregator = PriceFeedAggregator()
        self.validator = PriceValidator()
        self.health_status: Dict[str, Any] = {}
        self.last_health_check = datetime.now()
        self.health_check_interval = timedelta(minutes=5)

    async def get_validated_price(self, symbol: str) -> Optional[Decimal]:
        """
        Get price with validation and health checking
        """
        try:
            if datetime.now() - self.last_health_check > self.health_check_interval:
                await self._check_feed_health()
            price = await self.aggregator.get_price(symbol)
            if price is None:
                return None
            historical_prices = await self._get_historical_prices(symbol, days=10)
            if self.validator.validate_price(symbol, price, historical_prices):
                return price
            else:
                logger.warning(f"Price validation failed for {symbol}: {price}")
                return None
        except Exception as e:
            logger.error(f"Error getting validated price for {symbol}: {e}")
            return None

    async def _check_feed_health(self) -> None:
        """Check health of all price feeds"""
        try:
            test_symbols = ["BTC", "ETH"]
            for source in self.aggregator.sources:
                source_name = source.__class__.__name__
                healthy = True
                for symbol in test_symbols:
                    try:
                        price = await source.get_price(symbol)
                        if price is None or price <= 0:
                            healthy = False
                            break
                    except Exception:
                        healthy = False
                        break
                self.health_status[source_name] = {
                    "healthy": healthy,
                    "last_check": datetime.now().isoformat(),
                }
            self.last_health_check = datetime.now()
            unhealthy_sources = [
                name
                for name, status in self.health_status.items()
                if not status["healthy"]
            ]
            if unhealthy_sources:
                logger.warning(f"Unhealthy price feeds: {unhealthy_sources}")
        except Exception as e:
            logger.error(f"Error checking feed health: {e}")

    async def _get_historical_prices(
        self, symbol: str, days: int = 10
    ) -> List[Decimal]:
        """Get historical prices for validation"""
        try:
            return []
        except Exception as e:
            logger.error(f"Error getting historical prices: {e}")
            return []

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all price feeds"""
        return {
            "last_health_check": self.last_health_check.isoformat(),
            "sources": self.health_status,
            "overall_health": all(
                status["healthy"] for status in self.health_status.values()
            ),
        }

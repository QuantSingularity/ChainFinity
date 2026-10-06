import importlib
from typing import Any, Dict

_SUBPACKAGES: Dict[str, str] = {
    "VolatilityForecaster": "volatility",
    "ewma_volatility_forecast": "volatility",
    "CorrelationPredictor": "correlation",
    "shrunk_correlation": "correlation",
    "ExploitDetector": "exploit",
    "ExploitAlert": "exploit",
    "LiquidityCrisisDetector": "liquidity",
    "LiquidityAlert": "liquidity",
    "SmartMoneyTracker": "smart_money",
    "WalletProfile": "smart_money",
    "MovementSignal": "smart_money",
}

__all__ = sorted(_SUBPACKAGES)


def __getattr__(name: str) -> Any:
    subpackage = _SUBPACKAGES.get(name)
    if subpackage is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(f".{subpackage}", __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value

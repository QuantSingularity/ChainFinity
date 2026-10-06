import importlib
from typing import Any, Dict

__version__ = "2.0.0"

_EXPORTS: Dict[str, str] = {
    "VolatilityForecaster": "models.volatility",
    "ewma_volatility_forecast": "models.volatility",
    "CorrelationPredictor": "models.correlation",
    "shrunk_correlation": "models.correlation",
    "ExploitDetector": "models.exploit",
    "ExploitAlert": "models.exploit",
    "LiquidityCrisisDetector": "models.liquidity",
    "LiquidityAlert": "models.liquidity",
    "SmartMoneyTracker": "models.smart_money",
    "WalletProfile": "models.smart_money",
    "MovementSignal": "models.smart_money",
}

__all__ = sorted(_EXPORTS) + ["__version__"]


def __getattr__(name: str) -> Any:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(f".{module_name}", __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value

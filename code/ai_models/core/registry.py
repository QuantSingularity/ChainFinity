from typing import Dict, Tuple

MODEL_NAMES: Tuple[str, ...] = ("volatility", "correlation", "exploit", "smart_money")

ARTIFACT_DIRS: Dict[str, str] = {
    "volatility": "volatility_forecaster",
    "correlation": "correlation_predictor",
    "exploit": "exploit_detector",
    "smart_money": "smart_money_tracker",
}

INDEX_COLUMNS: Dict[str, str] = {
    "volatility": "timestamp",
    "correlation": "timestamp",
    "exploit": "timestamp",
    "smart_money": "address",
}

DEFAULT_ARTIFACTS_DIR = "ai_artifacts"

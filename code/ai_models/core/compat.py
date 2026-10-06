import importlib
import importlib.util
import threading
from typing import Any, Optional

TF_AVAILABLE = importlib.util.find_spec("tensorflow") is not None

_tf_module: Optional[Any] = None
_tf_lock = threading.Lock()


def require_tensorflow(feature: str) -> Any:
    global _tf_module
    if not TF_AVAILABLE:
        raise ImportError(
            f"TensorFlow is required for {feature}. Install it with: pip install tensorflow"
        )
    if _tf_module is None:
        with _tf_lock:
            if _tf_module is None:
                _tf_module = importlib.import_module("tensorflow")
    return _tf_module

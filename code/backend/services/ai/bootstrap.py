import importlib
import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _candidate_roots(configured: Optional[str]) -> list:
    candidates = []
    if configured:
        candidates.append(Path(configured).expanduser().resolve())
    candidates.append(BACKEND_ROOT)
    candidates.append(BACKEND_ROOT.parent / "ai_models")
    return candidates


def ensure_ai_models_importable(configured: Optional[str] = None) -> bool:
    try:
        importlib.import_module("ai_models")
        return True
    except ImportError:
        pass
    for candidate in _candidate_roots(configured):
        if candidate.name == "ai_models" and (candidate / "__init__.py").is_file():
            parent = str(candidate.parent)
        elif (candidate / "ai_models" / "__init__.py").is_file():
            parent = str(candidate)
        else:
            continue
        if parent not in sys.path:
            sys.path.insert(0, parent)
        try:
            importlib.import_module("ai_models")
            return True
        except ImportError as exc:
            logger.warning("Could not import ai_models from %s: %s", parent, exc)
    return False

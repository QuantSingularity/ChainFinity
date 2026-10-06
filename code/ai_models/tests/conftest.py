import os
import sys
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

PARENT = str(Path(__file__).resolve().parents[2])
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

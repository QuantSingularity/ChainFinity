import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Sequence

import pandas as pd

from . import __version__
from .core.persistence import META_FILE, artifact_exists
from .core.registry import (
    ARTIFACT_DIRS,
    DEFAULT_ARTIFACTS_DIR,
    INDEX_COLUMNS,
    MODEL_NAMES,
)

logger = logging.getLogger("ai_models.cli")


def read_table(path: Path, index_column: str) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")
    df = pd.read_csv(path)
    if index_column in df.columns:
        if index_column == "timestamp":
            df[index_column] = pd.to_datetime(
                df[index_column], errors="coerce", utc=True
            )
            df = df.dropna(subset=[index_column])
        df = df.set_index(index_column).sort_index()
    return df


def _train_volatility(df: pd.DataFrame, args: argparse.Namespace) -> Any:
    from .models.volatility import VolatilityForecaster

    model = VolatilityForecaster(
        sequence_length=args.sequence_length, forecast_horizon=args.horizon
    )
    return model.fit(df, epochs=args.epochs, verbose=args.verbose)


def _train_correlation(df: pd.DataFrame, args: argparse.Namespace) -> Any:
    from .models.correlation import CorrelationPredictor

    model = CorrelationPredictor(
        sequence_length=args.sequence_length, target_window=args.target_window
    )
    return model.fit(df, epochs=args.epochs, verbose=args.verbose)


def _train_exploit(df: pd.DataFrame, args: argparse.Namespace) -> Any:
    from .models.exploit import ExploitDetector

    model = ExploitDetector(
        sequence_length=args.sequence_length,
        contamination=args.contamination,
        use_autoencoder=not args.no_autoencoder,
    )
    return model.fit(df, epochs=args.epochs, verbose=args.verbose)


def _train_smart_money(df: pd.DataFrame, args: argparse.Namespace) -> Any:
    from .models.smart_money import SmartMoneyTracker

    return SmartMoneyTracker(n_clusters=args.clusters).fit(df)


TRAINERS: Dict[str, Callable[[pd.DataFrame, argparse.Namespace], Any]] = {
    "volatility": _train_volatility,
    "correlation": _train_correlation,
    "exploit": _train_exploit,
    "smart_money": _train_smart_money,
}


def run_train(args: argparse.Namespace) -> int:
    df = read_table(Path(args.data), INDEX_COLUMNS[args.model])
    logger.info("Training '%s' on %d rows", args.model, len(df))
    model = TRAINERS[args.model](df, args)
    target = Path(args.artifacts_dir) / ARTIFACT_DIRS[args.model]
    model.save(target)
    print(json.dumps({"model": args.model, "artifact": str(target), "rows": len(df)}))
    return 0


def run_inspect(args: argparse.Namespace) -> int:
    root = Path(args.artifacts_dir)
    report: Dict[str, Any] = {}
    for name in MODEL_NAMES:
        target = root / ARTIFACT_DIRS[name]
        if artifact_exists(target):
            report[name] = json.loads((target / META_FILE).read_text(encoding="utf-8"))
        else:
            report[name] = None
    print(json.dumps(report, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai_models", description="ChainFinity AI model tooling"
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    train = sub.add_parser(
        "train", help="Train a model from a CSV file and save its artifact"
    )
    train.add_argument("model", choices=MODEL_NAMES)
    train.add_argument("--data", required=True)
    train.add_argument("--artifacts-dir", default=DEFAULT_ARTIFACTS_DIR)
    train.add_argument("--epochs", type=int, default=50)
    train.add_argument("--sequence-length", type=int, default=30)
    train.add_argument("--horizon", type=int, default=7)
    train.add_argument("--target-window", type=int, default=14)
    train.add_argument("--contamination", type=float, default=0.05)
    train.add_argument("--no-autoencoder", action="store_true")
    train.add_argument("--clusters", type=int, default=5)
    train.add_argument("--verbose", type=int, default=0)
    train.set_defaults(func=run_train)

    inspect = sub.add_parser("inspect", help="Show saved model artifacts")
    inspect.add_argument("--artifacts-dir", default=DEFAULT_ARTIFACTS_DIR)
    inspect.set_defaults(func=run_inspect)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())

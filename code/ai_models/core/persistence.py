import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple, Union

import joblib

from .compat import require_tensorflow

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1
STATE_FILE = "state.joblib"
META_FILE = "meta.json"

PathLike = Union[str, Path]


class ArtifactError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_exists(directory: PathLike) -> bool:
    root = Path(directory)
    return (root / META_FILE).is_file() and (root / STATE_FILE).is_file()


def save_artifact(
    directory: PathLike,
    model_type: str,
    state: Mapping[str, Any],
    keras_models: Optional[Mapping[str, Any]] = None,
) -> Path:
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    checksums: Dict[str, str] = {}

    state_path = root / STATE_FILE
    joblib.dump(dict(state), state_path)
    checksums[STATE_FILE] = _sha256(state_path)

    keras_files = []
    for name, model in (keras_models or {}).items():
        filename = f"{name}.keras"
        model.save(root / filename)
        checksums[filename] = _sha256(root / filename)
        keras_files.append(filename)

    meta = {
        "schema_version": SCHEMA_VERSION,
        "model_type": model_type,
        "keras_files": keras_files,
        "checksums": checksums,
    }
    (root / META_FILE).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    logger.info("Saved %s artifact to %s", model_type, root)
    return root


def load_artifact(
    directory: PathLike, expected_type: str
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    root = Path(directory)
    meta_path = root / META_FILE
    if not meta_path.is_file():
        raise ArtifactError(f"No model artifact found at {root}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("schema_version") != SCHEMA_VERSION:
        raise ArtifactError(
            f"Unsupported artifact schema version: {meta.get('schema_version')}"
        )
    if meta.get("model_type") != expected_type:
        raise ArtifactError(
            f"Artifact at {root} is a {meta.get('model_type')!r} model, "
            f"expected {expected_type!r}"
        )
    for filename, expected in meta.get("checksums", {}).items():
        target = root / filename
        if not target.is_file():
            raise ArtifactError(f"Artifact file missing: {filename}")
        if _sha256(target) != expected:
            raise ArtifactError(f"Checksum mismatch for artifact file: {filename}")

    state = joblib.load(root / STATE_FILE)
    keras_models: Dict[str, Any] = {}
    if meta.get("keras_files"):
        tf = require_tensorflow("loading saved neural network models")
        for filename in meta["keras_files"]:
            keras_models[filename[: -len(".keras")]] = tf.keras.models.load_model(
                root / filename, compile=False
            )
    return state, keras_models

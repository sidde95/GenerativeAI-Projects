"""Helper utilities used across the application."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Union


def project_root() -> Path:
    """Return the repository root directory."""

    return Path(__file__).resolve().parent.parent


def _resolve_path(filepath: Union[str, Path]) -> Path:
    path = Path(filepath)
    if path.is_absolute():
        return path

    project_relative = project_root() / path
    if project_relative.exists() or project_relative.parent.exists():
        return project_relative

    return Path.cwd() / path


def generate_run_id() -> str:
    """Generate a unique run ID."""

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    short_uuid = str(uuid.uuid4())[:8]
    return f"fc-{timestamp}-{short_uuid}"


def load_json_file(filepath: Union[str, Path]) -> Dict[str, Any]:
    """Load a JSON object from disk."""

    path = _resolve_path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}, got {type(payload).__name__}")

    return payload


def save_json_file(data: Dict[str, Any], filepath: Union[str, Path]) -> None:
    """Persist a JSON object to disk."""

    path = Path(filepath)
    if not path.is_absolute():
        path = project_root() / path

    ensure_dir(path.parent)

    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def ensure_dir(dirpath: Union[str, Path]) -> Path:
    """Ensure a directory exists and return it."""

    path = Path(dirpath)
    path.mkdir(parents=True, exist_ok=True)
    return path


def format_currency(amount: float) -> str:
    """Format a numeric value as currency."""

    return f"${amount:,.2f}"


def calculate_percentage(part: float, whole: float) -> float:
    """Calculate percentage safely."""

    if whole == 0:
        return 0.0
    return (part / whole) * 100


def get_timestamp() -> str:
    """Return the current timestamp in ISO format."""

    return datetime.now().isoformat()
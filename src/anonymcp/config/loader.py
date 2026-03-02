"""Load policy configuration from YAML/JSON files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_policy_file(path: Path) -> dict[str, Any]:
    """Load a YAML or JSON policy file and return as a dictionary.

    Args:
        path: Path to the policy file (.yaml, .yml, or .json).

    Returns:
        Parsed policy configuration dictionary.

    Raises:
        FileNotFoundError: If the policy file does not exist.
        ValueError: If the file format is not supported.
    """
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")

    suffix = path.suffix.lower()

    if suffix in (".yaml", ".yml"):
        with open(path) as f:
            data = yaml.safe_load(f)
    elif suffix == ".json":
        import json

        with open(path) as f:
            data = json.load(f)
    else:
        raise ValueError(f"Unsupported policy file format: {suffix}. Use .yaml, .yml, or .json")

    if not isinstance(data, dict):
        raise ValueError(f"Policy file must contain a mapping, got {type(data).__name__}")

    return data

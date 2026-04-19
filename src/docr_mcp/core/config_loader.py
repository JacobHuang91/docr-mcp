"""Configuration loading utilities."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from docr_mcp.models import LibraryConfig


def load_config(library: str) -> LibraryConfig:
    """Load and validate configuration for a library.

    Args:
        library: Library name (e.g., "strands", "aws")

    Returns:
        Validated LibraryConfig object

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    # Get config directory (relative to this file)
    config_dir = Path(__file__).parent.parent / "config"
    config_file = config_dir / f"{library}.yml"

    if not config_file.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_file}\n"
            f"Available libraries: {', '.join([f.stem for f in config_dir.glob('*.yml')])}"
        )

    with open(config_file, "r") as f:
        config_data = yaml.safe_load(f)

    # Validate and create Pydantic model
    try:
        config = LibraryConfig(**config_data)
    except ValidationError as e:
        raise ValueError(f"Invalid config for '{library}': {e}") from e

    return config

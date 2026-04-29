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

    # Try public first, then authenticated
    public_config = config_dir / "public" / f"{library}.yml"
    authenticated_config = config_dir / "authenticated" / f"{library}.yml"

    if public_config.exists():
        config_file = public_config
    elif authenticated_config.exists():
        config_file = authenticated_config
    else:
        # List available configs from both directories
        public_libs = (
            [f.stem for f in (config_dir / "public").glob("*.yml") if not f.stem.endswith(".example")]
            if (config_dir / "public").exists()
            else []
        )
        authenticated_libs = (
            [f.stem for f in (config_dir / "authenticated").glob("*.yml") if not f.stem.endswith(".example")]
            if (config_dir / "authenticated").exists()
            else []
        )
        all_libs = sorted(public_libs + authenticated_libs)

        raise FileNotFoundError(
            f"Configuration file not found: {library}.yml\nAvailable libraries: {', '.join(all_libs)}"
        )

    with open(config_file, "r") as f:
        config_data = yaml.safe_load(f)

    # Validate and create Pydantic model
    try:
        config = LibraryConfig(**config_data)
    except ValidationError as e:
        raise ValueError(f"Invalid config for '{library}': {e}") from e

    return config

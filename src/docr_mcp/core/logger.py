"""Centralized logging configuration for docr-mcp."""

import logging
import sys
from typing import Optional


def setup_logger(name: str = "docr_mcp", level: Optional[int] = None) -> logging.Logger:
    """Configure and return a logger instance.

    Args:
        name: Logger name (default: "docr_mcp")
        level: Logging level (default: INFO, or DEBUG if DOCR_DEBUG env var is set)

    Returns:
        Configured logger instance
    """
    import os

    # Determine log level
    if level is None:
        level = logging.DEBUG if os.getenv("DOCR_DEBUG") else logging.INFO

    # Get logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    # Create console handler with formatting
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    # Format: [2026-04-19 14:30:45] INFO - docr_mcp.parsers.strands - Message
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s - %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False

    return logger


# Convenience function to get logger for any module
def get_logger(module_name: str) -> logging.Logger:
    """Get a logger for a specific module.

    Args:
        module_name: Usually __name__ from the calling module

    Returns:
        Logger instance with module-specific name
    """
    return logging.getLogger(module_name)

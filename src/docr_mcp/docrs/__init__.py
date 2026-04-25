"""Docr factory and loader."""

from docr_mcp.models import LibraryConfig

from .base import BaseDocr


def load_docr(config: LibraryConfig) -> BaseDocr:
    """Load the appropriate docr based on config.

    Args:
        config: LibraryConfig object

    Returns:
        Docr instance for the specified library

    Raises:
        ValueError: If docr type is unknown
    """
    docr_name = config.parser

    if docr_name == "strands":
        from .strands import StrandsDocr

        return StrandsDocr()

    elif docr_name == "vercel":
        from .vercel import VercelDocr

        return VercelDocr()

    elif docr_name == "twilio":
        from .twilio import TwilioDocr

        return TwilioDocr()

    else:
        raise ValueError(f"Unknown docr: {docr_name}. Available docrs: strands, vercel, twilio")

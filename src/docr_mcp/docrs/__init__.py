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

    # Public docrs
    if docr_name == "strands":
        from .public.strands import StrandsDocr

        return StrandsDocr()

    elif docr_name == "vercel":
        from .public.vercel import VercelDocr

        return VercelDocr()

    elif docr_name == "twilio":
        from .public.twilio import TwilioDocr

        return TwilioDocr()

    elif docr_name == "openai":
        from .public.openai import OpenAIDocr

        return OpenAIDocr()

    elif docr_name == "stripe":
        from .public.stripe import StripeDocr

        return StripeDocr()

    elif docr_name == "anthropic":
        from .public.anthropic import AnthropicDocr

        return AnthropicDocr()

    # Authenticated docrs (require authentication)
    elif docr_name == "cookie":
        from .authenticated.cookie import CookieDocr

        return CookieDocr(auth_config=config.auth)

    else:
        raise ValueError(
            f"Unknown docr: {docr_name}. Available docrs: strands, vercel, twilio, openai, stripe, anthropic, cookie"
        )

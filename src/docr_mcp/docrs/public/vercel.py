"""Docr for Vercel documentation."""

from ..patterns import LLMsMdDocr


class VercelDocr(LLMsMdDocr):
    """Docr for Vercel documentation (vercel.com)."""

    ALLOWED_DOMAINS = {"vercel.com"}
    SOURCE_NAME = "vercel"

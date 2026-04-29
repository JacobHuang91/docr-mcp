"""Docr for Anthropic documentation."""

from ..patterns import LLMsMdDocr


class AnthropicDocr(LLMsMdDocr):
    """Docr for Anthropic documentation (platform.claude.com)."""

    ALLOWED_DOMAINS = {"platform.claude.com", "claude.com"}
    SOURCE_NAME = "anthropic"

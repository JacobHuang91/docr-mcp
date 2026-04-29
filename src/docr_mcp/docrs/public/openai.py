"""Docr for OpenAI documentation."""

from ..patterns import LLMsMdDocr


class OpenAIDocr(LLMsMdDocr):
    """Docr for OpenAI documentation (platform.openai.com)."""

    ALLOWED_DOMAINS = {"platform.openai.com", "developers.openai.com", "openai.com"}
    SOURCE_NAME = "openai"

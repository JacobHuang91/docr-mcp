"""Docr for Strands Agents documentation."""

from ..patterns import LLMsMdDocr


class StrandsDocr(LLMsMdDocr):
    """Docr for Strands Agents documentation (strandsagents.com)."""

    ALLOWED_DOMAINS = {"strandsagents.com"}
    SOURCE_NAME = "strands"

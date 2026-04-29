"""Docr for Twilio documentation."""

from ..patterns import LLMsMdDocr


class TwilioDocr(LLMsMdDocr):
    """Docr for Twilio public documentation (www.twilio.com)."""

    ALLOWED_DOMAINS = {"www.twilio.com", "twilio.com"}
    SOURCE_NAME = "twilio"

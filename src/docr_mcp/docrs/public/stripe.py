"""Docr for Stripe documentation."""

from ..patterns import LLMsMdDocr


class StripeDocr(LLMsMdDocr):
    """Docr for Stripe documentation (docs.stripe.com)."""

    ALLOWED_DOMAINS = {"docs.stripe.com", "stripe.com"}
    SOURCE_NAME = "stripe"

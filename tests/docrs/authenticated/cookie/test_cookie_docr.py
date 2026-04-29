"""Tests for CookieDocr."""

import pytest

from docr_mcp.docrs.authenticated.cookie import CookieDocr
from docr_mcp.models import AuthConfig


class TestCookieDocr:
    """Test cases for CookieDocr."""

    def test_cookie_parsing(self):
        """Test cookie string parsing."""
        auth = AuthConfig(cookie="session=abc123")
        docr = CookieDocr(auth_config=auth)

        # Single cookie
        cookies = docr._parse_cookie_string("session=abc123")
        assert cookies == {"session": "abc123"}

        # Multiple cookies
        cookies = docr._parse_cookie_string("session=abc123; user=john")
        assert cookies == {"session": "abc123", "user": "john"}

        # With spaces
        cookies = docr._parse_cookie_string("session = abc123 ; user = john")
        assert cookies == {"session": "abc123", "user": "john"}

    def test_missing_auth_config(self):
        """Test that missing auth config raises error when accessing client."""
        docr = CookieDocr()  # No auth_config provided
        with pytest.raises(ValueError, match="Auth configuration with cookie is required"):
            docr._ensure_client()

    def test_missing_cookie_in_auth_config(self):
        """Test that missing cookie in auth config raises error."""
        auth = AuthConfig(allowed_domains=["example.com"])  # No cookie
        docr = CookieDocr(auth_config=auth)
        with pytest.raises(ValueError, match="Auth configuration with cookie is required"):
            docr._ensure_client()

    def test_url_validation_requires_domain(self):
        """Test that URL validation works with domain whitelist."""
        auth = AuthConfig(cookie="session=test", allowed_domains=["docs.example.com"])
        docr = CookieDocr(auth_config=auth)

        # Valid domain should pass
        docr._validate_url("https://docs.example.com/page")

        # Invalid domain should fail
        with pytest.raises(ValueError, match="Domain not allowed"):
            docr._validate_url("https://evil.com/docs")

    def test_url_validation_checks_https(self):
        """Test URL validation requires HTTPS."""
        auth = AuthConfig(cookie="session=test", allowed_domains=["docs.example.com"])
        docr = CookieDocr(auth_config=auth)

        # Invalid scheme
        with pytest.raises(ValueError, match="HTTPS"):
            docr._validate_url("http://docs.example.com/docs")

    def test_url_validation_no_domain_restriction(self):
        """Test URL validation when no domains specified."""
        auth = AuthConfig(cookie="session=test")
        docr = CookieDocr(auth_config=auth)

        # Any HTTPS URL should pass when no domains specified
        docr._validate_url("https://any-domain.com/page")
        docr._validate_url("https://another-domain.com/page")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Base docr interface."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

import httpx

from docr_mcp.models import Document, IndexConfig, IndexEntry


class BaseDocr(ABC):
    """Base interface that all docrs must implement.

    Provides common HTTP client functionality. Subclasses can override
    _get_client_config() to customize headers, cookies, or other client settings.
    """

    # Subclasses should define ALLOWED_DOMAINS
    ALLOWED_DOMAINS: Set[str] = set()

    def __init__(self):
        """Initialize docr with common HTTP client setup."""
        self.client: Optional[httpx.Client] = None
        self._timeout = 30.0

    def __enter__(self):
        """Context manager entry - initialize HTTP client."""
        self._ensure_client()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.close()
        return False

    def _get_client_config(self) -> Dict:
        """Get HTTP client configuration.

        Override this in subclasses to customize client settings.

        Returns:
            Dict with httpx.Client kwargs (timeout, headers, cookies, etc.)
        """
        return {
            "timeout": self._timeout,
            "follow_redirects": True,
            "headers": {"User-Agent": "docr-mcp/0.2.0"},
        }

    def _ensure_client(self):
        """Ensure HTTP client is initialized.

        Override this in subclasses that need custom initialization logic
        (e.g., loading cookies from environment).
        """
        if not self.client:
            config = self._get_client_config()
            self.client = httpx.Client(**config)

    def close(self):
        """Close and cleanup HTTP client.

        Override this method in subclasses that need additional cleanup.
        """
        if self.client:
            self.client.close()
            self.client = None

    def _validate_url(self, url: str) -> None:
        """Validate URL is safe to fetch.

        Checks:
        - URL is HTTPS only
        - Domain is in ALLOWED_DOMAINS

        Args:
            url: URL to validate

        Raises:
            ValueError: If URL is invalid or not allowed
        """
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValueError(f"Invalid URL format: {url}") from e

        # Must be HTTPS
        if parsed.scheme != "https":
            raise ValueError(f"Only HTTPS URLs are allowed, got: {parsed.scheme}")

        # Must be in allowed domains (if defined)
        if self.ALLOWED_DOMAINS and parsed.netloc not in self.ALLOWED_DOMAINS:
            raise ValueError(f"Domain not allowed: {parsed.netloc}. Allowed: {self.ALLOWED_DOMAINS}")

    @abstractmethod
    def fetch_index_entries(self, index_config: IndexConfig) -> List[IndexEntry]:
        """Fetch documentation index entries.

        Args:
            index_config: IndexConfig object with type and url

        Returns:
            List of IndexEntry objects with title, url, section, and tags
        """
        pass

    @abstractmethod
    def fetch_content(self, url: str) -> Document:
        """Fetch and parse a documentation page.

        Args:
            url: Documentation page URL

        Returns:
            Document object with url, content, and metadata
        """
        pass

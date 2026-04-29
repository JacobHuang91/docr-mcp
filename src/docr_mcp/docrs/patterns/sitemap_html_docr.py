"""SitemapHtmlDocr - Base implementation for docrs using sitemap.xml index + HTML content."""

import logging
from typing import List

import httpx

from docr_mcp.core.content_parsers import HtmlContentParser
from docr_mcp.core.index_parsers import SitemapIndexParser
from docr_mcp.models import Document, IndexConfig, IndexEntry

from ..base import BaseDocr

logger = logging.getLogger(__name__)


class SitemapHtmlDocr(BaseDocr):
    """Base docr for documentation using sitemap.xml index + HTML content.

    Provides default implementations for:
    - Fetching and parsing sitemap.xml index
    - Fetching HTML content and converting to markdown

    Subclasses only need to define:
    - ALLOWED_DOMAINS: Set of allowed domains
    - SOURCE_NAME: Name for metadata (e.g., "internal", "company-docs")
    """

    # Subclasses must define these
    SOURCE_NAME: str = "unknown"

    def fetch_index_entries(self, index_config: IndexConfig) -> List[IndexEntry]:
        """Fetch and parse sitemap.xml documentation index.

        Default implementation:
        1. Validates URL
        2. Fetches content
        3. Parses with SitemapIndexParser

        Args:
            index_config: IndexConfig object with source field pointing to sitemap.xml URL

        Returns:
            List of IndexEntry objects with title, URL, section, and tags

        Raises:
            ValueError: If source URL is invalid or entries list is empty
            httpx.HTTPError: If HTTP request fails
        """
        url = index_config.source
        self._timeout = index_config.timeout

        # Validate URL
        self._validate_url(url)

        # Initialize client if not already done
        self._ensure_client()

        logger.debug(f"Fetching sitemap.xml from {url}")

        try:
            # Fetch content
            response = self.client.get(url)
            response.raise_for_status()
            content = response.text
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise ValueError(f"Failed to fetch index from {url}: {type(e).__name__}") from e

        # Parse the content using SitemapIndexParser
        parser = SitemapIndexParser()
        entries = parser.parse(content)

        # Validate non-empty
        if not entries:
            raise ValueError(f"No entries found in index at {url}")

        logger.info(f"Parsed {len(entries)} entries from {url}")
        return entries

    def fetch_content(self, url: str) -> Document:
        """Fetch and parse a documentation page.

        Default implementation:
        1. Fetches HTML content
        2. Uses HtmlContentParser to extract and convert to markdown

        Args:
            url: Documentation page URL

        Returns:
            Document with markdown content converted from HTML

        Raises:
            ValueError: If URL is invalid
            httpx.HTTPError: If HTTP request fails
        """
        # Validate URL
        self._validate_url(url)

        # Initialize client if not already done
        self._ensure_client()

        logger.debug(f"Fetching content from {url}")

        try:
            response = self.client.get(url)
            response.raise_for_status()
            html_content = response.text
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise

        # Parse HTML content using HtmlContentParser
        parser = HtmlContentParser()
        markdown_content, title = parser.parse(html_content)

        return Document(
            url=url,
            content=markdown_content,
            metadata={"title": title, "source": self.SOURCE_NAME, "format": "markdown"},
        )

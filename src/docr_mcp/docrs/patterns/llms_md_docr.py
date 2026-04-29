"""LLMsMdDocr - Base implementation for docrs using llms.txt index + markdown content."""

import logging
from typing import List

import httpx

from docr_mcp.core.index_parsers import LLMsIndexParser
from docr_mcp.models import Document, IndexConfig, IndexEntry

from ..base import BaseDocr

logger = logging.getLogger(__name__)


class LLMsMdDocr(BaseDocr):
    """Base docr for documentation using llms.txt index + markdown content.

    Provides default implementations for:
    - Fetching and parsing llms.txt index
    - Fetching markdown content with HTML fallback

    Subclasses only need to define:
    - ALLOWED_DOMAINS: Set of allowed domains
    - SOURCE_NAME: Name for metadata (e.g., "stripe", "anthropic")
    """

    # Subclasses must define these
    SOURCE_NAME: str = "unknown"

    def fetch_index_entries(self, index_config: IndexConfig) -> List[IndexEntry]:
        """Fetch and parse llms.txt documentation index.

        Default implementation:
        1. Validates URL
        2. Fetches content
        3. Parses with LLMsIndexParser

        Args:
            index_config: IndexConfig object with source field pointing to llms.txt URL

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

        logger.debug(f"Fetching llms.txt from {url}")

        try:
            # Fetch content
            response = self.client.get(url)
            response.raise_for_status()
            content = response.text
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise ValueError(f"Failed to fetch index from {url}: {type(e).__name__}") from e

        # Parse the content using LLMsIndexParser
        # Extract base URL for resolving relative URLs (e.g., /docs/page.md)
        from urllib.parse import urlparse

        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        parser = LLMsIndexParser(base_url=base_url)
        entries = parser.parse(content)

        # Validate non-empty
        if not entries:
            raise ValueError(f"No entries found in index at {url}")

        logger.info(f"Parsed {len(entries)} entries from {url}")
        return entries

    def fetch_content(self, url: str) -> Document:
        """Fetch and parse a documentation page.

        Default implementation:
        1. Tries to fetch markdown (.md)
        2. Falls back to HTML if 404
        3. Extracts title from # heading

        Args:
            url: Documentation page URL

        Returns:
            Document with markdown content (or HTML if markdown unavailable)

        Raises:
            ValueError: If URL is invalid
            httpx.HTTPError: If HTTP request fails (non-404 errors)
        """
        # Validate URL
        self._validate_url(url)

        # Initialize client if not already done
        self._ensure_client()

        logger.debug(f"Fetching content from {url}")

        try:
            response = self.client.get(url)
            response.raise_for_status()
            content = response.text
            content_format = "markdown" if url.endswith(".md") else "html"
        except httpx.HTTPStatusError as e:
            # Fallback to HTML if markdown version doesn't exist
            if e.response.status_code == 404 and url.endswith(".md"):
                html_url = url[:-3]  # Remove .md extension
                logger.warning(f"Markdown not found at {url}, falling back to HTML")
                try:
                    response = self.client.get(html_url)
                    response.raise_for_status()
                    content = response.text
                    content_format = "html"
                    logger.info(f"Successfully fetched HTML from {html_url}")
                except httpx.HTTPError as html_error:
                    logger.error(f"Failed to fetch HTML from {html_url}: {html_error}")
                    raise
            else:
                logger.error(f"HTTP error fetching {url}: {e}")
                raise
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise

        # Extract title from first # heading if available
        title = ""
        first_line = content.split("\n")[0] if content else ""
        if first_line.startswith("# "):
            title = first_line[2:].strip()

        return Document(
            url=url, content=content, metadata={"title": title, "source": self.SOURCE_NAME, "format": content_format}
        )

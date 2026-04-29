"""Content parser for markdown documentation with optional HTML fallback."""

import logging
from typing import Callable, Optional

import httpx

from docr_mcp.models import Document

logger = logging.getLogger(__name__)


class MarkdownContentParser:
    """Parser for markdown documentation content with flexible fetching strategies.

    Supports multiple strategies:
    1. Direct markdown fetch (url points to .md file)
    2. Markdown with HTML fallback (try .md, fallback to HTML if 404)
    3. Custom URL transformation (e.g., add .md extension, convert paths)
    """

    def __init__(
        self,
        client: httpx.Client,
        html_fallback: bool = True,
        url_transform: Optional[Callable[[str], str]] = None,
        source_name: str = "unknown",
    ):
        """Initialize markdown content parser.

        Args:
            client: httpx.Client instance for making requests
            html_fallback: If True, fallback to HTML (remove .md) on 404 errors
            url_transform: Optional function to transform URL before fetching
            source_name: Source name for metadata (e.g., "stripe", "anthropic")
        """
        self.client = client
        self.html_fallback = html_fallback
        self.url_transform = url_transform
        self.source_name = source_name

    def fetch(self, url: str) -> Document:
        """Fetch and parse documentation content.

        Args:
            url: Documentation page URL

        Returns:
            Document with content and metadata

        Raises:
            httpx.HTTPError: If HTTP request fails
        """
        # Apply URL transformation if provided
        fetch_url = self.url_transform(url) if self.url_transform else url

        logger.debug(f"Fetching content from {fetch_url}")

        try:
            response = self.client.get(fetch_url)
            response.raise_for_status()
            content = response.text
            content_format = self._detect_format(fetch_url)

        except httpx.HTTPStatusError as e:
            # Try HTML fallback if enabled and markdown 404
            if self.html_fallback and e.response.status_code == 404 and fetch_url.endswith(".md"):
                content, content_format = self._try_html_fallback(fetch_url)
            else:
                logger.error(f"HTTP error fetching {fetch_url}: {e}")
                raise

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {fetch_url}: {e}")
            raise

        # Extract title from content
        title = self._extract_title(content, content_format)

        return Document(
            url=url,  # Return original URL, not transformed
            content=content,
            metadata={
                "title": title,
                "source": self.source_name,
                "format": content_format,
            },
        )

    def _try_html_fallback(self, md_url: str) -> tuple[str, str]:
        """Try fetching HTML version after markdown 404.

        Args:
            md_url: Markdown URL that returned 404

        Returns:
            Tuple of (content, format)

        Raises:
            httpx.HTTPError: If HTML fetch also fails
        """
        html_url = md_url[:-3]  # Remove .md extension
        logger.warning(f"Markdown not found at {md_url}, falling back to HTML")

        try:
            response = self.client.get(html_url)
            response.raise_for_status()
            content = response.text
            logger.info(f"Successfully fetched HTML from {html_url}")
            return content, "html"
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch HTML from {html_url}: {e}")
            raise

    def _detect_format(self, url: str) -> str:
        """Detect content format from URL.

        Args:
            url: Content URL

        Returns:
            Format string ("markdown" or "html")
        """
        return "markdown" if url.endswith(".md") else "html"

    def _extract_title(self, content: str, content_format: str) -> str:
        """Extract title from content.

        Args:
            content: Page content
            content_format: Content format ("markdown" or "html")

        Returns:
            Extracted title or empty string
        """
        if not content:
            return ""

        # For markdown, extract from # heading
        if content_format == "markdown":
            first_line = content.split("\n")[0]
            if first_line.startswith("# "):
                return first_line[2:].strip()

        # For HTML, could parse <title> or <h1> tags here if needed
        # For now, just return empty for HTML
        return ""

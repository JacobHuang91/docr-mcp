"""Docr for Stripe documentation."""

import logging
import re
from typing import List
from urllib.parse import urlparse

import httpx

from docr_mcp.models import Document, IndexConfig, IndexEntry

from .base import BaseDocr

logger = logging.getLogger(__name__)


class StripeDocr(BaseDocr):
    """Docr for Stripe documentation (docs.stripe.com)."""

    ALLOWED_DOMAINS = {"docs.stripe.com", "stripe.com"}

    def __init__(self):
        self.client = None
        self._timeout = 30.0

    def __enter__(self):
        """Context manager entry."""
        self.client = httpx.Client(
            timeout=self._timeout, follow_redirects=True, headers={"User-Agent": "docr-mcp/0.1.0"}
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        if self.client:
            self.client.close()
        return False

    def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if not self.client:
            self.client = httpx.Client(
                timeout=self._timeout, follow_redirects=True, headers={"User-Agent": "docr-mcp/0.1.0"}
            )

    def fetch_index_entries(self, index_config: IndexConfig) -> List[IndexEntry]:
        """Fetch and parse documentation index entries.

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

        # Parse the content
        entries = self._parse_llms_txt(content)

        # Validate non-empty
        if not entries:
            raise ValueError(f"No entries found in index at {url}")

        logger.info(f"Parsed {len(entries)} entries from {url}")
        return entries

    def _parse_llms_txt(self, content: str) -> List[IndexEntry]:
        """Parse llms.txt content into IndexEntry objects.

        Args:
            content: Raw llms.txt content

        Returns:
            List of parsed IndexEntry objects
        """
        docs = []
        lines = content.split("\n")

        # Track current section hierarchy
        current_section: List[str] = []
        section_stack: List[tuple[int, str]] = []  # (indent_level, section_name)

        for line in lines:
            # Skip empty lines and top-level title (single #)
            if not line.strip() or line.strip().startswith("# "):
                continue

            # Detect section headers (## Section Name)
            section_match = re.match(r"^##\s+(.+)$", line)
            if section_match:
                section_name = section_match.group(1)
                # Start fresh section hierarchy from this top-level section
                current_section = [section_name]
                section_stack = [(0, section_name)]
                continue

            # Calculate indentation level
            indent_match = re.match(r"^(\s*)(.+)$", line)
            if not indent_match:
                continue

            indent = len(indent_match.group(1))
            line_content = indent_match.group(2).strip()

            # Parse markdown link: * [title](url) or - [title](url)
            link_match = re.match(r"[*-]\s+\[(.+?)\]\((.+?)\)(?::\s+(.+))?", line_content)

            if link_match:
                title = link_match.group(1)
                doc_url = link_match.group(2)
                description = link_match.group(3) if link_match.group(3) else ""

                # Build full section path
                section_path = " > ".join(current_section)

                # Extract tags from title, section, and description
                tags = self._extract_tags(title, current_section, description)

                docs.append(
                    IndexEntry(
                        title=title,
                        url=doc_url,
                        section=section_path,
                        tags=tags,
                    )
                )

            else:
                # This is a section header without a link
                # Update the section hierarchy
                section_name = line_content.lstrip("*- ").strip()

                # Adjust section stack based on indentation
                # Pop sections at deeper or equal indentation levels
                while section_stack and section_stack[-1][0] > indent:
                    section_stack.pop()

                section_stack.append((indent, section_name))
                current_section = [name for _, name in section_stack]

        logger.debug(f"Parsed {len(docs)} documents from index")
        return docs

    def _extract_tags(self, title: str, section: List[str], description: str = "") -> List[str]:
        """Extract searchable tags from title, section, and description.

        Args:
            title: Document title
            section: Section hierarchy
            description: Optional description text

        Returns:
            List of tags for search
        """
        tags = []

        # Add section components as tags
        tags.extend([s.lower() for s in section if s])

        # Split title by common separators and add as tags
        title_parts = re.split(r"[-_\s]+", title.lower())
        tags.extend([p for p in title_parts if len(p) > 2])

        # Add description words as tags (if available)
        if description:
            desc_parts = re.split(r"[-_\s]+", description.lower())
            tags.extend([p for p in desc_parts if len(p) > 3])

        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        return unique_tags

    def _validate_url(self, url: str) -> None:
        """Validate URL is safe to fetch.

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

        # Must be in allowed domains
        if parsed.netloc not in self.ALLOWED_DOMAINS:
            raise ValueError(f"Domain not allowed: {parsed.netloc}. Allowed: {self.ALLOWED_DOMAINS}")

    def fetch_content(self, url: str) -> Document:
        """Fetch and parse a Stripe documentation page.

        Stripe URLs in llms.txt already include .md extension. This method
        fetches the markdown version directly, and falls back to HTML (by
        removing .md) if the markdown version is not available (404).

        Args:
            url: Documentation page URL (typically ends with .md)

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
            url=url, content=content, metadata={"title": title, "source": "stripe", "format": content_format}
        )

    def close(self):
        """Explicitly close HTTP client."""
        if self.client:
            self.client.close()
            self.client = None

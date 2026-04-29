"""Docr for cookie-based authentication.

This docr supports documentation sites that use cookie-based authentication
(e.g., Okta SSO, session cookies, JWT cookies).

Configuration:
    Configure in your YAML file:

    auth:
      cookie: "cookie_name=cookie_value"
      allowed_domains:
        - "docs.example.com"

    index:
      source: "https://docs.example.com/sitemap.xml"
"""

import logging
import re
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from docr_mcp.core.index_parsers import LLMsIndexParser, SitemapIndexParser
from docr_mcp.models import AuthConfig, Document, IndexConfig, IndexEntry

from ..base import BaseDocr

logger = logging.getLogger(__name__)


class CookieDocr(BaseDocr):
    """Docr for cookie-based authentication.

    Supports documentation sites that use cookie-based authentication
    (e.g., Okta SSO, session cookies, JWT cookies).

    Auth configuration is provided via LibraryConfig.auth field.
    """

    def __init__(self, auth_config: Optional[AuthConfig] = None):
        """Initialize CookieDocr with auth configuration.

        Args:
            auth_config: Authentication configuration from YAML
        """
        super().__init__()
        self._auth_config = auth_config
        self._allowed_domains = set()

        if auth_config and auth_config.allowed_domains:
            self._allowed_domains = set(auth_config.allowed_domains)

    def _get_client_config(self) -> dict:
        """Get HTTP client configuration with cookies.

        Overrides base class to add cookie authentication.

        Returns:
            Dict with httpx.Client kwargs including cookies

        Raises:
            ValueError: If auth_config or cookie is not provided
        """
        if not self._auth_config or not self._auth_config.cookie:
            raise ValueError(
                "Auth configuration with cookie is required for CookieDocr. "
                "Add 'auth' section to your YAML config file with 'cookie' field."
            )

        # Parse cookies
        cookies = self._parse_cookie_string(self._auth_config.cookie)

        # Get base config and add cookies
        config = super()._get_client_config()
        config["cookies"] = cookies
        return config

    def _parse_cookie_string(self, cookie_string: str) -> dict:
        """Parse cookie string into dict.

        Supports formats:
        - "name=value"
        - "name1=value1; name2=value2"
        """
        cookies = {}
        for cookie in cookie_string.split(";"):
            cookie = cookie.strip()
            if "=" in cookie:
                name, value = cookie.split("=", 1)
                cookies[name.strip()] = value.strip()
        return cookies

    def _validate_url(self, url: str) -> None:
        """Validate URL is safe to fetch.

        Overrides base class to use dynamic ALLOWED_DOMAINS from config.
        """
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValueError(f"Invalid URL format: {url}") from e

        # Must be HTTPS
        if parsed.scheme != "https":
            raise ValueError(f"Only HTTPS URLs are allowed, got: {parsed.scheme}")

        # Must be in allowed domains (if configured)
        if self._allowed_domains and parsed.netloc not in self._allowed_domains:
            raise ValueError(f"Domain not allowed: {parsed.netloc}. Allowed: {self._allowed_domains}")

    def fetch_index_entries(self, index_config: IndexConfig) -> List[IndexEntry]:
        """Fetch and parse documentation index entries.

        Supports multiple index formats:
        - llms.txt: Markdown-based documentation index
        - sitemap.xml: XML sitemap
        - HTML: Parse navigation from homepage (Docusaurus, etc.)

        Args:
            index_config: IndexConfig object with source field

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

        logger.debug(f"Fetching index from {url}")

        try:
            # Fetch content
            response = self.client.get(url)
            response.raise_for_status()
            content = response.text
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise ValueError(f"Failed to fetch index from {url}: {type(e).__name__}") from e

        # Detect format and parse accordingly
        if url.endswith(".xml") or "sitemap" in url.lower():
            parser = SitemapIndexParser()
            entries = parser.parse(content)
        elif url.endswith(".txt") or "llms.txt" in url:
            # Extract base URL for resolving relative URLs
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            parser = LLMsIndexParser(base_url=base_url)
            entries = parser.parse(content)
        else:
            # Assume HTML homepage with navigation
            entries = self._parse_html_navigation(content, url)

        # Validate non-empty
        if not entries:
            raise ValueError(f"No entries found in index at {url}")

        logger.info(f"Parsed {len(entries)} entries from {url}")
        return entries

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

    def _parse_html_navigation(self, content: str, base_url: str) -> List[IndexEntry]:
        """Parse HTML navigation into IndexEntry objects.

        Extracts links from common navigation patterns:
        - <nav> elements
        - Elements with class="nav", "sidebar", "menu"
        - <ul> lists with links

        Args:
            content: Raw HTML content
            base_url: Base URL for resolving relative URLs

        Returns:
            List of parsed IndexEntry objects
        """
        soup = BeautifulSoup(content, "html.parser")
        entries = []
        seen_urls = set()

        # Find navigation elements
        nav_elements = []
        nav_elements.extend(soup.find_all("nav"))
        nav_elements.extend(soup.find_all(class_=re.compile(r"(nav|sidebar|menu|toc)", re.I)))

        # If no nav found, look for lists with links
        if not nav_elements:
            nav_elements = soup.find_all("ul")

        for nav in nav_elements:
            # Find all links in this nav element
            links = nav.find_all("a", href=True)

            current_section = []
            for link in links:
                href = link.get("href", "").strip()
                text = link.get_text().strip()

                if not href or not text:
                    continue

                # Resolve relative URLs
                if not href.startswith(("http://", "https://", "#")):
                    href = urljoin(base_url, href)

                # Skip anchors and duplicates
                if href.startswith("#") or href in seen_urls:
                    continue

                seen_urls.add(href)

                # Detect if this is a section header (often has no href or is not a link)
                parent = link.parent
                if parent and parent.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    current_section = [text]
                    continue

                # Extract section from parent structure
                section = " > ".join(current_section) if current_section else ""

                # Extract tags from title and URL
                tags = self._extract_tags(text, current_section, "")

                entries.append(
                    IndexEntry(
                        title=text,
                        url=href,
                        section=section,
                        tags=tags,
                    )
                )

        return entries

    def fetch_content(self, url: str) -> Document:
        """Fetch and parse an authenticated documentation page.

        Args:
            url: Documentation page URL

        Returns:
            Document with content and metadata

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
            content = response.text
            content_format = "markdown" if url.endswith(".md") else "html"
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise

        # Extract title from first # heading if available
        title = ""
        first_line = content.split("\n")[0] if content else ""
        if first_line.startswith("# "):
            title = first_line[2:].strip()

        return Document(
            url=url, content=content, metadata={"title": title, "source": "cookie", "format": content_format}
        )

    def close(self):
        """Explicitly close HTTP client."""
        if self.client:
            self.client.close()
            self.client = None

"""Content parser for HTML documentation pages."""

import logging
from typing import Optional

from bs4 import BeautifulSoup
from markdownify import markdownify as md

logger = logging.getLogger(__name__)


class HtmlContentParser:
    """Content parser for HTML documentation pages.

    Extracts main content from HTML pages and converts to markdown.
    Handles common documentation site structures (Docusaurus, MkDocs, etc.).
    """

    def __init__(
        self,
        strip_navigation: bool = True,
        strip_footer: bool = True,
        strip_header: bool = True,
        heading_style: str = "ATX",
    ):
        """Initialize HTML content parser.

        Args:
            strip_navigation: Remove navigation elements (default: True)
            strip_footer: Remove footer elements (default: True)
            strip_header: Remove header elements (default: True)
            heading_style: Markdown heading style - "ATX" (#) or "SETEXT" (underline)
        """
        self.strip_navigation = strip_navigation
        self.strip_footer = strip_footer
        self.strip_header = strip_header
        self.heading_style = heading_style

    def parse(self, html_content: str) -> tuple[str, str]:
        """Parse HTML content and extract main content as markdown.

        Args:
            html_content: Raw HTML content

        Returns:
            Tuple of (markdown_content, title)
        """
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract main content
        main_content = self._extract_main_content(soup)

        # Clean up content
        if main_content:
            self._cleanup_content(main_content)

        # Extract title
        title = self._extract_title(soup, main_content)

        # Convert to markdown
        if main_content:
            markdown_content = md(str(main_content), heading_style=self.heading_style)
        else:
            # Fallback to full body if no main content found
            body = soup.find("body")
            markdown_content = md(str(body) if body else html_content, heading_style=self.heading_style)

        return markdown_content, title

    def _extract_main_content(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Extract main content from HTML.

        Tries common content container selectors in priority order:
        1. <main> tag
        2. <article> tag
        3. [role="main"] attribute
        4. Common class names (.content, .main-content, etc.)
        5. #content id

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Main content element or None
        """
        # Try semantic HTML5 tags first
        main_content = soup.find("main")
        if main_content:
            return main_content

        main_content = soup.find("article")
        if main_content:
            return main_content

        # Try ARIA role
        main_content = soup.find(attrs={"role": "main"})
        if main_content:
            return main_content

        # Try common class names
        for class_name in ["content", "main-content", "documentation", "docs-content", "article-content"]:
            main_content = soup.find(class_=class_name)
            if main_content:
                return main_content

        # Try common IDs
        main_content = soup.find(id="content")
        if main_content:
            return main_content

        main_content = soup.find(id="main")
        if main_content:
            return main_content

        # Fallback to body
        return soup.find("body")

    def _cleanup_content(self, content: BeautifulSoup) -> None:
        """Remove non-content elements from main content.

        Args:
            content: BeautifulSoup element to clean up
        """
        # Remove navigation elements
        if self.strip_navigation:
            for selector in ["nav", ".nav", ".navigation", ".sidebar", ".menu", ".toc", "[role='navigation']"]:
                for element in content.select(selector):
                    element.decompose()

        # Remove footer
        if self.strip_footer:
            for selector in ["footer", ".footer", "[role='contentinfo']"]:
                for element in content.select(selector):
                    element.decompose()

        # Remove header
        if self.strip_header:
            for selector in ["header", ".header", "[role='banner']"]:
                for element in content.select(selector):
                    element.decompose()

        # Remove scripts and styles
        for tag in content.find_all(["script", "style"]):
            tag.decompose()

        # Remove common non-content elements
        for class_name in ["advertisement", "ads", "promo", "banner", "cookie-notice"]:
            for element in content.find_all(class_=lambda x, cn=class_name: x and cn in x.lower()):
                element.decompose()

    def _extract_title(self, soup: BeautifulSoup, main_content: Optional[BeautifulSoup]) -> str:
        """Extract page title.

        Priority order:
        1. First <h1> in main content
        2. First <h1> in page
        3. <title> tag

        Args:
            soup: Full page BeautifulSoup
            main_content: Main content element

        Returns:
            Extracted title or empty string
        """
        # Try h1 in main content first
        if main_content:
            h1 = main_content.find("h1")
            if h1:
                return h1.get_text().strip()

        # Try any h1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text().strip()

        # Fallback to title tag
        if soup.title:
            return soup.title.string.strip()

        return ""

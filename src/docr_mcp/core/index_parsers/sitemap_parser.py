"""Index parser for sitemap.xml format."""

import logging
import re
from typing import List
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from docr_mcp.models import IndexEntry

logger = logging.getLogger(__name__)


class SitemapIndexParser:
    """Index parser for sitemap.xml format.

    Supports:
    - Standard sitemap.xml with <url><loc> structure
    - Simplified format with just <loc> tags
    - Extracts title from URL path
    - Generates section hierarchy from URL structure
    """

    def parse(self, content: str) -> List[IndexEntry]:
        """Parse sitemap.xml content into IndexEntry objects.

        Args:
            content: Raw sitemap.xml content

        Returns:
            List of parsed IndexEntry objects
        """
        soup = BeautifulSoup(content, "xml")
        entries = []

        # Find all <url> elements in sitemap
        url_elements = soup.find_all("url")

        if not url_elements:
            # Try simplified format with just <loc> tags
            loc_tags = soup.find_all("loc")
            url_elements = [{"loc": loc} for loc in loc_tags]

        for url_entry in url_elements:
            # Extract <loc> tag
            if isinstance(url_entry, dict):
                loc_tag = url_entry["loc"]
            else:
                loc_tag = url_entry.find("loc")

            if not loc_tag:
                continue

            url = loc_tag.get_text().strip()

            # Extract title from URL (last path segment)
            parsed = urlparse(url)
            path_parts = [p for p in parsed.path.split("/") if p]

            if not path_parts:
                # Root URL, skip or use domain as title
                continue

            title = path_parts[-1]

            # Clean up title (remove extensions and convert to readable format)
            title = re.sub(r"\.(html?|md|php)$", "", title)
            title = title.replace("-", " ").replace("_", " ")
            title = title.title()

            # Extract section from URL path (all parts except the last one)
            section = " > ".join(path_parts[:-1]) if len(path_parts) > 1 else ""

            # Extract tags from URL path components
            tags = [p.lower() for p in path_parts if len(p) > 2]

            entries.append(
                IndexEntry(
                    title=title,
                    url=url,
                    section=section,
                    tags=tags,
                )
            )

        logger.debug(f"Parsed {len(entries)} documents from sitemap.xml")
        return entries

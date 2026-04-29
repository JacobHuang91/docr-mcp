"""Index parser for llms.txt documentation index format."""

import logging
import re
from typing import Callable, List, Optional
from urllib.parse import urljoin

from docr_mcp.models import IndexEntry

logger = logging.getLogger(__name__)


class LLMsIndexParser:
    """Index parser for llms.txt format with flexible URL handling.

    Supports:
    - Hierarchical sections with ## and ### headers
    - Markdown links: * [title](url) or - [title](url)
    - Optional descriptions: * [title](url): description
    - Relative and absolute URLs
    - Customizable URL transformation
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        url_transform: Optional[Callable[[str], str]] = None,
        max_header_level: int = 3,
    ):
        """Initialize llms.txt parser.

        Args:
            base_url: Base URL for resolving relative URLs (e.g., "https://docs.example.com")
            url_transform: Optional function to transform URLs (e.g., convert relative to absolute)
            max_header_level: Maximum header level to parse (2 = ##, 3 = ###, etc.)
        """
        self.base_url = base_url
        self.url_transform = url_transform
        self.max_header_level = max_header_level

    def parse(self, content: str) -> List[IndexEntry]:
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

            # Detect section headers (## Section Name, ### Subsection, etc.)
            header_pattern = f"^(#{{{2},{self.max_header_level}}})\\s+(.+)$"
            section_match = re.match(header_pattern, line)
            if section_match:
                level = len(section_match.group(1))
                section_name = section_match.group(2)

                if level == 2:
                    # Top-level section (##)
                    current_section = [section_name]
                    section_stack = [(0, section_name)]
                else:
                    # Subsection (### or deeper)
                    # Add to current hierarchy
                    if len(current_section) >= level - 2:
                        # Replace at this level
                        current_section = current_section[: level - 2] + [section_name]
                    else:
                        # Add new level
                        current_section.append(section_name)
                    section_stack = [(i, s) for i, s in enumerate(current_section)]
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

                # Transform URL if needed
                doc_url = self._process_url(doc_url)

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

        logger.debug(f"Parsed {len(docs)} documents from llms.txt")
        return docs

    def _process_url(self, url: str) -> str:
        """Process URL with custom transformation or base URL resolution.

        Args:
            url: Raw URL from llms.txt

        Returns:
            Processed URL
        """
        # Apply custom transformation if provided
        if self.url_transform:
            return self.url_transform(url)

        # Resolve relative URLs against base URL
        if self.base_url and not url.startswith(("http://", "https://")):
            return urljoin(self.base_url, url)

        return url

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

"""Base docr interface."""

from abc import ABC, abstractmethod
from typing import List

from docr_mcp.models import Document, IndexConfig, IndexEntry


class BaseDocr(ABC):
    """Base interface that all docrs must implement.

    Docrs handle fetching and parsing documentation from specific sources.
    For docrs that need authentication, implement your own HTTP client setup in __init__.
    """

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

    def close(self):
        """Close and cleanup resources.

        Override this method in subclasses that need cleanup.
        Default implementation does nothing.
        """
        return None  # Default: no cleanup needed

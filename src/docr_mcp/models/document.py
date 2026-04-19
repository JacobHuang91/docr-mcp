"""Type definitions for docr-mcp."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IndexEntry(BaseModel):
    """Represents an entry from the documentation index.

    This is the standard format that parsers' fetch_index() should return.
    Contains lightweight metadata for search but not the full content.
    """

    title: str = Field(..., description="Entry title")
    url: str = Field(..., description="Full URL to the documentation page")
    section: str = Field(default="", description="Section hierarchy (e.g., 'User Guide > Concepts > Agents')")
    tags: List[str] = Field(default_factory=list, description="Searchable tags extracted from title and section")
    description: Optional[str] = Field(default=None, description="Optional brief description")

    model_config = {"frozen": False}


class Document(BaseModel):
    """Represents a fetched documentation page with full content.

    This is what parsers' fetch_content() should return.
    """

    url: str = Field(..., description="URL of the fetched document")
    content: str = Field(..., description="Full document content (usually markdown)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata (title, format, etc.)")

    model_config = {"frozen": False}


class SearchResult(BaseModel):
    """Represents a search result with relevance score."""

    title: str = Field(..., description="Document title")
    url: str = Field(..., description="Document URL")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0.0-1.0)")
    section: str = Field(default="", description="Section hierarchy")

    model_config = {"frozen": True}  # Search results are immutable

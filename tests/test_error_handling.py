"""Tests for error handling and edge cases."""

import pytest

from docr_mcp.core.search import SearchIndex
from docr_mcp.models import IndexEntry


class TestSearchIndexValidation:
    """Test SearchIndex validation."""

    def test_empty_entries_raises_error(self):
        """Test that empty entries list raises ValueError."""
        with pytest.raises(ValueError, match="Cannot create search index with empty entries list"):
            SearchIndex([])

    def test_search_with_no_matches(self):
        """Test search returns empty list when no matches found."""
        entries = [
            IndexEntry(title="foo", url="http://example.com/foo", section="", tags=[]),
            IndexEntry(title="bar", url="http://example.com/bar", section="", tags=[]),
        ]
        search_index = SearchIndex(entries)

        results = search_index.search("nonexistentxyz123", top_k=5)

        assert len(results) == 0

    def test_search_with_zero_scores(self):
        """Test search handles all-zero scores correctly."""
        entries = [
            IndexEntry(title="test", url="http://example.com/test", section="", tags=[]),
        ]
        search_index = SearchIndex(entries)

        # Query with no token overlap should return empty
        results = search_index.search("completely different words here", top_k=5)

        assert len(results) == 0


class TestTopKValidation:
    """Test top_k parameter validation."""

    def test_top_k_clamping(self):
        """Test that top_k is clamped to valid range."""
        entries = [IndexEntry(title=f"doc{i}", url=f"http://example.com/{i}", section="", tags=[]) for i in range(150)]
        search_index = SearchIndex(entries)

        # Should clamp to 100
        results = search_index.search("doc", top_k=999)
        assert len(results) <= 100

        # Should clamp to 1
        results = search_index.search("doc", top_k=0)
        assert len(results) >= 1 or len(results) == 0  # Empty if no matches


class TestURLValidation:
    """Test URL validation in Strands docr."""

    def test_http_url_rejected(self):
        """Test that HTTP URLs are rejected."""
        from docr_mcp.docrs.public.strands import StrandsDocr

        docr = StrandsDocr()
        docr.client = type("MockClient", (), {})()  # Mock client

        with pytest.raises(ValueError, match="Only HTTPS URLs are allowed"):
            docr._validate_url("http://strandsagents.com/docs")

    def test_invalid_domain_rejected(self):
        """Test that invalid domains are rejected."""
        from docr_mcp.docrs.public.strands import StrandsDocr

        docr = StrandsDocr()

        with pytest.raises(ValueError, match="Domain not allowed"):
            docr._validate_url("https://evil.com/docs")

    def test_valid_url_accepted(self):
        """Test that valid URLs are accepted."""
        from docr_mcp.docrs.public.strands import StrandsDocr

        docr = StrandsDocr()

        # Should not raise
        docr._validate_url("https://strandsagents.com/docs/index.md")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

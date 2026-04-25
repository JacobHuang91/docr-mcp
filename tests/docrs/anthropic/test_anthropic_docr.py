"""Tests for Anthropic docr."""

import pytest

from docr_mcp.core.search import SearchIndex
from docr_mcp.docrs.anthropic import AnthropicDocr
from docr_mcp.models import IndexConfig


@pytest.fixture(scope="module")
def anthropic_docs():
    """Fetch real Anthropic documentation index once for all tests."""
    docr = AnthropicDocr()
    with docr:
        config = IndexConfig(source="https://platform.claude.com/llms.txt")
        return docr.fetch_index_entries(config)


class TestAnthropicDocr:
    """Test cases for Anthropic docr."""

    def test_fetch_real_index(self, anthropic_docs):
        """Test fetching real llms.txt from live Anthropic site."""
        docs = anthropic_docs

        # Verify we got documents (Anthropic has 1200+ entries)
        assert len(docs) > 1200, f"Expected 1200+ documents, got {len(docs)}"

        # Check documents have expected structure
        for doc in docs[:5]:
            assert doc.title
            assert doc.url
            assert doc.url.startswith("https://")
            assert hasattr(doc, "section")
            assert hasattr(doc, "tags")

    def test_absolute_url_format(self, anthropic_docs):
        """Test that URLs are already absolute (no conversion needed)."""
        docs = anthropic_docs

        # All URLs should be absolute
        for doc in docs[:10]:
            assert doc.url.startswith("https://platform.claude.com/"), f"Expected absolute URL, got {doc.url}"

    def test_section_hierarchy(self, anthropic_docs):
        """Test that section hierarchy is correctly tracked."""
        docs = anthropic_docs

        # Check if sections exist
        sections = {d.section for d in docs}
        assert len(sections) > 0, "Should have multiple sections"

    def test_tags_extraction(self, anthropic_docs):
        """Test that tags are correctly extracted from titles and sections."""
        docs = anthropic_docs

        # Check that docs have tags
        docs_with_tags = [d for d in docs if len(d.tags) > 0]
        assert len(docs_with_tags) > 0, "Should have documents with tags"

    def test_url_validation(self):
        """Test URL validation for Anthropic docs."""
        docr = AnthropicDocr()

        # Valid Anthropic URL
        docr._validate_url("https://platform.claude.com/docs")

        # Invalid scheme
        with pytest.raises(ValueError, match="HTTPS"):
            docr._validate_url("http://platform.claude.com/docs")

        # Invalid domain
        with pytest.raises(ValueError, match="not allowed"):
            docr._validate_url("https://evil.com/docs")

    def test_fetch_real_doc_content(self):
        """Test fetching real documentation page content."""
        docr = AnthropicDocr()
        with docr:
            # Get index first
            config = IndexConfig(source="https://platform.claude.com/llms.txt")
            docs = docr.fetch_index_entries(config)

            # Fetch first 3 docs to verify content fetching works
            for doc in docs[:3]:
                content = docr.fetch_content(doc.url)
                assert content.url == doc.url
                assert len(content.content) > 0, f"Should fetch content for {doc.url}"
                assert content.metadata["source"] == "anthropic"
                # Format can be either markdown or html depending on availability
                assert content.metadata["format"] in ["markdown", "html"]


class TestSearchWithAnthropic:
    """Test search functionality with Anthropic documents."""

    def test_search_by_title(self, anthropic_docs):
        """Test searching by title."""
        docs = anthropic_docs
        search_index = SearchIndex(docs)

        # Search for a common Anthropic term
        results = search_index.search("prompt caching", top_k=5)

        assert len(results) > 0
        # Should find prompt caching related docs
        assert any("prompt" in r["title"].lower() or "caching" in r["title"].lower() for r in results)

    def test_search_by_feature(self, anthropic_docs):
        """Test searching for Anthropic features."""
        docs = anthropic_docs
        search_index = SearchIndex(docs)

        results = search_index.search("tool use", top_k=10)

        assert len(results) > 0

    def test_search_returns_limited_results(self, anthropic_docs):
        """Test that search respects top_k limit."""
        docs = anthropic_docs
        search_index = SearchIndex(docs)

        results = search_index.search("claude", top_k=3)

        assert len(results) <= 3

    def test_search_no_match(self, anthropic_docs):
        """Test searching for something that doesn't exist."""
        docs = anthropic_docs
        search_index = SearchIndex(docs)

        results = search_index.search("nonexistentxyz123", top_k=5)

        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

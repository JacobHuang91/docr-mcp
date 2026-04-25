"""Tests for OpenAI docr."""

import pytest

from docr_mcp.core.search import SearchIndex
from docr_mcp.docrs.openai import OpenAIDocr
from docr_mcp.models import IndexConfig


@pytest.fixture(scope="module")
def openai_docs():
    """Fetch real OpenAI documentation index once for all tests."""
    docr = OpenAIDocr()
    with docr:
        config = IndexConfig(source="https://developers.openai.com/llms.txt")
        return docr.fetch_index_entries(config)


class TestOpenAIDocr:
    """Test cases for OpenAI docr."""

    def test_fetch_real_index(self, openai_docs):
        """Test fetching real llms.txt from live OpenAI site."""
        docs = openai_docs

        # Verify we got documents (OpenAI has 300+ entries)
        assert len(docs) > 300, f"Expected 300+ documents, got {len(docs)}"

        # Check documents have expected structure
        for doc in docs[:5]:
            assert doc.title
            assert doc.url
            assert doc.url.startswith("https://")
            assert hasattr(doc, "section")
            assert hasattr(doc, "tags")

    def test_absolute_url_format(self, openai_docs):
        """Test that URLs are already absolute (no conversion needed)."""
        docs = openai_docs

        # All URLs should be absolute
        for doc in docs[:10]:
            assert doc.url.startswith("https://developers.openai.com/"), f"Expected absolute URL, got {doc.url}"

    def test_section_hierarchy(self, openai_docs):
        """Test that section hierarchy is correctly tracked."""
        docs = openai_docs

        # Check if sections exist
        sections = {d.section for d in docs}
        assert len(sections) > 0, "Should have multiple sections"

    def test_tags_extraction(self, openai_docs):
        """Test that tags are correctly extracted from titles and sections."""
        docs = openai_docs

        # Check that docs have tags
        docs_with_tags = [d for d in docs if len(d.tags) > 0]
        assert len(docs_with_tags) > 0, "Should have documents with tags"

    def test_url_validation(self):
        """Test URL validation for OpenAI docs."""
        docr = OpenAIDocr()

        # Valid OpenAI URL
        docr._validate_url("https://developers.openai.com/api/docs")

        # Invalid scheme
        with pytest.raises(ValueError, match="HTTPS"):
            docr._validate_url("http://developers.openai.com/docs")

        # Invalid domain
        with pytest.raises(ValueError, match="not allowed"):
            docr._validate_url("https://evil.com/docs")

    def test_fetch_real_doc_content(self):
        """Test fetching real documentation page content."""
        docr = OpenAIDocr()
        with docr:
            # Get index first
            config = IndexConfig(source="https://developers.openai.com/llms.txt")
            docs = docr.fetch_index_entries(config)

            # Fetch first 3 docs to verify content fetching works
            for doc in docs[:3]:
                content = docr.fetch_content(doc.url)
                assert content.url == doc.url
                assert len(content.content) > 0, f"Should fetch content for {doc.url}"
                assert content.metadata["source"] == "openai"
                # Format can be either markdown or html depending on availability
                assert content.metadata["format"] in ["markdown", "html"]


class TestSearchWithOpenAI:
    """Test search functionality with OpenAI documents."""

    def test_search_by_title(self, openai_docs):
        """Test searching by title."""
        docs = openai_docs
        search_index = SearchIndex(docs)

        # Search for a common OpenAI term
        results = search_index.search("function calling", top_k=5)

        assert len(results) > 0
        # Should find function calling related docs
        assert any("function" in r["title"].lower() for r in results)

    def test_search_by_feature(self, openai_docs):
        """Test searching for OpenAI features."""
        docs = openai_docs
        search_index = SearchIndex(docs)

        results = search_index.search("agents", top_k=10)

        assert len(results) > 0

    def test_search_returns_limited_results(self, openai_docs):
        """Test that search respects top_k limit."""
        docs = openai_docs
        search_index = SearchIndex(docs)

        results = search_index.search("openai", top_k=3)

        assert len(results) <= 3

    def test_search_no_match(self, openai_docs):
        """Test searching for something that doesn't exist."""
        docs = openai_docs
        search_index = SearchIndex(docs)

        results = search_index.search("nonexistentxyz123", top_k=5)

        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

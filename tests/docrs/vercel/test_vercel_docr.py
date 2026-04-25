"""Tests for Vercel docr."""

import pytest

from docr_mcp.core.search import SearchIndex
from docr_mcp.docrs.vercel import VercelDocr
from docr_mcp.models import IndexConfig


@pytest.fixture(scope="module")
def vercel_docs():
    """Fetch real Vercel documentation index once for all tests."""
    docr = VercelDocr()
    with docr:
        config = IndexConfig(source="https://vercel.com/llms.txt")
        return docr.fetch_index_entries(config)


class TestVercelDocr:
    """Test cases for Vercel docr."""

    def test_fetch_real_index(self, vercel_docs):
        """Test fetching real llms.txt from live Vercel site."""
        docs = vercel_docs

        # Verify we got documents (Vercel has 1700+ entries)
        assert len(docs) > 1700, f"Expected 1700+ documents, got {len(docs)}"

        # Check documents have expected structure
        for doc in docs[:5]:
            assert doc.title
            assert doc.url
            assert doc.url.startswith("https://")
            assert hasattr(doc, "section")
            assert hasattr(doc, "tags")

    def test_section_hierarchy(self, vercel_docs):
        """Test that section hierarchy is correctly tracked."""
        docs = vercel_docs

        # Check sections exist
        sections = {d.section for d in docs}
        assert len(sections) > 0, "Should have multiple sections"

    def test_tags_extraction(self, vercel_docs):
        """Test that tags are correctly extracted from titles and sections."""
        docs = vercel_docs

        # Check that docs have tags
        docs_with_tags = [d for d in docs if len(d.tags) > 0]
        assert len(docs_with_tags) > 0, "Should have documents with tags"

    def test_url_validation(self):
        """Test URL validation for Vercel docs."""
        docr = VercelDocr()

        # Valid Vercel URL
        docr._validate_url("https://vercel.com/docs")

        # Invalid scheme
        with pytest.raises(ValueError, match="HTTPS"):
            docr._validate_url("http://vercel.com/docs")

        # Invalid domain
        with pytest.raises(ValueError, match="not allowed"):
            docr._validate_url("https://evil.com/docs")

    def test_fetch_real_doc_content(self):
        """Test fetching real documentation page content."""
        docr = VercelDocr()
        with docr:
            # Get index first
            config = IndexConfig(source="https://vercel.com/llms.txt")
            docs = docr.fetch_index_entries(config)

            # Fetch first 3 docs to verify content fetching works
            for doc in docs[:3]:
                content = docr.fetch_content(doc.url)
                assert content.url == doc.url
                assert len(content.content) > 0, f"Should fetch content for {doc.url}"
                assert content.metadata["source"] == "vercel"
                # Format can be either markdown or html depending on availability
                assert content.metadata["format"] in ["markdown", "html"]


class TestSearchWithVercel:
    """Test search functionality with Vercel documents."""

    def test_search_by_title(self, vercel_docs):
        """Test searching by title."""
        docs = vercel_docs
        search_index = SearchIndex(docs)

        # Search for a common Vercel term
        results = search_index.search("deploy", top_k=5)

        assert len(results) > 0
        # Should find deployment related docs
        assert any("deploy" in r["title"].lower() for r in results)

    def test_search_by_product(self, vercel_docs):
        """Test searching for Vercel products."""
        docs = vercel_docs
        search_index = SearchIndex(docs)

        results = search_index.search("next.js", top_k=10)

        assert len(results) > 0

    def test_search_returns_limited_results(self, vercel_docs):
        """Test that search respects top_k limit."""
        docs = vercel_docs
        search_index = SearchIndex(docs)

        results = search_index.search("vercel", top_k=3)

        assert len(results) <= 3

    def test_search_no_match(self, vercel_docs):
        """Test searching for something that doesn't exist."""
        docs = vercel_docs
        search_index = SearchIndex(docs)

        results = search_index.search("nonexistentxyz123", top_k=5)

        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

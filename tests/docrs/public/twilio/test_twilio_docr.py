"""Tests for Twilio docr."""

import pytest

from docr_mcp.core.search import SearchIndex
from docr_mcp.docrs.public.twilio import TwilioDocr
from docr_mcp.models import IndexConfig


@pytest.fixture(scope="module")
def twilio_docs():
    """Fetch real Twilio documentation index once for all tests."""
    docr = TwilioDocr()
    with docr:
        config = IndexConfig(source="https://www.twilio.com/docs/llms.txt")
        return docr.fetch_index_entries(config)


class TestTwilioDocr:
    """Test cases for Twilio docr."""

    def test_fetch_real_index(self, twilio_docs):
        """Test fetching real llms.txt from live Twilio site."""
        docs = twilio_docs

        # Verify we got documents (Twilio has 1100+ entries)
        assert len(docs) > 1100, f"Expected 1100+ documents, got {len(docs)}"

        # Check documents have expected structure
        for doc in docs[:5]:
            assert doc.title
            assert doc.url
            assert doc.url.startswith("https://")
            assert hasattr(doc, "section")
            assert hasattr(doc, "tags")

    def test_relative_url_conversion(self, twilio_docs):
        """Test that relative URLs are converted to absolute URLs."""
        docs = twilio_docs

        # All URLs should be absolute (Twilio uses relative paths in llms.txt)
        for doc in docs[:10]:
            assert doc.url.startswith("https://www.twilio.com/"), f"Expected absolute URL, got {doc.url}"

    def test_section_hierarchy(self, twilio_docs):
        """Test that section hierarchy is correctly tracked."""
        docs = twilio_docs

        # Check if sections exist
        sections = {d.section for d in docs}
        assert len(sections) > 0, "Should have multiple sections"

    def test_tags_extraction(self, twilio_docs):
        """Test that tags are correctly extracted from titles and sections."""
        docs = twilio_docs

        # Check that docs have tags
        docs_with_tags = [d for d in docs if len(d.tags) > 0]
        assert len(docs_with_tags) > 0, "Should have documents with tags"

    def test_url_validation(self):
        """Test URL validation for Twilio docs."""
        docr = TwilioDocr()

        # Valid Twilio URL
        docr._validate_url("https://www.twilio.com/docs/sms")

        # Invalid scheme
        with pytest.raises(ValueError, match="HTTPS"):
            docr._validate_url("http://www.twilio.com/docs")

        # Invalid domain
        with pytest.raises(ValueError, match="not allowed"):
            docr._validate_url("https://evil.com/docs")

    def test_fetch_real_doc_content(self):
        """Test fetching real documentation page content."""
        docr = TwilioDocr()
        with docr:
            # Get index first
            config = IndexConfig(source="https://www.twilio.com/docs/llms.txt")
            docs = docr.fetch_index_entries(config)

            # Fetch first 3 docs to verify content fetching works
            for doc in docs[:3]:
                content = docr.fetch_content(doc.url)
                assert content.url == doc.url
                assert len(content.content) > 0, f"Should fetch content for {doc.url}"
                assert content.metadata["source"] == "twilio"
                # Format can be either markdown or html depending on availability
                assert content.metadata["format"] in ["markdown", "html"]


class TestSearchWithTwilio:
    """Test search functionality with Twilio documents."""

    def test_search_by_title(self, twilio_docs):
        """Test searching by title."""
        docs = twilio_docs
        search_index = SearchIndex(docs)

        # Search for a common Twilio term
        results = search_index.search("SMS", top_k=5)

        assert len(results) > 0
        # Should find SMS related docs
        assert any("sms" in r["title"].lower() for r in results)

    def test_search_by_product(self, twilio_docs):
        """Test searching for Twilio product names."""
        docs = twilio_docs
        search_index = SearchIndex(docs)

        results = search_index.search("messaging", top_k=10)

        assert len(results) > 0

    def test_search_returns_limited_results(self, twilio_docs):
        """Test that search respects top_k limit."""
        docs = twilio_docs
        search_index = SearchIndex(docs)

        results = search_index.search("twilio", top_k=3)

        assert len(results) <= 3

    def test_search_no_match(self, twilio_docs):
        """Test searching for something that doesn't exist."""
        docs = twilio_docs
        search_index = SearchIndex(docs)

        results = search_index.search("nonexistentxyz123", top_k=5)

        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

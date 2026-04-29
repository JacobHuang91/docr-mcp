"""Tests for Stripe docr."""

import pytest

from docr_mcp.core.search import SearchIndex
from docr_mcp.docrs.public.stripe import StripeDocr
from docr_mcp.models import IndexConfig


@pytest.fixture(scope="module")
def stripe_docs():
    """Fetch real Stripe documentation index once for all tests."""
    docr = StripeDocr()
    with docr:
        config = IndexConfig(source="https://docs.stripe.com/llms.txt")
        return docr.fetch_index_entries(config)


class TestStripeDocr:
    """Test cases for Stripe docr."""

    def test_fetch_real_index(self, stripe_docs):
        """Test fetching real llms.txt from live Stripe site."""
        docs = stripe_docs

        # Verify we got documents (Stripe has 400+ entries)
        assert len(docs) > 400, f"Expected 400+ documents, got {len(docs)}"

        # Check documents have expected structure
        for doc in docs[:5]:
            assert doc.title
            assert doc.url
            assert doc.url.startswith("https://")
            assert hasattr(doc, "section")
            assert hasattr(doc, "tags")

    def test_absolute_url_format(self, stripe_docs):
        """Test that URLs are already absolute (no conversion needed)."""
        docs = stripe_docs

        # All URLs should be absolute
        for doc in docs[:10]:
            assert doc.url.startswith("https://docs.stripe.com/"), f"Expected absolute URL, got {doc.url}"

    def test_section_hierarchy(self, stripe_docs):
        """Test that section hierarchy is correctly tracked."""
        docs = stripe_docs

        # Check if sections exist
        sections = {d.section for d in docs}
        assert len(sections) > 0, "Should have multiple sections"

    def test_tags_extraction(self, stripe_docs):
        """Test that tags are correctly extracted from titles and sections."""
        docs = stripe_docs

        # Check that docs have tags
        docs_with_tags = [d for d in docs if len(d.tags) > 0]
        assert len(docs_with_tags) > 0, "Should have documents with tags"

    def test_url_validation(self):
        """Test URL validation for Stripe docs."""
        docr = StripeDocr()

        # Valid Stripe URL
        docr._validate_url("https://docs.stripe.com/payments")

        # Invalid scheme
        with pytest.raises(ValueError, match="HTTPS"):
            docr._validate_url("http://docs.stripe.com/payments")

        # Invalid domain
        with pytest.raises(ValueError, match="not allowed"):
            docr._validate_url("https://evil.com/docs")

    def test_fetch_real_doc_content(self):
        """Test fetching real documentation page content."""
        docr = StripeDocr()
        with docr:
            # Get index first
            config = IndexConfig(source="https://docs.stripe.com/llms.txt")
            docs = docr.fetch_index_entries(config)

            # Fetch first 3 docs to verify content fetching works
            for doc in docs[:3]:
                content = docr.fetch_content(doc.url)
                assert content.url == doc.url
                assert len(content.content) > 0, f"Should fetch content for {doc.url}"
                assert content.metadata["source"] == "stripe"
                # Format can be either markdown or html depending on availability
                assert content.metadata["format"] in ["markdown", "html"]


class TestSearchWithStripe:
    """Test search functionality with Stripe documents."""

    def test_search_by_title(self, stripe_docs):
        """Test searching by title."""
        docs = stripe_docs
        search_index = SearchIndex(docs)

        # Search for a common Stripe term
        results = search_index.search("payment", top_k=5)

        assert len(results) > 0
        # Should find payment related docs
        assert any("payment" in r["title"].lower() for r in results)

    def test_search_by_feature(self, stripe_docs):
        """Test searching for Stripe features."""
        docs = stripe_docs
        search_index = SearchIndex(docs)

        results = search_index.search("checkout", top_k=10)

        assert len(results) > 0

    def test_search_returns_limited_results(self, stripe_docs):
        """Test that search respects top_k limit."""
        docs = stripe_docs
        search_index = SearchIndex(docs)

        results = search_index.search("stripe", top_k=3)

        assert len(results) <= 3

    def test_search_no_match(self, stripe_docs):
        """Test searching for something that doesn't exist."""
        docs = stripe_docs
        search_index = SearchIndex(docs)

        results = search_index.search("nonexistentxyz123", top_k=5)

        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

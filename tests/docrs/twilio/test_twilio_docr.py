"""Tests for Twilio docr."""

from pathlib import Path

import pytest

from docr_mcp.core.search import SearchIndex
from docr_mcp.docrs.twilio import TwilioDocr
from docr_mcp.models import IndexConfig

# Path to fixtures
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "twilio"


def load_fixture(filename: str) -> str:
    """Load a test fixture file.

    Args:
        filename: Name of the fixture file

    Returns:
        File contents as string
    """
    fixture_path = FIXTURES_DIR / filename
    with open(fixture_path, "r") as f:
        return f.read()


class TestTwilioDocr:
    """Test cases for Twilio docr."""

    def test_parse_index_structure(self):
        """Test that docr correctly extracts documents with sections."""
        docr = TwilioDocr()

        # Mock the HTTP client with real fixture data
        class MockResponse:
            def __init__(self):
                self.text = load_fixture("llms.txt")

            def raise_for_status(self):
                pass

        class MockClient:
            def get(self, url):
                return MockResponse()

            def close(self):
                pass

        docr.client = MockClient()

        # Parse index
        config = IndexConfig(source="https://www.twilio.com/docs/llms.txt")
        docs = docr.fetch_index_entries(config)

        # Verify we got documents (Twilio has 1100+ entries)
        assert len(docs) > 1100, f"Should parse 1100+ documents, got {len(docs)}"

        # Check first few documents have expected structure
        for doc in docs[:5]:
            assert doc.title
            assert doc.url
            assert hasattr(doc, "section")
            assert hasattr(doc, "tags")

        # Verify URLs are absolute (not relative)
        for doc in docs[:10]:
            assert doc.url.startswith("https://"), f"Expected absolute URL, got {doc.url}"

    def test_relative_url_conversion(self):
        """Test that relative URLs are converted to absolute URLs."""
        docr = TwilioDocr()

        class MockResponse:
            def __init__(self):
                self.text = load_fixture("llms.txt")

            def raise_for_status(self):
                pass

        class MockClient:
            def get(self, url):
                return MockResponse()

            def close(self):
                pass

        docr.client = MockClient()

        config = IndexConfig(source="https://www.twilio.com/docs/llms.txt")
        docs = docr.fetch_index_entries(config)

        # All URLs should be absolute
        for doc in docs:
            assert doc.url.startswith("https://www.twilio.com/"), f"Expected absolute URL, got {doc.url}"

    def test_section_hierarchy(self):
        """Test that section hierarchy is correctly tracked."""
        docr = TwilioDocr()

        class MockResponse:
            def __init__(self):
                self.text = load_fixture("llms.txt")

            def raise_for_status(self):
                pass

        class MockClient:
            def get(self, url):
                return MockResponse()

            def close(self):
                pass

        docr.client = MockClient()

        config = IndexConfig(source="https://www.twilio.com/docs/llms.txt")
        docs = docr.fetch_index_entries(config)

        # Check if sections exist
        sections = {d.section for d in docs}
        assert len(sections) > 0

    def test_tags_extraction(self):
        """Test that tags are correctly extracted from titles and sections."""
        docr = TwilioDocr()

        class MockResponse:
            def __init__(self):
                self.text = load_fixture("llms.txt")

            def raise_for_status(self):
                pass

        class MockClient:
            def get(self, url):
                return MockResponse()

            def close(self):
                pass

        docr.client = MockClient()

        config = IndexConfig(source="https://www.twilio.com/docs/llms.txt")
        docs = docr.fetch_index_entries(config)

        # Check that docs have tags
        docs_with_tags = [d for d in docs if len(d.tags) > 0]
        assert len(docs_with_tags) > 0

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

    def test_markdown_url_handling(self):
        """Test that markdown URLs are handled correctly."""
        docr = TwilioDocr()

        class MockResponse:
            def __init__(self, url):
                self.url = url
                self.text = "# Test Content\n\nTest markdown content"

            def raise_for_status(self):
                pass

        class MockClient:
            def get(self, url):
                return MockResponse(url)

            def close(self):
                pass

        docr.client = MockClient()

        # Fetch content with .md extension (typical Twilio URL)
        doc = docr.fetch_content("https://www.twilio.com/docs/test.md")

        assert doc.url == "https://www.twilio.com/docs/test.md"
        assert doc.metadata["format"] == "markdown"
        assert "Test markdown content" in doc.content

    def test_markdown_fallback_to_html(self):
        """Test fallback to HTML when markdown is not available."""
        docr = TwilioDocr()

        class MockResponse:
            def __init__(self, url, status_code=200):
                self.url = url
                self.status_code = status_code
                if url.endswith(".md"):
                    self.text = ""
                else:
                    self.text = "<!DOCTYPE html><html><body><h1>Test HTML Content</h1></body></html>"

            def raise_for_status(self):
                if self.status_code == 404:
                    import httpx

                    raise httpx.HTTPStatusError("Not Found", request=None, response=self)

        call_count = {"count": 0}

        class MockClient:
            def get(self, url):
                call_count["count"] += 1
                if url.endswith(".md") and call_count["count"] == 1:
                    return MockResponse(url, status_code=404)
                else:
                    return MockResponse(url, status_code=200)

            def close(self):
                pass

        docr.client = MockClient()

        # Fetch content - should try .md, get 404, then fallback to HTML
        doc = docr.fetch_content("https://www.twilio.com/docs/test.md")

        assert doc.url == "https://www.twilio.com/docs/test.md"
        assert doc.metadata["format"] == "html"
        assert "Test HTML Content" in doc.content
        assert call_count["count"] == 2  # Should have tried both .md and HTML

    def test_full_real_index(self):
        """Test parsing the full real Twilio llms.txt file."""
        docr = TwilioDocr()

        class MockResponse:
            def __init__(self):
                self.text = load_fixture("llms.txt")

            def raise_for_status(self):
                pass

        class MockClient:
            def get(self, url):
                return MockResponse()

            def close(self):
                pass

        docr.client = MockClient()

        config = IndexConfig(source="https://www.twilio.com/docs/llms.txt")
        docs = docr.fetch_index_entries(config)

        # Should have all docs from real file (1100+ entries)
        assert len(docs) > 1100, f"Expected 1100+ docs, got {len(docs)}"

        # Verify some known sections exist
        sections = {d.section for d in docs}
        section_names = " ".join(sections).lower()
        # At least some common Twilio product names should appear
        assert any(keyword in section_names for keyword in ["authy", "flex", "messaging", "voice", "sms"])

        # Verify known documentation pages exist
        titles = {d.title for d in docs}
        # Should have SMS or Messaging related titles
        assert any("sms" in t.lower() or "messaging" in t.lower() for t in titles)


class TestSearchWithTwilio:
    """Test search functionality with Twilio documents."""

    def get_sample_docs(self):
        """Helper to get parsed sample documents."""
        docr = TwilioDocr()

        class MockResponse:
            def __init__(self):
                self.text = load_fixture("llms.txt")

            def raise_for_status(self):
                pass

        class MockClient:
            def get(self, url):
                return MockResponse()

            def close(self):
                pass

        docr.client = MockClient()

        config = IndexConfig(source="https://www.twilio.com/docs/llms.txt")
        return docr.fetch_index_entries(config)

    def test_search_by_title(self):
        """Test searching by title."""
        docs = self.get_sample_docs()
        search_index = SearchIndex(docs)

        # Search for a common Twilio term
        results = search_index.search("SMS", top_k=5)

        assert len(results) > 0
        # Should find SMS related docs
        assert any("sms" in r["title"].lower() for r in results)

    def test_search_by_product(self):
        """Test searching for Twilio product names."""
        docs = self.get_sample_docs()
        search_index = SearchIndex(docs)

        results = search_index.search("messaging", top_k=10)

        assert len(results) > 0

    def test_search_returns_limited_results(self):
        """Test that search respects top_k limit."""
        docs = self.get_sample_docs()
        search_index = SearchIndex(docs)

        results = search_index.search("twilio", top_k=3)

        assert len(results) <= 3

    def test_search_no_match(self):
        """Test searching for something that doesn't exist."""
        docs = self.get_sample_docs()
        search_index = SearchIndex(docs)

        results = search_index.search("nonexistentxyz123", top_k=5)

        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

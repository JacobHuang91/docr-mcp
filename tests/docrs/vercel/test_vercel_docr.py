"""Tests for Vercel docr."""

from pathlib import Path

import pytest

from docr_mcp.core.search import SearchIndex
from docr_mcp.docrs.vercel import VercelDocr
from docr_mcp.models import IndexConfig

# Path to fixtures
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "vercel"


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


class TestVercelDocr:
    """Test cases for Vercel docr."""

    def test_parse_index_structure(self):
        """Test that docr correctly extracts documents with sections."""
        docr = VercelDocr()

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
        config = IndexConfig(source="https://vercel.com/llms.txt")
        docs = docr.fetch_index_entries(config)

        # Verify we got documents (full llms.txt has 1700+ entries)
        assert len(docs) > 1700, f"Should parse 1700+ documents, got {len(docs)}"

        # Check first few documents have expected structure
        for doc in docs[:5]:
            assert doc.title
            assert doc.url
            assert hasattr(doc, "section")
            assert hasattr(doc, "tags")

    def test_section_hierarchy(self):
        """Test that section hierarchy is correctly tracked."""
        docr = VercelDocr()

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

        config = IndexConfig(source="https://vercel.com/llms.txt")
        docs = docr.fetch_index_entries(config)

        # Find specific documents and check their sections
        # Check if Next.js framework exists
        nextjs = next((d for d in docs if "Next.js" in d.title), None)
        if nextjs:
            # Should have section hierarchy
            assert len(nextjs.section) > 0

        # Check for framework-related sections
        sections = {d.section for d in docs}
        assert len(sections) > 0

    def test_tags_extraction(self):
        """Test that tags are correctly extracted from titles and sections."""
        docr = VercelDocr()

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

        config = IndexConfig(source="https://vercel.com/llms.txt")
        docs = docr.fetch_index_entries(config)

        # Check that docs have tags
        docs_with_tags = [d for d in docs if len(d.tags) > 0]
        assert len(docs_with_tags) > 0

        # Check a specific doc has relevant tags
        if docs:
            first_doc = docs[0]
            assert len(first_doc.tags) > 0

    def test_url_validation(self):
        """Test URL validation for Vercel docs."""
        docr = VercelDocr()

        # Valid Vercel URL
        docr._validate_url("https://vercel.com/docs/frameworks")

        # Invalid scheme
        with pytest.raises(ValueError, match="HTTPS"):
            docr._validate_url("http://vercel.com/docs")

        # Invalid domain
        with pytest.raises(ValueError, match="not allowed"):
            docr._validate_url("https://evil.com/docs")

    def test_markdown_url_conversion(self):
        """Test that HTML URLs are converted to markdown URLs."""
        docr = VercelDocr()

        class MockResponse:
            def __init__(self, url):
                # Verify .md was appended
                assert url.endswith(".md"), f"Expected markdown URL, got {url}"
                self.text = "# Test Content\n\nTest markdown content"

            def raise_for_status(self):
                pass

        class MockClient:
            def get(self, url):
                return MockResponse(url)

            def close(self):
                pass

        docr.client = MockClient()

        # Fetch content - should append .md
        doc = docr.fetch_content("https://vercel.com/docs/test")

        assert doc.url == "https://vercel.com/docs/test"
        assert doc.metadata["format"] == "markdown"
        assert "Test markdown content" in doc.content

    def test_markdown_fallback_to_html(self):
        """Test fallback to HTML when markdown is not available."""
        docr = VercelDocr()

        class MockResponse:
            def __init__(self, url, status_code=200):
                self.url = url
                self.status_code = status_code
                if url.endswith(".md"):
                    # Simulate 404 for markdown
                    self.text = ""
                else:
                    # Return HTML for non-.md URLs
                    self.text = "<!DOCTYPE html><html><body><h1>Test HTML Content</h1></body></html>"

            def raise_for_status(self):
                if self.status_code == 404:
                    import httpx

                    raise httpx.HTTPStatusError("Not Found", request=None, response=self)

        call_count = {"count": 0}

        class MockClient:
            def get(self, url):
                call_count["count"] += 1
                if url.endswith(".md"):
                    # First call: markdown 404
                    return MockResponse(url, status_code=404)
                else:
                    # Second call: HTML success
                    return MockResponse(url, status_code=200)

            def close(self):
                pass

        docr.client = MockClient()

        # Fetch content - should try .md, get 404, then fallback to HTML
        doc = docr.fetch_content("https://vercel.com/docs/test")

        assert doc.url == "https://vercel.com/docs/test"
        assert doc.metadata["format"] == "html"
        assert "Test HTML Content" in doc.content
        assert call_count["count"] == 2  # Should have tried both .md and HTML

    def test_full_real_index(self):
        """Test parsing the full real Vercel llms.txt file."""
        docr = VercelDocr()

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

        config = IndexConfig(source="https://vercel.com/llms.txt")
        docs = docr.fetch_index_entries(config)

        # Should have all docs from real file (1742 entries as of 2024)
        assert len(docs) > 1700, f"Expected 1700+ docs, got {len(docs)}"

        # Verify some known sections exist
        sections = {d.section for d in docs}
        # Check for actual sections that exist in Vercel's llms.txt
        assert any("Build & Deploy" in s for s in sections)
        assert any("CDN" in s for s in sections)
        assert any("AI" in s for s in sections)

        # Verify known documentation pages exist
        titles = {d.title for d in docs}
        assert any("Next.js" in t for t in titles)
        assert any("Getting Started" in t for t in titles)


class TestSearchWithVercel:
    """Test search functionality with Vercel documents."""

    def get_sample_docs(self):
        """Helper to get parsed sample documents."""
        docr = VercelDocr()

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

        config = IndexConfig(source="https://vercel.com/llms.txt")
        return docr.fetch_index_entries(config)

    def test_search_by_title(self):
        """Test searching by title."""
        docs = self.get_sample_docs()
        search_index = SearchIndex(docs)

        # Search for a common term in Vercel docs
        results = search_index.search("Next.js", top_k=5)

        assert len(results) > 0
        # Should find Next.js related docs
        assert any("next" in r["title"].lower() for r in results)

    def test_search_by_framework(self):
        """Test searching for framework names."""
        docs = self.get_sample_docs()
        search_index = SearchIndex(docs)

        results = search_index.search("framework", top_k=10)

        assert len(results) > 0

    def test_search_returns_limited_results(self):
        """Test that search respects top_k limit."""
        docs = self.get_sample_docs()
        search_index = SearchIndex(docs)

        results = search_index.search("vercel", top_k=3)

        assert len(results) <= 3

    def test_search_no_match(self):
        """Test searching for something that doesn't exist."""
        docs = self.get_sample_docs()
        search_index = SearchIndex(docs)

        results = search_index.search("nonexistentxyz123", top_k=5)

        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

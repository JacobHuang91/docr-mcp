"""Tests for Strands parser."""

from pathlib import Path

import pytest

from docr_mcp.core.search import SearchIndex
from docr_mcp.docrs.strands import StrandsDocr
from docr_mcp.models import IndexConfig

# Path to fixtures
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "strands"


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


class TestStrandsDocr:
    """Test cases for Strands docr."""

    def test_parse_index_structure(self):
        """Test that docr correctly extracts documents with sections."""
        docr = StrandsDocr()

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
        config = IndexConfig(source="https://strandsagents.com/llms.txt")
        docs = docr.fetch_index_entries(config)

        # Verify we got documents
        assert len(docs) > 0, "Should parse at least one document"

        # Check first few documents have expected structure
        for doc in docs[:5]:
            assert doc.title
            assert doc.url
            assert hasattr(doc, "section")
            assert hasattr(doc, "tags")

    def test_section_hierarchy(self):
        """Test that section hierarchy is correctly tracked."""
        docr = StrandsDocr()

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

        config = IndexConfig(source="https://strandsagents.com/llms.txt")
        docs = docr.fetch_index_entries(config)

        # Find specific documents and check their sections
        agent_loop = next((d for d in docs if d.title == "agent-loop"), None)
        assert agent_loop is not None
        # Section should include the hierarchy
        assert "Concepts" in agent_loop.section
        assert "Agents" in agent_loop.section

        # Check nested tools
        mcp_tools = next((d for d in docs if d.title == "mcp-tools"), None)
        assert mcp_tools is not None
        assert "Tools" in mcp_tools.section

        # Check examples section
        weather = next((d for d in docs if d.title == "weather_forecaster"), None)
        assert weather is not None
        assert "Examples" in weather.section

    def test_tags_extraction(self):
        """Test that tags are correctly extracted from titles and sections."""
        docr = StrandsDocr()

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

        config = IndexConfig(source="https://strandsagents.com/llms.txt")
        docs = docr.fetch_index_entries(config)

        # Check agent-loop has relevant tags
        agent_loop = next((d for d in docs if d.title == "agent-loop"), None)
        assert agent_loop is not None
        assert len(agent_loop.tags) > 0
        # Should include section parts
        tag_lower = [t.lower() for t in agent_loop.tags]
        assert "concepts" in tag_lower
        assert "agents" in tag_lower

    def test_full_real_index(self):
        """Test parsing the full real Strands llms.txt file."""
        docr = StrandsDocr()

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

        config = IndexConfig(source="https://strandsagents.com/llms.txt")
        docs = docr.fetch_index_entries(config)

        # Should have all the docs from real file (420+)
        assert len(docs) > 400, f"Expected 400+ docs, got {len(docs)}"

        # Verify some known sections exist
        sections = {d.section for d in docs}
        assert any("User Guide" in s for s in sections)
        assert any("Examples" in s for s in sections)
        assert any("Api Python" in s for s in sections)


class TestSearchWithStrands:
    """Test search functionality with Strands documents."""

    def get_sample_docs(self):
        """Helper to get parsed sample documents."""
        docr = StrandsDocr()

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

        config = IndexConfig(source="https://strandsagents.com/llms.txt")
        return docr.fetch_index_entries(config)

    def test_search_by_title(self):
        """Test searching by exact title match."""
        docs = self.get_sample_docs()
        search_index = SearchIndex(docs)

        results = search_index.search("agent-loop", top_k=5)

        assert len(results) > 0
        # Exact match should be first
        assert results[0]["title"] == "agent-loop"
        assert results[0]["score"] >= 0.8

    def test_search_by_partial_title(self):
        """Test searching with partial title."""
        docs = self.get_sample_docs()
        search_index = SearchIndex(docs)

        results = search_index.search("agent", top_k=10)

        assert len(results) > 0
        # Should find multiple agent-related docs
        titles = [r["title"] for r in results]
        assert any("agent" in t.lower() for t in titles)

    def test_search_by_section(self):
        """Test searching by section name."""
        docs = self.get_sample_docs()
        search_index = SearchIndex(docs)

        results = search_index.search("tools", top_k=10)

        assert len(results) > 0
        # Should find docs in Tools section
        for result in results[:5]:
            assert "tools" in result["title"].lower() or "tools" in result["section"].lower()

    def test_search_multi_word(self):
        """Test searching with multiple words."""
        docs = self.get_sample_docs()
        search_index = SearchIndex(docs)

        results = search_index.search("model providers", top_k=10)

        assert len(results) > 0
        # Should find model provider docs
        assert any("model" in r["title"].lower() or "providers" in r["title"].lower() for r in results)

    def test_search_returns_limited_results(self):
        """Test that search respects top_k limit."""
        docs = self.get_sample_docs()
        search_index = SearchIndex(docs)

        results = search_index.search("agent", top_k=3)

        assert len(results) <= 3

    def test_search_no_match(self):
        """Test searching for something that doesn't exist."""
        docs = self.get_sample_docs()
        search_index = SearchIndex(docs)

        results = search_index.search("nonexistentxyz123", top_k=5)

        assert len(results) == 0

    def test_search_tag_matching(self):
        """Test that search matches tags."""
        docs = self.get_sample_docs()
        search_index = SearchIndex(docs)

        # Search for something that should be in tags
        results = search_index.search("anthropic", top_k=10)

        assert len(results) > 0
        # Should find anthropic-related docs
        assert any("anthropic" in r["title"].lower() for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

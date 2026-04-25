"""Tests for Strands parser."""

import pytest

from docr_mcp.core.search import SearchIndex
from docr_mcp.docrs.strands import StrandsDocr
from docr_mcp.models import IndexConfig


@pytest.fixture(scope="module")
def strands_docs():
    """Fetch real Strands documentation index once for all tests."""
    docr = StrandsDocr()
    with docr:
        config = IndexConfig(source="https://strandsagents.com/llms.txt")
        return docr.fetch_index_entries(config)


class TestStrandsDocr:
    """Test cases for Strands docr."""

    def test_fetch_real_index(self, strands_docs):
        """Test fetching real llms.txt from live Strands site."""
        docs = strands_docs

        # Verify we got documents (Strands has 400+ entries)
        assert len(docs) > 400, f"Expected 400+ documents, got {len(docs)}"

        # Check documents have expected structure
        for doc in docs[:5]:
            assert doc.title
            assert doc.url
            assert doc.url.startswith("https://")
            assert hasattr(doc, "section")
            assert hasattr(doc, "tags")

    def test_section_hierarchy(self, strands_docs):
        """Test that section hierarchy is correctly tracked."""
        docs = strands_docs

        # Find specific documents and check their sections
        agent_loop = next((d for d in docs if d.title == "agent-loop"), None)
        assert agent_loop is not None, "Should find agent-loop document"
        # Section should include the hierarchy
        assert "Concepts" in agent_loop.section
        assert "Agents" in agent_loop.section

        # Check nested tools
        mcp_tools = next((d for d in docs if d.title == "mcp-tools"), None)
        assert mcp_tools is not None, "Should find mcp-tools document"
        assert "Tools" in mcp_tools.section

        # Check examples section
        weather = next((d for d in docs if d.title == "weather_forecaster"), None)
        assert weather is not None, "Should find weather_forecaster example"
        assert "Examples" in weather.section

    def test_tags_extraction(self, strands_docs):
        """Test that tags are correctly extracted from titles and sections."""
        docs = strands_docs

        # Check agent-loop has relevant tags
        agent_loop = next((d for d in docs if d.title == "agent-loop"), None)
        assert agent_loop is not None
        assert len(agent_loop.tags) > 0
        # Should include section parts
        tag_lower = [t.lower() for t in agent_loop.tags]
        assert "concepts" in tag_lower
        assert "agents" in tag_lower

    def test_known_sections_exist(self, strands_docs):
        """Test that known sections exist in the real documentation."""
        docs = strands_docs

        # Verify some known sections exist
        sections = {d.section for d in docs}
        assert any("User Guide" in s for s in sections), "Should have User Guide section"
        assert any("Examples" in s for s in sections), "Should have Examples section"
        assert any("Api Python" in s for s in sections), "Should have Api Python section"

    def test_fetch_real_doc_content(self):
        """Test fetching real documentation page content."""
        docr = StrandsDocr()
        with docr:
            # Get index first
            config = IndexConfig(source="https://strandsagents.com/llms.txt")
            docs = docr.fetch_index_entries(config)

            # Fetch first 3 docs to verify content fetching works
            for doc in docs[:3]:
                content = docr.fetch_content(doc.url)
                assert content.url == doc.url
                assert len(content.content) > 0, f"Should fetch content for {doc.url}"
                assert content.metadata["source"] == "strands"
                assert content.metadata["format"] == "markdown"


class TestSearchWithStrands:
    """Test search functionality with Strands documents."""

    def test_search_by_title(self, strands_docs):
        """Test searching by exact title match."""
        docs = strands_docs
        search_index = SearchIndex(docs)

        results = search_index.search("agent-loop", top_k=5)

        assert len(results) > 0
        # Exact match should be first
        assert results[0]["title"] == "agent-loop"
        assert results[0]["score"] >= 0.8

    def test_search_by_partial_title(self, strands_docs):
        """Test searching with partial title."""
        docs = strands_docs
        search_index = SearchIndex(docs)

        results = search_index.search("agent", top_k=10)

        assert len(results) > 0
        # Should find multiple agent-related docs
        titles = [r["title"] for r in results]
        assert any("agent" in t.lower() for t in titles)

    def test_search_by_section(self, strands_docs):
        """Test searching by section name."""
        docs = strands_docs
        search_index = SearchIndex(docs)

        results = search_index.search("tools", top_k=10)

        assert len(results) > 0
        # Should find docs in Tools section
        for result in results[:5]:
            assert "tools" in result["title"].lower() or "tools" in result["section"].lower()

    def test_search_multi_word(self, strands_docs):
        """Test searching with multiple words."""
        docs = strands_docs
        search_index = SearchIndex(docs)

        results = search_index.search("model providers", top_k=10)

        assert len(results) > 0
        # Should find model provider docs
        assert any("model" in r["title"].lower() or "providers" in r["title"].lower() for r in results)

    def test_search_returns_limited_results(self, strands_docs):
        """Test that search respects top_k limit."""
        docs = strands_docs
        search_index = SearchIndex(docs)

        results = search_index.search("agent", top_k=3)

        assert len(results) <= 3

    def test_search_no_match(self, strands_docs):
        """Test searching for something that doesn't exist."""
        docs = strands_docs
        search_index = SearchIndex(docs)

        results = search_index.search("nonexistentxyz123", top_k=5)

        assert len(results) == 0

    def test_search_tag_matching(self, strands_docs):
        """Test that search matches tags."""
        docs = strands_docs
        search_index = SearchIndex(docs)

        # Search for something that should be in tags
        results = search_index.search("anthropic", top_k=10)

        assert len(results) > 0
        # Should find anthropic-related docs
        assert any("anthropic" in r["title"].lower() for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

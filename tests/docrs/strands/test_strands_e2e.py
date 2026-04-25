"""End-to-end tests for Strands docr."""

import pytest

from docr_mcp.core.search import SearchIndex
from docr_mcp.docrs.strands import StrandsDocr
from docr_mcp.models import IndexConfig


class TestStrandsE2E:
    """E2E tests simulating real MCP workflow: question → search → fetch content."""

    def test_agent_loop_workflow(self):
        """Test full workflow: ask about agent-loop, search, fetch content."""
        # Step 1: User asks "how does agent-loop work in Strands?"
        query = "agent-loop"

        # Step 2: Fetch and search index (like search_docs tool)
        docr = StrandsDocr()
        with docr:
            config = IndexConfig(source="https://strandsagents.com/llms.txt")
            docs = docr.fetch_index_entries(config)

            search_index = SearchIndex(docs)
            results = search_index.search(query, top_k=3)

            # Should find agent-loop docs
            assert len(results) > 0, "Should find results for agent-loop"
            assert results[0]["title"] == "agent-loop", "Exact match should be first"

            # Step 3: Fetch actual doc content (like fetch_doc tool)
            doc_url = results[0]["url"]
            content = docr.fetch_content(doc_url)

            # Step 4: Verify we got useful content
            assert len(content.content) > 0, "Should fetch doc content"
            assert content.metadata["format"] == "markdown"
            assert "agent-loop" in content.content.lower() or "agent loop" in content.content.lower()

    def test_model_providers_workflow(self):
        """Test workflow: ask about model providers."""
        query = "model providers"

        docr = StrandsDocr()
        with docr:
            config = IndexConfig(source="https://strandsagents.com/llms.txt")
            docs = docr.fetch_index_entries(config)

            search_index = SearchIndex(docs)
            results = search_index.search(query, top_k=3)

            assert len(results) > 0, "Should find model provider docs"

            # Fetch top result
            doc_url = results[0]["url"]
            content = docr.fetch_content(doc_url)

            assert len(content.content) > 0, "Should fetch content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

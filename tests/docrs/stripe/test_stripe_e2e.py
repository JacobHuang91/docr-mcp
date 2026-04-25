"""End-to-end tests for Stripe docr."""

import pytest

from docr_mcp.core.search import SearchIndex
from docr_mcp.docrs.stripe import StripeDocr
from docr_mcp.models import IndexConfig


class TestStripeE2E:
    """E2E tests simulating real MCP workflow: question → search → fetch content."""

    def test_payment_workflow(self):
        """Test full workflow: ask about payments."""
        query = "accept payments"

        docr = StripeDocr()
        with docr:
            config = IndexConfig(source="https://docs.stripe.com/llms.txt")
            docs = docr.fetch_index_entries(config)

            search_index = SearchIndex(docs)
            results = search_index.search(query, top_k=3)

            assert len(results) > 0, "Should find payment docs"

            # Fetch top result
            doc_url = results[0]["url"]
            content = docr.fetch_content(doc_url)

            assert len(content.content) > 0, "Should fetch content"
            assert content.metadata["format"] in ["markdown", "html"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

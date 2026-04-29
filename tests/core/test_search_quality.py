"""Tests for search quality and BM25 algorithm effectiveness."""

import pytest

from docr_mcp.core.search import SearchIndex
from docr_mcp.docrs.public.strands import StrandsDocr
from docr_mcp.models import IndexConfig


@pytest.fixture(scope="module")
def strands_entries():
    """Fetch real Strands entries for testing search quality."""
    docr = StrandsDocr()
    with docr:
        config = IndexConfig(source="https://strandsagents.com/llms.txt")
        return docr.fetch_index_entries(config)


class TestBM25SearchQuality:
    """Test BM25 search algorithm quality with real documentation."""

    def test_exact_title_match(self, strands_entries):
        """Test that exact title matches rank highest."""
        search_index = SearchIndex(strands_entries)

        # Search for exact title
        results = search_index.search("agent-loop", top_k=5)

        assert len(results) > 0
        # Exact match should be first
        assert results[0]["title"] == "agent-loop"
        # Should have high score (BM25 should rank exact matches highly)
        assert results[0]["score"] > 0.7

    def test_partial_title_match(self, strands_entries):
        """Test partial title matching."""
        search_index = SearchIndex(strands_entries)

        results = search_index.search("agent", top_k=10)

        assert len(results) > 0
        # Should find multiple agent-related docs
        titles = [r["title"].lower() for r in results]
        assert any("agent" in t for t in titles)

    def test_multi_word_query(self, strands_entries):
        """Test that multi-word queries work well."""
        search_index = SearchIndex(strands_entries)

        results = search_index.search("model providers", top_k=10)

        assert len(results) > 0
        # Should rank docs with both words higher
        first_result = results[0]
        title_lower = first_result["title"].lower()
        # At least one word should match in top result
        assert "model" in title_lower or "provider" in title_lower

    def test_camel_case_handling(self, strands_entries):
        """Test that camelCase is properly tokenized."""
        search_index = SearchIndex(strands_entries)

        # Search for "model" should match "modelProviders"
        results = search_index.search("model", top_k=20)

        assert len(results) > 0
        # Should find entries with "model" in camelCase
        titles = [r["title"] for r in results]
        # Check that we find model-related entries
        model_entries = [t for t in titles if "model" in t.lower()]
        assert len(model_entries) > 0

    def test_snake_case_handling(self, strands_entries):
        """Test that snake_case is properly tokenized."""
        search_index = SearchIndex(strands_entries)

        # Search for "agent" should match "agent_loop"
        results = search_index.search("agent loop", top_k=10)

        assert len(results) > 0
        # Should find agent-loop or agent_loop entries
        titles = [r["title"].lower() for r in results]
        assert any("agent" in t and "loop" in t for t in titles)

    def test_tag_matching(self, strands_entries):
        """Test that tags contribute to search relevance."""
        search_index = SearchIndex(strands_entries)

        # Search for "anthropic" which appears in tags
        results = search_index.search("anthropic", top_k=10)

        assert len(results) > 0
        # Should find anthropic-related docs
        assert any("anthropic" in r["title"].lower() for r in results)

    def test_section_matching(self, strands_entries):
        """Test that section hierarchy contributes to search."""
        search_index = SearchIndex(strands_entries)

        # Search for section name
        results = search_index.search("examples", top_k=10)

        assert len(results) > 0
        # Should find docs in Examples section
        assert any("examples" in r["section"].lower() for r in results)

    def test_relevance_ranking(self, strands_entries):
        """Test that more relevant results rank higher."""
        search_index = SearchIndex(strands_entries)

        results = search_index.search("mcp tools", top_k=10)

        assert len(results) > 0
        # Results should be sorted by score descending
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

        # Top result should have both words ideally
        top_title = results[0]["title"].lower()
        # At least the first result should be highly relevant
        assert "mcp" in top_title or "tool" in top_title

    def test_no_results_for_nonexistent(self, strands_entries):
        """Test that nonexistent queries return empty results."""
        search_index = SearchIndex(strands_entries)

        results = search_index.search("nonexistentxyz123foobarbaz", top_k=5)

        assert len(results) == 0

    def test_top_k_limit(self, strands_entries):
        """Test that top_k parameter is respected."""
        search_index = SearchIndex(strands_entries)

        results = search_index.search("agent", top_k=3)

        assert len(results) <= 3

    def test_natural_language_query(self, strands_entries):
        """Test natural language queries (LLM-style)."""
        search_index = SearchIndex(strands_entries)

        # LLM might ask: "how to use agents in strands"
        results = search_index.search("how to use agents", top_k=10)

        assert len(results) > 0
        # Should find agent-related docs
        assert any("agent" in r["title"].lower() for r in results)

    def test_technical_term_precision(self, strands_entries):
        """Test that technical terms are preserved (no stemming)."""
        search_index = SearchIndex(strands_entries)

        # Search for specific technical term
        results = search_index.search("api", top_k=10)

        assert len(results) > 0
        # Should find API-related docs
        titles = [r["title"].lower() for r in results]
        sections = [r["section"].lower() for r in results]
        assert any("api" in t or "api" in s for t, s in zip(titles, sections, strict=True))

    def test_score_normalization(self, strands_entries):
        """Test that scores are normalized between 0 and 1."""
        search_index = SearchIndex(strands_entries)

        results = search_index.search("agent", top_k=10)

        for result in results:
            assert 0.0 <= result["score"] <= 1.0, f"Score {result['score']} out of range for {result['title']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

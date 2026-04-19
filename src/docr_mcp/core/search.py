"""Search implementation using BM25 algorithm for documentation."""

import logging
import re
from typing import Any, Dict, List

from rank_bm25 import BM25Okapi

from docr_mcp.models import IndexEntry, SearchResult

logger = logging.getLogger(__name__)


class SearchIndex:
    """BM25-based search index with field weighting for documentation."""

    def __init__(self, entries: List[IndexEntry]):
        """Initialize BM25 search index.

        Args:
            entries: List of IndexEntry objects from parsed index

        Raises:
            ValueError: If entries list is empty
        """
        if not entries:
            raise ValueError("Cannot create search index with empty entries list")

        self.entries = entries

        # Build corpus with field weighting (repeat high-value fields)
        corpus = []
        for entry in entries:
            # Title: 3x weight (most important for matching)
            # Tags: 2x weight (relevant keywords)
            # Section: 1x weight (contextual information)
            tokens = (
                self._tokenize(entry.title) * 3
                + sum([self._tokenize(tag) for tag in entry.tags], []) * 2
                + self._tokenize(entry.section)
            )
            corpus.append(tokens)

        self.bm25 = BM25Okapi(corpus)
        logger.debug(f"Built BM25 index with {len(entries)} entries")

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text with code-aware splitting.

        Handles camelCase, snake_case, and normal words.
        No stemming or stop word removal to preserve technical terms.

        Args:
            text: Text to tokenize

        Returns:
            List of lowercase tokens
        """
        if not text:
            return []

        # Split camelCase: "camelCase" -> "camel Case"
        text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
        # Replace underscores and hyphens with spaces
        text = text.replace("_", " ").replace("-", " ")
        # Split and lowercase
        return text.lower().split()

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search entries using BM25 ranking.

        Args:
            query: Search query
            top_k: Maximum number of results

        Returns:
            List of dicts with search results (for MCP compatibility)
        """
        # Tokenize query
        query_tokens = self._tokenize(query)

        if not query_tokens:
            logger.warning(f"Empty query after tokenization: '{query}'")
            return []

        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)

        # Check if all scores are zero (no matches)
        if len(scores) == 0 or max(scores) == 0:
            logger.debug(f"No matches found for query: '{query}'")
            return []

        # Normalize scores to 0-1 range
        max_score = max(scores)
        normalized_scores = [s / max_score for s in scores]

        # Get top-k indices
        top_indices = sorted(range(len(normalized_scores)), key=lambda i: normalized_scores[i], reverse=True)[:top_k]

        # Build results (filter out zero scores)
        results = []
        for idx in top_indices:
            score = normalized_scores[idx]
            if score > 0:
                entry = self.entries[idx]
                results.append(
                    SearchResult(
                        title=entry.title,
                        url=entry.url,
                        score=min(score, 1.0),  # Cap at 1.0 for Pydantic validation
                        section=entry.section,
                    )
                )

        logger.debug(f"Search for '{query}' returned {len(results)} results")

        # Convert to dicts for MCP compatibility
        return [{"title": r.title, "url": r.url, "score": r.score, "section": r.section} for r in results]

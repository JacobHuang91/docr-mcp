# Claude Development Guide

This file contains project context, architecture decisions, and development guidelines for working on docr-mcp with Claude.

## Project Overview

**docr-mcp** is a universal MCP (Model Context Protocol) server that provides LLMs with intelligent access to documentation from libraries, tools, cloud providers, and any software with public docs.

### Core Problem Being Solved
LLMs have outdated training data and can't efficiently search/fetch current documentation during conversations. This server bridges that gap.

## Architecture Decisions

### 1. Per-Library Instance Design ✅

**Decision**: Run separate MCP instances per library (e.g., `docr-twilio`, `docr-aws`)

**Rationale**:
- Smaller search space → better result quality
- Clearer tool naming for LLMs (`docr-twilio::search_docs` vs generic `search_docs`)
- Efficient context window usage (only load needed docs)
- Aligns with MCP's composable server philosophy
- Avoids namespace collision (e.g., "Lambda" in AWS vs Python)

**Implementation**: Single codebase with `--library` CLI argument that initializes server with library-specific config.

### 2. llms.txt First, Fallback Second

**Decision**: Primary indexing source is `llms.txt`, with fallbacks (sitemap.xml, manual config)

**Rationale**:
- `llms.txt` is becoming the standard for LLM-friendly docs
- Sites without it can use sitemap parsing
- Manual configs for high-priority libraries

### 3. Search-Then-Fetch Pattern

**Decision**: Two-step flow: `search_docs()` returns titles/URLs, then `fetch_doc()` gets content

**Rationale**:
- Avoids over-fetching
- LLM can decide which docs to fetch based on relevance
- Better for rate limiting and caching

### 4. Configuration-Driven

**Decision**: Each library has a YAML config file in `config/`

**Example**:
```yaml
name: "Twilio"
llms_txt: "https://www.twilio.com/llms.txt"
fallback: "sitemap"
sitemap_url: "https://www.twilio.com/sitemap.xml"
```

**Rationale**:
- Easy to add new libraries without code changes
- Community can contribute configs
- Version-specific config possible

## Tech Stack

- **Framework**: `fastmcp` (MCP server framework)
- **Search**: BM25 algorithm (future: code-aware tokenization)
- **Content Extraction**: HTML → Markdown (consider `trafilatura` or `html2text`)
- **Storage**: File-based for now, SQLite + FTS5 in Phase 2
- **Caching**: In-memory for Phase 1, persistent in Phase 2

## Development Guidelines

### Code Style
- Python 3.10+ (currently supporting 3.10-3.14)
- Use `ruff` for formatting and linting (configured in pyproject.toml)
- Type hints required
- Line length: 120 characters

### Adding New Libraries

1. Create config file: `config/{library}.yml`
2. Test llms.txt availability
3. Add fallback if needed
4. Update library list in `list_available_libraries()` tool

### Testing Strategy (Future)
- Unit tests for search/fetch logic
- Integration tests with mock HTTP responses
- Test against real llms.txt files (cached locally)

### Performance Considerations
- Lazy-load library indexes (don't load until first search)
- Cache fetched content with TTL (docs change infrequently)
- Rate limit crawling (respect robots.txt)
- Consider async fetching for multiple docs

## Current State (Phase 1)

### Implemented ✅
- Basic MCP server structure with 3 tools
- `get_server_info()` functional
- GitHub Actions for code format verification

### In Progress 🚧
- Command-line argument parsing (`--library`)
- Library configuration system
- llms.txt parsing and indexing
- BM25 search implementation
- HTML→Markdown extraction

### Not Started ❌
- Persistent storage
- Caching layer
- Multi-version support
- Sitemap fallback

## Design Patterns

### Tool Interface
Each instance provides:
```python
@mcp.tool()
def search_docs(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Returns: [{"title": "...", "url": "...", "score": 0.95}]"""

@mcp.tool()
def fetch_doc(url: str) -> Dict[str, Any]:
    """Returns: {"url": "...", "content": "...", "metadata": {...}}"""
```

### Configuration Schema
```yaml
name: string          # Display name
llms_txt: string      # URL to llms.txt
fallback: string      # "sitemap" | "manual" | null
sitemap_url: string?  # Optional sitemap URL
version: string?      # Optional version specifier
```

## Future Enhancements

1. **Multi-version support**: Allow `--library twilio@v2.0`
2. **Code-aware search**: Better tokenization for API names (camelCase, snake_case)
3. **Metadata enrichment**: Return doc type (tutorial, API ref, guide)
4. **Auto-discovery**: Crawl popular package registries (npm, PyPI) for docs links
5. **Cross-library search**: Advanced feature for power users

## User Workflow

```bash
# Discover available libraries
mcp add docr-mcp --list

# Add specific library
mcp add docr-mcp --library twilio

# In Claude conversation
"How do I send SMS with Twilio?"
# → Claude uses docr-twilio::search_docs()
# → Claude uses docr-twilio::fetch_doc() for top result
# → Response with current docs
```

## Open Questions

1. Should we support multiple libraries in one instance as an advanced feature?
2. What's the best cache TTL for docs? (Suggestion: 24 hours)
3. Should `search_docs` return content snippets or just titles/URLs?
4. How to handle authentication for private docs? (Future scope)

## Contributing Notes

- Keep the per-library design principle in mind
- Configuration changes preferred over code changes when adding libraries
- Test against real llms.txt files before committing configs
- Update this file when making architectural decisions

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

### 2. Flexible Index Sources

**Decision**: Support flexible source locations (URLs, file paths, etc.)

**Rationale**:
- Each docr knows what format it expects
- `source` field can be URL, file path, or any location string
- Future-proof for non-HTTP sources (local files, databases, APIs)
- No need for `type` field - docr implementation determines behavior

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

- **Framework**: `fastmcp` 3.2.3+ (MCP server framework)
- **Search**: BM25Okapi via `rank-bm25` with field weighting
- **Tokenization**: Code-aware (handles camelCase, snake_case)
- **HTTP Client**: `httpx` with timeout and redirect support
- **Config**: YAML + Pydantic models for validation
- **Testing**: pytest with 31 tests (functional + error paths)
- **Code Quality**: ruff for formatting and linting

## Development Guidelines

### Code Style
- Python 3.10+ (currently supporting 3.10-3.14)
- Use `ruff` for formatting and linting (configured in pyproject.toml)
- Type hints required
- Line length: 120 characters

### Adding New Public Libraries

1. Create docr: `src/docr_mcp/docrs/{library}.py` extending `BaseDocr`
2. Implement `fetch_index_entries()` and `fetch_content()` for the site's structure
3. Add URL validation and allowed domains
4. Register docr in `docrs/__init__.py`
5. Create config file: `config/{library}.yml` with source and tool descriptions
6. Add tests in `tests/docrs/{library}/`
7. Test against real docs with MCP Inspector
8. Submit PR

### Adding Authenticated Libraries (With Auth)

Authenticated documentation requires credentials (cookies, API keys, etc.). The `cookie` docr provides a reference implementation:

1. Clone repo locally
2. Copy `config/authenticated/cookie.example.yml` to `config/authenticated/mysite.yml`
3. Add your credentials directly in the YAML file:
   ```yaml
   auth:
     cookie: "session=abc123; token=xyz"
     allowed_domains:
       - "internal-docs.example.com"
   ```
4. Install locally: `uv pip install -e .`
5. Run: `uv run docr-mcp --library mysite`

For other auth methods (bearer tokens, API keys), extend `BaseDocr` and override `_get_client_config()`. See `authenticated/cookie.py` for reference.

### Testing Strategy
- **Functional tests**: 24 tests for parsing, search, and BM25 quality
- **Error path tests**: 7 tests for validation, HTTP errors, edge cases
- **Real fixtures**: Tests use actual llms.txt from strandsagents.com
- **Mock HTTP**: MockClient to avoid network calls during tests
- **Test structure**: `tests/docrs/{library}/` for per-library tests

### Performance & Security
- **Index loaded once**: Fetched at startup, kept in memory
- **BM25 is fast**: Searches hundreds of entries in <1ms
- **Resource cleanup**: atexit handler closes HTTP clients
- **Configurable timeout**: Per-docr timeout setting (default 30s)
- **URL validation**: HTTPS-only, domain whitelist, SSRF prevention
- **Error sanitization**: Don't expose internal stack traces
- **Top-K bounds**: Clamped to [1, 100] to prevent DoS

## Current State (v0.1.0 - Phase 1 Complete)

### ✅ Fully Implemented
- MCP server with 3 tools: `search_docs`, `fetch_doc`, `get_server_info`
- Command-line `--library` argument
- YAML config system with Pydantic validation
- llms.txt parsing with hierarchical sections and tag extraction
- BM25 search with field weighting (title 3x, tags 2x, section 1x)
- Code-aware tokenization (camelCase, snake_case)
- Markdown content fetching (Strands docr)
- HTTP error handling and validation
- URL validation (HTTPS-only, domain whitelist)
- Resource cleanup (atexit handler)
- 31 comprehensive tests
- GitHub Actions CI (test + lint + format)
- Tested with MCP clients and MCP Inspector

### 🔜 Future Enhancements
- Additional docrs (AWS, Twilio, OpenAI, etc.)
- Sitemap.xml source support
- Local file source support
- Persistent caching
- Multi-version docs

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
name: string                    # Display name
description: string             # Brief description
parser: string                  # Docr name (strands, aws, etc.)

index:                          # Index configuration
  source: string                # Source location (URL, file path, etc.)
  timeout: int?                 # HTTP timeout in seconds (default: 30, range: 1-300)

tools:                          # Optional tool descriptions
  search_docs:
    description: string         # Custom description for LLM
  fetch_doc:
    description: string         # Custom description for LLM
```

## Docr Architecture

Each documentation site needs a custom docr due to different structures and formats.

### Base Docr Interface

```python
from abc import ABC, abstractmethod
from typing import List
from docr_mcp.models import Document, IndexConfig, IndexEntry

class BaseDocr(ABC):
    @abstractmethod
    def fetch_index_entries(self, index_config: IndexConfig) -> List[IndexEntry]:
        """Fetch index entries from source.
        
        Returns: List[IndexEntry] with title, url, section, tags
        """
        pass
    
    @abstractmethod
    def fetch_content(self, url: str) -> Document:
        """Fetch documentation page.
        
        Returns: Document with url, content (markdown), metadata
        """
        pass
    
    def close(self):
        """Optional: cleanup resources (HTTP clients, etc.)"""
        return None
```

### Implemented Docrs

- **StrandsDocr**: 
  - Parses llms.txt with hierarchical sections
  - Extracts tags from titles and sections
  - Fetches raw markdown from strandsagents.com
  - HTTPS-only, domain-whitelisted

### Why Different Docrs?

Every documentation site has different:
- **Index format**: llms.txt, sitemap.xml, API, HTML page
- **Content format**: Markdown, HTML, reStructuredText
- **Structure**: Section hierarchy, navigation patterns
- **Security**: Domain restrictions, auth requirements

## Authentication for Internal Docs

**We do NOT implement authentication.**

**For internal/private docs:**
1. Fork the repo
2. Create custom docr extending BaseDocr
3. Override `_ensure_client()` to add auth headers
4. Store credentials in environment variables
5. Install locally: `uv pip install -e .`

**Example:**
```python
class MyCompanyDocr(BaseDocr):
    def _ensure_client(self):
        token = os.getenv("COMPANY_API_TOKEN")
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {token}"}
        )
```

## Design Decisions

### Why Not Generic Parser?

We don't have a "generic" fallback parser because:
- Every doc site is unique
- Automatic extraction (like trafilatura) often fails on technical docs
- Better to write custom logic for each site
- Ensures high-quality results

### Why No Caching?

For v0.1.0, we skip persistent caching because:
- Index loaded once at startup (stays in memory)
- Documentation changes infrequently
- Simpler architecture
- Can add later if needed

### Why BM25 Instead of Embeddings?

BM25 is sufficient for our use case:
- Fast (searches hundreds of entries in <1ms)
- No API costs
- Works offline
- Interpretable scores
- Good enough for keyword + semantic matching

## Key Implementation Details

### URL Validation
Every docr should validate URLs before fetching:
```python
def _validate_url(self, url: str):
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Only HTTPS allowed")
    if parsed.netloc not in self.ALLOWED_DOMAINS:
        raise ValueError(f"Domain not allowed: {parsed.netloc}")
```

### Resource Cleanup
HTTP clients should be cleaned up properly:
```python
# In server.py
def cleanup():
    docr.close()
atexit.register(cleanup)

# In docr
def close(self):
    if self.client:
        self.client.close()
        self.client = None
```

### Error Handling
Sanitize errors before returning to users:
```python
try:
    doc = docr.fetch_content(url)
except Exception as e:
    # Don't expose internal details
    if "timeout" in str(e).lower():
        return "Request timeout"
    elif "404" in str(e):
        return "Documentation not found"
    else:
        return "Failed to fetch documentation"
```

## Contributing

### Before Submitting PR

1. **Run tests**: `uv run pytest tests/ -v`
2. **Check coverage**: `uv run pytest tests/ --cov=docr_mcp`
3. **Format code**: `uv run ruff format .`
4. **Lint**: `uv run ruff check .`
5. **Test locally**: `npx @modelcontextprotocol/inspector uv run docr-mcp --library {name}`
6. **Update README**: Add library to supported docs table

### What to Include

- Docr implementation with URL validation
- Config YAML file
- Tests (functional + error handling)
- Update supported docs table in README
- No need to update CLAUDE.md unless adding new patterns

### Code Standards

- Python 3.10+
- Type hints required
- Docstrings for public methods
- Line length: 120 characters
- Use Pydantic models for validation
- Log with `logging.getLogger(__name__)`

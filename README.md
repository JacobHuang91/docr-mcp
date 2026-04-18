# docr-mcp

Universal MCP server for documentation. Provides LLMs with intelligent access to documentation from popular libraries, tools, cloud providers, and any software with public docs.

## Concept

**Problem**: LLMs need up-to-date documentation but can't efficiently search and fetch docs during conversations.

**Solution**: docr-mcp is an MCP server that:
1. Indexes documentation using `llms.txt` (or fallback strategies)
2. Searches docs using semantic/keyword algorithms (BM25 or similar)
3. Fetches and returns relevant doc content to the LLM

## Architecture

### Per-Library Instances
Instead of one massive server with all docs, docr-mcp runs **separate instances per library**:

```bash
# Add Twilio docs
mcp add docr-mcp --library twilio

# Add AWS docs separately
mcp add docr-mcp --library aws
```

**Why?**
- **Better search quality**: Smaller search space = more relevant results
- **Clearer tool naming**: LLM sees `docr-twilio::search_docs` vs `docr-aws::search_docs`
- **Efficient context usage**: Only load what's needed for the current project
- **Follows MCP philosophy**: Focused, composable servers

### How It Works

```
┌─────────────┐
│   LLM       │
│  (Claude)   │
└──────┬──────┘
       │
       │ "How do I send SMS with Twilio?"
       ▼
┌─────────────────────┐
│ docr-twilio MCP     │
│                     │
│ 1. search_docs()    │◄─── Searches indexed llms.txt content
│    └─> BM25 ranking │
│                     │
│ 2. fetch_doc()      │◄─── Fetches full doc content
│    └─> HTML → MD    │
└─────────────────────┘
```

### Configuration-Driven

Each library has a config file:

```yaml
# config/twilio.yml
name: "Twilio"
llms_txt: "https://www.twilio.com/llms.txt"
fallback: "sitemap"  # If llms.txt unavailable
sitemap_url: "https://www.twilio.com/sitemap.xml"
```

## Tools Provided

Each instance provides:

- `search_docs(query, top_k)` - Search documentation pages
- `fetch_doc(url)` - Fetch full documentation content
- `get_server_info()` - Get server metadata

## Roadmap

### Phase 1 (Current)
- [x] Basic MCP server structure
- [ ] Command-line argument for `--library`
- [ ] Library configuration system
- [ ] llms.txt parsing and indexing
- [ ] Basic BM25 search
- [ ] HTML→Markdown content extraction

### Phase 2
- [ ] Persistent index (SQLite with FTS5)
- [ ] Caching layer
- [ ] Background indexing
- [ ] Sitemap.xml fallback

### Phase 3
- [ ] Multi-version support (e.g., `/docs/v2.0/`)
- [ ] Auto-discovery of new libraries
- [ ] Code-aware tokenization
- [ ] Rate limiting and robots.txt respect

## Installation

```bash
# Install via uvx
uvx docr-mcp --library twilio

# Or install from source
git clone https://github.com/JacobHuang91/docr-mcp.git
cd docr-mcp
uv sync
uv run docr-mcp --library twilio
```

## Development

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Format code
uv run ruff format .

# Lint
uv run ruff check .
```

## License

MIT

## Contributing

Contributions welcome! See [CLAUDE.md](CLAUDE.md) for development guidelines and architecture decisions.

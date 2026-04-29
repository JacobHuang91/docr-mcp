# Contributing to docr-mcp

Thank you for your interest in contributing to docr-mcp! This guide will help you set up your development environment and add support for new documentation libraries.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Initial Setup

```bash
# Clone repository
git clone https://github.com/JacobHuang91/docr-mcp.git
cd docr-mcp

# Install dependencies (including dev dependencies)
uv sync --extra dev

# Run tests to verify setup
uv run pytest tests/ -v

# All tests should pass ✓
```

### Development Workflow

```bash
# Run tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/docrs/strands/ -v

# Format code (do this before committing)
uv run ruff format .

# Lint code (fix any issues before committing)
uv run ruff check .
```

### Testing with Claude Code

```bash
# Add your local changes to Claude Code for testing
make add-{library}-local

# Restart Claude Code and test
# Remove when done testing:
claude mcp remove docr-mcp-{library}-local
```

---

## Adding Authenticated Documentation

If you need to access **private/internal documentation** that requires authentication:

### Quick Setup (For Users)

1. **Copy the example config:**
   ```bash
   cd config/authenticated/
   cp cookie.example.yml my-internal-docs.yml
   ```

2. **Get your cookies** from browser DevTools (see [config/authenticated/README.md](src/docr_mcp/config/authenticated/README.md))

3. **Update the config** with your cookies and domain:
   ```yaml
   parser: cookie
   auth:
     cookie: "session=abc; token=xyz"
     allowed_domains: ["internal.mycompany.com"]
   index:
     source: "https://internal.mycompany.com/sitemap.xml"
   ```

4. **Run locally:**
   ```bash
   uv run docr-mcp --library my-internal-docs
   ```

**No code changes needed** - just create a YAML config file! The `cookie` docr handles all authentication.

See [config/authenticated/README.md](src/docr_mcp/config/authenticated/README.md) for detailed instructions.

---

## Adding a New Library

### Overview

Each documentation source needs a custom docr because every site has different:
- **Index format**: llms.txt, sitemap.xml, JSON API, HTML page, etc.
- **Content format**: Markdown, HTML, reStructuredText, etc.
- **URL structure**: Absolute vs relative URLs, domain patterns
- **Section hierarchy**: How content is organized

**Important**: Don't force your implementation to match existing patterns. Design your docr based on what works best for your documentation source.

### Steps to Add a New Library

#### 1. Create a Docr Implementation

**File**: `src/docr_mcp/docrs/{library}.py`

Your docr must extend `BaseDocr` and implement:
- `fetch_index_entries(IndexConfig) -> List[IndexEntry]` - Parse the index/sitemap
- `fetch_content(url) -> Document` - Fetch a documentation page
- `_validate_url(url)` - Validate URLs before fetching
- `close()` - Clean up HTTP client resources

**Key requirements**:
- Define `ALLOWED_DOMAINS` class attribute (security)
- Only accept HTTPS URLs
- Use `httpx.Client` for HTTP requests
- Implement context manager (`__enter__`, `__exit__`)
- Add proper error handling and logging

Refer to existing docrs (`strands.py`, `vercel.py`, `twilio.py`, etc.) for implementation patterns, but adapt to your needs.

#### 2. Register the Docr

**File**: `src/docr_mcp/docrs/__init__.py`

Add your docr to the `load_docr()` function:
- Import your docr class
- Add an `elif` block for your library name
- Update the error message with available docrs

#### 3. Create Configuration

**File**: `src/docr_mcp/config/{library}.yml`

Define:
- `name`: Display name
- `description`: Brief description
- `parser`: Your docr name (lowercase)
- `index.source`: URL to index file (llms.txt, sitemap, etc.)
- `index.timeout`: Optional timeout in seconds (default: 30)
- `tools.search_docs.description`: When to use this tool
- `tools.fetch_doc.description`: What this tool does

Make descriptions specific and helpful for LLMs to know when to use your tool.

#### 4. Write Tests

**Directory**: `tests/docrs/{library}/`

Create at minimum:
- `__init__.py`
- `test_{library}_docr.py` - Unit tests
- `test_{library}_e2e.py` - End-to-end workflow tests

**Tests must**:
- Fetch from **real live documentation** (no static fixtures)
- Test index parsing (verify structure, count, URLs)
- Test content fetching (verify format, content length)
- Test URL validation (HTTPS only, domain whitelist)
- Test search functionality (queries, scoring, limits)
- Test E2E workflow (search → fetch → verify)

Use `@pytest.fixture(scope="module")` to fetch index once per test module.

#### 5. Update Infrastructure

Add to these files:
- **README.md**: Add row to supported docs table with status badge
- **Makefile**: Add `add-{library}` and `add-{library}-local` targets
- **.github/workflows/code-format.yml**: Add `test-{library}` job

#### 6. Test Locally

```bash
# Run your tests
uv run pytest tests/docrs/{library}/ -v

# Install locally and test with Claude Code
make add-{library}-local

# Restart Claude Code and ask questions to test search and fetch
```

#### 7. Submit Pull Request

Your PR should include:
- Docr implementation
- Configuration YAML
- Tests (unit + E2E)
- Updated README, Makefile, CI workflow
- Clear commit message describing what was added

**PR Checklist**:
- [ ] All tests pass (`uv run pytest tests/ -v`)
- [ ] Code is formatted (`uv run ruff format .`)
- [ ] No linting errors (`uv run ruff check .`)
- [ ] Tests fetch from real live documentation
- [ ] Updated README.md with new library
- [ ] Updated Makefile and CI workflow
- [ ] Tested with Claude Code locally

---

## Code Standards

### Style
- Python 3.10+
- Type hints required
- Docstrings for public methods
- Line length: 120 characters max
- Use ruff for formatting and linting

### Security (Required)
1. **HTTPS Only**: Reject HTTP URLs
2. **Domain Whitelist**: Define `ALLOWED_DOMAINS`
3. **URL Validation**: Validate before fetching
4. **Error Sanitization**: Don't expose internal details
5. **Resource Cleanup**: Implement `close()` method

### Testing (Required)
- Fetch from **live documentation sites** (no static fixtures)
- Test both success and error paths
- Mock HTTP only for error testing
- Aim for comprehensive coverage

---

## Design Philosophy

**Every documentation site is unique.** Don't force your implementation to match existing patterns:

- If your docs have relative URLs, convert them to absolute
- If your docs use a custom format, parse it appropriately
- If your docs need special headers or auth, implement it
- If your docs structure differs, adapt the parsing logic

The framework is flexible - focus on making your docr work well for your specific documentation source.

---

## Getting Help

- **Questions?** Open a [Discussion](https://github.com/JacobHuang91/docr-mcp/discussions)
- **Bug Reports?** Open an [Issue](https://github.com/JacobHuang91/docr-mcp/issues)
- **Architecture?** See [CLAUDE.md](CLAUDE.md) for project context

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

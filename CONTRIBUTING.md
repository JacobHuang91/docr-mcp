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

# Run tests with coverage
uv run pytest tests/ --cov=docr_mcp

# Run specific test file
uv run pytest tests/docrs/strands/ -v

# Format code (do this before committing)
uv run ruff format .

# Lint code (fix any issues before committing)
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .
```

### Testing Locally with MCP Inspector

```bash
# Test your changes with MCP Inspector
npx @modelcontextprotocol/inspector uv run docr-mcp --library strands

# Opens at http://localhost:6274
# - Test search_docs with different queries
# - Test fetch_doc with URLs from search results
# - Check BM25 scoring and relevance
```

### Testing with MCP Clients

```bash
# Add to your MCP client for testing (example: Claude Code)
claude mcp add docr-mcp-test -- \
  uv --directory $(pwd) run docr-mcp --library strands

# Restart your client and test by asking questions
# Remove when done testing:
claude mcp remove docr-mcp-test
```

---

## Adding a New Library

### 1. Create a Docr

Create a new file `src/docr_mcp/docrs/{library}.py`:

```python
"""Docr for {Library Name} documentation."""

import logging
import re
from typing import List
from urllib.parse import urlparse

import httpx

from docr_mcp.models import Document, IndexConfig, IndexEntry
from .base import BaseDocr

logger = logging.getLogger(__name__)


class MyLibraryDocr(BaseDocr):
    """Docr for {Library Name} documentation."""

    ALLOWED_DOMAINS = {"docs.mylibrary.com"}

    def __init__(self):
        self.client = None
        self._timeout = 30.0

    def __enter__(self):
        """Context manager entry."""
        self.client = httpx.Client(
            timeout=self._timeout,
            follow_redirects=True,
            headers={"User-Agent": "docr-mcp/0.1.0"}
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        if self.client:
            self.client.close()
        return False

    def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if not self.client:
            self.client = httpx.Client(
                timeout=self._timeout,
                follow_redirects=True,
                headers={"User-Agent": "docr-mcp/0.1.0"}
            )

    def _validate_url(self, url: str) -> None:
        """Validate URL is safe to fetch."""
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValueError(f"Invalid URL format: {url}") from e

        if parsed.scheme != "https":
            raise ValueError(f"Only HTTPS URLs allowed, got: {parsed.scheme}")

        if parsed.netloc not in self.ALLOWED_DOMAINS:
            raise ValueError(
                f"Domain not allowed: {parsed.netloc}. "
                f"Allowed: {self.ALLOWED_DOMAINS}"
            )

    def fetch_index_entries(self, index_config: IndexConfig) -> List[IndexEntry]:
        """Fetch and parse documentation index entries.

        Args:
            index_config: IndexConfig with source URL

        Returns:
            List of IndexEntry objects

        Raises:
            ValueError: If source is invalid or empty
            httpx.HTTPError: If HTTP request fails
        """
        url = index_config.source
        self._timeout = index_config.timeout

        # Validate URL
        self._validate_url(url)

        # Initialize client
        self._ensure_client()

        logger.debug(f"Fetching index from {url}")

        try:
            response = self.client.get(url)
            response.raise_for_status()
            content = response.text
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise ValueError(f"Failed to fetch index: {type(e).__name__}") from e

        # Parse content into IndexEntry objects
        entries = self._parse_index(content)

        if not entries:
            raise ValueError(f"No entries found in index at {url}")

        logger.info(f"Parsed {len(entries)} entries from {url}")
        return entries

    def _parse_index(self, content: str) -> List[IndexEntry]:
        """Parse index content into IndexEntry objects.
        
        Implement your parsing logic here based on the format:
        - llms.txt: Parse markdown links with sections
        - sitemap.xml: Parse XML for URLs
        - JSON API: Parse JSON response
        - HTML page: Parse HTML links
        """
        # TODO: Implement parsing logic
        entries = []
        # Your parsing code here
        return entries

    def fetch_content(self, url: str) -> Document:
        """Fetch and parse a documentation page.

        Args:
            url: Documentation page URL

        Returns:
            Document with content and metadata

        Raises:
            ValueError: If URL is invalid
            httpx.HTTPError: If HTTP request fails
        """
        self._validate_url(url)
        self._ensure_client()

        logger.debug(f"Fetching content from {url}")

        try:
            response = self.client.get(url)
            response.raise_for_status()
            content = response.text
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise

        # Extract title and format content
        title = self._extract_title(content)

        return Document(
            url=url,
            content=content,
            metadata={
                "title": title,
                "source": "mylibrary",
                "format": "markdown"  # or "html", etc.
            }
        )

    def _extract_title(self, content: str) -> str:
        """Extract title from content."""
        # TODO: Implement title extraction
        return ""

    def close(self):
        """Explicitly close HTTP client."""
        if self.client:
            self.client.close()
            self.client = None
```

### 2. Register the Docr

Add to `src/docr_mcp/docrs/__init__.py`:

```python
def load_docr(config: LibraryConfig) -> BaseDocr:
    """Load the appropriate docr based on config."""
    docr_name = config.parser

    if docr_name == "strands":
        from .strands import StrandsDocr
        return StrandsDocr()
    elif docr_name == "mylibrary":  # Add this
        from .mylibrary import MyLibraryDocr
        return MyLibraryDocr()
    else:
        raise ValueError(f"Unknown docr: {docr_name}. Available: strands, mylibrary")
```

### 3. Create Configuration

Create `src/docr_mcp/config/{library}.yml`:

```yaml
name: "My Library"
description: "Brief description of what this library does..."
parser: "mylibrary"

index:
  source: "https://docs.mylibrary.com/llms.txt"
  timeout: 30  # Optional, defaults to 30

tools:
  search_docs:
    description: |
      Search My Library documentation.
      
      Use this tool when users ask about:
      - Core concepts and features
      - API reference and usage
      - Configuration and setup
      - Examples and tutorials
      
      Returns relevant documentation pages ranked by relevance.
      
  fetch_doc:
    description: |
      Fetch full content from a My Library documentation page.
      
      Retrieves complete documentation and returns it formatted
      for easy reading. Use after search_docs to get detailed
      information about a specific topic.
```

### 4. Add Tests

Create `tests/docrs/{library}/test_{library}_docr.py`:

```python
"""Tests for {Library} docr."""

from pathlib import Path

import pytest

from docr_mcp.core.search import SearchIndex
from docr_mcp.docrs.mylibrary import MyLibraryDocr
from docr_mcp.models import IndexConfig

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "mylibrary"


def load_fixture(filename: str) -> str:
    """Load test fixture."""
    with open(FIXTURES_DIR / filename, "r") as f:
        return f.read()


class TestMyLibraryDocr:
    """Test cases for MyLibrary docr."""

    def test_parse_index_structure(self):
        """Test that docr correctly extracts entries."""
        docr = MyLibraryDocr()

        # Mock HTTP client
        class MockResponse:
            def __init__(self):
                self.text = load_fixture("index.txt")

            def raise_for_status(self):
                pass

        class MockClient:
            def get(self, url):
                return MockResponse()

            def close(self):
                pass

        docr.client = MockClient()

        config = IndexConfig(source="https://docs.mylibrary.com/index.txt")
        entries = docr.fetch_index_entries(config)

        assert len(entries) > 0
        assert entries[0].title
        assert entries[0].url

    def test_url_validation(self):
        """Test URL validation."""
        docr = MyLibraryDocr()
        docr.client = type("MockClient", (), {})()

        # Should reject HTTP
        with pytest.raises(ValueError, match="HTTPS"):
            docr._validate_url("http://docs.mylibrary.com")

        # Should reject invalid domain
        with pytest.raises(ValueError, match="Domain not allowed"):
            docr._validate_url("https://evil.com")

        # Should accept valid URL
        docr._validate_url("https://docs.mylibrary.com/docs")
```

Create `tests/fixtures/{library}/index.txt` with sample data.

### 5. Test Locally

```bash
# Run unit tests
uv run pytest tests/docrs/{library}/ -v

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run docr-mcp --library {library}

# Test search and fetch in browser UI
```

### 6. Submit Pull Request

Your PR should include:

1. **Docr implementation** (`src/docr_mcp/docrs/{library}.py`)
2. **Registration** (updated `src/docr_mcp/docrs/__init__.py`)
3. **Configuration** (`src/docr_mcp/config/{library}.yml`)
4. **Tests** (`tests/docrs/{library}/`)
5. **Test fixtures** (`tests/fixtures/{library}/`)
6. **Documentation** (update supported docs table in README.md)

**PR Checklist:**
- [ ] All tests pass (`uv run pytest tests/ -v`)
- [ ] Code is formatted (`uv run ruff format .`)
- [ ] No linting errors (`uv run ruff check .`)
- [ ] Tested with MCP Inspector
- [ ] Updated README.md supported docs table
- [ ] Added clear commit message

## Code Standards

### Style Guide

- **Python Version**: 3.10+
- **Type Hints**: Required for all function signatures
- **Docstrings**: Required for public methods (Google style)
- **Line Length**: 120 characters max
- **Imports**: Sorted with ruff
- **Naming**: snake_case for functions/variables, PascalCase for classes

### Security Requirements

All docrs must implement:

1. **HTTPS Only**: Reject non-HTTPS URLs
2. **Domain Whitelist**: Define `ALLOWED_DOMAINS` class attribute
3. **URL Validation**: Call `_validate_url()` before fetching
4. **Error Sanitization**: Don't expose internal details in errors
5. **Resource Cleanup**: Implement `close()` method

### Testing Requirements

- **Functional tests**: Index parsing, content fetching
- **Error handling tests**: Invalid URLs, HTTP errors, empty results
- **Use fixtures**: Don't hardcode test data in code
- **Mock HTTP**: Use MockClient to avoid network calls
- **Coverage**: Aim for >80% coverage of new code


## Getting Help

- **Questions?** Open a [Discussion](https://github.com/JacobHuang91/docr-mcp/discussions)
- **Bug Reports?** Open an [Issue](https://github.com/JacobHuang91/docr-mcp/issues)
- **Architecture Questions?** See [CLAUDE.md](CLAUDE.md)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

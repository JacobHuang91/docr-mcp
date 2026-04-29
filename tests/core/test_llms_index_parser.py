"""Tests for LLMsIndexParser."""

import pytest

from docr_mcp.core.index_parsers import LLMsIndexParser


class TestLLMsIndexParser:
    """Test cases for LLMsIndexParser."""

    def test_parse_basic_llms_txt(self):
        """Test parsing basic llms.txt format."""
        content = """# Documentation

## Getting Started
- [Introduction](https://docs.example.com/intro.md): Getting started guide
- [Installation](https://docs.example.com/install.md)

## API Reference
- [Authentication](https://docs.example.com/api/auth.md)
- [Endpoints](https://docs.example.com/api/endpoints.md)
"""
        parser = LLMsIndexParser()
        entries = parser.parse(content)

        assert len(entries) == 4
        assert entries[0].title == "Introduction"
        assert entries[0].url == "https://docs.example.com/intro.md"
        assert entries[0].section == "Getting Started"
        assert "getting" in entries[0].tags
        assert "introduction" in entries[0].tags

    def test_parse_relative_urls(self):
        """Test parsing llms.txt with relative URLs."""
        content = """# Documentation

## API
- [Authentication](/docs/auth.md)
- [Endpoints](/docs/endpoints.md)
"""
        parser = LLMsIndexParser(base_url="https://example.com")
        entries = parser.parse(content)

        assert len(entries) == 2
        assert entries[0].url == "https://example.com/docs/auth.md"
        assert entries[1].url == "https://example.com/docs/endpoints.md"

    def test_parse_absolute_urls(self):
        """Test parsing llms.txt with absolute URLs."""
        content = """# Documentation

## API
- [Auth](https://docs.example.com/auth.md)
- [Users](https://api.example.com/users.md)
"""
        parser = LLMsIndexParser(base_url="https://example.com")
        entries = parser.parse(content)

        # Absolute URLs should remain unchanged
        assert entries[0].url == "https://docs.example.com/auth.md"
        assert entries[1].url == "https://api.example.com/users.md"

    def test_parse_with_subsections(self):
        """Test parsing with nested subsections."""
        content = """# Documentation

## API Reference
### Authentication
- [OAuth](https://docs.example.com/oauth.md)
- [API Keys](https://docs.example.com/api-keys.md)

### Resources
- [Users](https://docs.example.com/users.md)
"""
        parser = LLMsIndexParser()
        entries = parser.parse(content)

        assert len(entries) == 3
        assert entries[0].section == "API Reference > Authentication"
        assert entries[2].section == "API Reference > Resources"

    def test_parse_with_descriptions(self):
        """Test parsing entries with descriptions."""
        content = """# Documentation

## Guides
- [Quick Start](https://docs.example.com/quickstart.md): Get started in 5 minutes
- [Advanced](https://docs.example.com/advanced.md): Deep dive into features
"""
        parser = LLMsIndexParser()
        entries = parser.parse(content)

        assert len(entries) == 2
        # Tags should include words from description
        assert any("started" in tag or "minutes" in tag for tag in entries[0].tags)

    def test_parse_empty_content(self):
        """Test parsing empty content."""
        parser = LLMsIndexParser()
        entries = parser.parse("")

        assert len(entries) == 0

    def test_parse_no_links(self):
        """Test parsing content with no links."""
        content = """# Documentation

## Section 1
Some text here

## Section 2
More text
"""
        parser = LLMsIndexParser()
        entries = parser.parse(content)

        assert len(entries) == 0

    def test_custom_url_transform(self):
        """Test custom URL transformation."""
        content = """# Documentation

## API
- [Auth](/auth.md)
"""

        def transform(url):
            return url.replace(".md", ".html")

        parser = LLMsIndexParser(url_transform=transform)
        entries = parser.parse(content)

        assert entries[0].url == "/auth.html"

    def test_parse_mixed_bullet_styles(self):
        """Test parsing with both * and - bullets."""
        content = """# Documentation

## Section 1
* [Link 1](https://example.com/1.md)
- [Link 2](https://example.com/2.md)
* [Link 3](https://example.com/3.md)
"""
        parser = LLMsIndexParser()
        entries = parser.parse(content)

        assert len(entries) == 3

    def test_parse_real_strands_format(self):
        """Test parsing with real Strands llms.txt format."""
        content = """# Strands Agents Documentation

## Getting Started
- [Quickstart](https://strandsagents.com/docs/quickstart.md): Get up and running with Strands
- [agent-loop](https://strandsagents.com/docs/agent-loop.md): Understanding the agent execution loop

## Core Concepts
### Agent System
- [Agents](https://strandsagents.com/docs/agents.md): Building intelligent agents
- [Tools](https://strandsagents.com/docs/tools.md): Extending agent capabilities
"""
        parser = LLMsIndexParser()
        entries = parser.parse(content)

        assert len(entries) == 4
        assert entries[0].title == "Quickstart"
        assert entries[0].section == "Getting Started"
        assert entries[2].title == "Agents"
        assert entries[2].section == "Core Concepts > Agent System"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

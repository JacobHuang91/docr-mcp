"""Tests for SitemapIndexParser."""

import pytest

from docr_mcp.core.index_parsers import SitemapIndexParser


class TestSitemapIndexParser:
    """Test cases for SitemapIndexParser."""

    def test_parse_basic_sitemap(self):
        """Test parsing basic sitemap.xml format."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://docs.example.com/getting-started</loc>
    <lastmod>2025-01-01</lastmod>
  </url>
  <url>
    <loc>https://docs.example.com/api/authentication</loc>
    <lastmod>2025-01-02</lastmod>
  </url>
  <url>
    <loc>https://docs.example.com/api/endpoints</loc>
  </url>
</urlset>"""
        parser = SitemapIndexParser()
        entries = parser.parse(content)

        assert len(entries) == 3
        assert entries[0].title == "Getting Started"
        assert entries[0].url == "https://docs.example.com/getting-started"
        assert entries[0].section == ""
        assert "getting-started" in entries[0].tags

        assert entries[1].title == "Authentication"
        assert entries[1].section == "api"
        assert "api" in entries[1].tags
        assert "authentication" in entries[1].tags

    def test_parse_simplified_sitemap(self):
        """Test parsing simplified sitemap with just <loc> tags."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset>
  <loc>https://docs.example.com/intro</loc>
  <loc>https://docs.example.com/guide</loc>
</urlset>"""
        parser = SitemapIndexParser()
        entries = parser.parse(content)

        assert len(entries) == 2
        assert entries[0].title == "Intro"
        assert entries[1].title == "Guide"

    def test_parse_nested_paths(self):
        """Test parsing URLs with nested path structure."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://docs.example.com/api/v2/users/create</loc>
  </url>
  <url>
    <loc>https://docs.example.com/api/v2/users/delete</loc>
  </url>
</urlset>"""
        parser = SitemapIndexParser()
        entries = parser.parse(content)

        assert len(entries) == 2
        assert entries[0].title == "Create"
        assert entries[0].section == "api > v2 > users"
        assert entries[1].title == "Delete"
        assert entries[1].section == "api > v2 > users"

    def test_parse_with_html_extension(self):
        """Test parsing URLs with .html extension."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://docs.example.com/guides/quick-start.html</loc>
  </url>
  <url>
    <loc>https://docs.example.com/api/auth.html</loc>
  </url>
</urlset>"""
        parser = SitemapIndexParser()
        entries = parser.parse(content)

        assert len(entries) == 2
        # Extensions should be removed
        assert entries[0].title == "Quick Start"
        assert entries[1].title == "Auth"

    def test_parse_with_various_extensions(self):
        """Test parsing URLs with different extensions."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://docs.example.com/page1.html</loc>
  </url>
  <url>
    <loc>https://docs.example.com/page2.htm</loc>
  </url>
  <url>
    <loc>https://docs.example.com/page3.md</loc>
  </url>
  <url>
    <loc>https://docs.example.com/page4.php</loc>
  </url>
</urlset>"""
        parser = SitemapIndexParser()
        entries = parser.parse(content)

        assert len(entries) == 4
        for entry in entries:
            # All should have extensions removed and be title-cased
            assert not entry.title.endswith((".html", ".htm", ".md", ".php"))
            assert entry.title[0].isupper()

    def test_parse_with_hyphens_and_underscores(self):
        """Test title conversion from URLs with hyphens and underscores."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://docs.example.com/getting-started-guide</loc>
  </url>
  <url>
    <loc>https://docs.example.com/api_reference_v2</loc>
  </url>
  <url>
    <loc>https://docs.example.com/user-guide_advanced</loc>
  </url>
</urlset>"""
        parser = SitemapIndexParser()
        entries = parser.parse(content)

        assert len(entries) == 3
        assert entries[0].title == "Getting Started Guide"
        assert entries[1].title == "Api Reference V2"
        assert entries[2].title == "User Guide Advanced"

    def test_parse_empty_sitemap(self):
        """Test parsing empty sitemap."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
</urlset>"""
        parser = SitemapIndexParser()
        entries = parser.parse(content)

        assert len(entries) == 0

    def test_parse_root_urls_skipped(self):
        """Test that root URLs without path are skipped."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://docs.example.com/</loc>
  </url>
  <url>
    <loc>https://docs.example.com</loc>
  </url>
  <url>
    <loc>https://docs.example.com/guide</loc>
  </url>
</urlset>"""
        parser = SitemapIndexParser()
        entries = parser.parse(content)

        # Only the one with actual path should be included
        assert len(entries) == 1
        assert entries[0].title == "Guide"

    def test_parse_tags_generation(self):
        """Test that tags are generated from URL path components."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://docs.example.com/api/authentication/oauth</loc>
  </url>
</urlset>"""
        parser = SitemapIndexParser()
        entries = parser.parse(content)

        assert len(entries) == 1
        tags = entries[0].tags
        assert "api" in tags
        assert "authentication" in tags
        assert "oauth" in tags

    def test_parse_malformed_xml(self):
        """Test parsing malformed XML."""
        content = """not valid xml"""
        parser = SitemapIndexParser()

        # Should not crash, but may return empty list
        entries = parser.parse(content)
        assert isinstance(entries, list)

    def test_parse_real_world_sitemap(self):
        """Test parsing with realistic sitemap structure."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://internal-docs.example.com/products/sms/overview</loc>
    <lastmod>2025-04-20T10:00:00+00:00</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://internal-docs.example.com/products/sms/api-reference</loc>
    <lastmod>2025-04-21T12:00:00+00:00</lastmod>
  </url>
  <url>
    <loc>https://internal-docs.example.com/products/voice/quickstart</loc>
  </url>
</urlset>"""
        parser = SitemapIndexParser()
        entries = parser.parse(content)

        assert len(entries) == 3
        assert entries[0].title == "Overview"
        assert entries[0].section == "products > sms"
        assert entries[1].title == "Api Reference"
        assert entries[1].section == "products > sms"
        assert entries[2].title == "Quickstart"
        assert entries[2].section == "products > voice"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Common docr patterns for different documentation site structures.

Each pattern combines an index parser with a content parser:
- LLMsMdDocr: llms.txt index + markdown content
- SitemapHtmlDocr: sitemap.xml index + HTML content (converted to markdown)
"""

from .llms_md_docr import LLMsMdDocr
from .sitemap_html_docr import SitemapHtmlDocr

__all__ = ["LLMsMdDocr", "SitemapHtmlDocr"]

"""Main MCP server implementation."""

import argparse
import atexit
import sys
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

from docr_mcp.core.config_loader import load_config
from docr_mcp.core.logger import get_logger, setup_logger
from docr_mcp.core.search import SearchIndex
from docr_mcp.docrs import load_docr

# Setup centralized logging
setup_logger()
logger = get_logger(__name__)


def create_server(library: str) -> FastMCP:
    """Create and configure MCP server for a specific library.

    Args:
        library: Library name (e.g., "strands", "aws")

    Returns:
        Configured FastMCP server instance
    """
    # Load configuration
    try:
        config = load_config(library)
    except FileNotFoundError as err:
        logger.error(f"Configuration not found: {err}")
        sys.exit(1)
    except ValueError as err:
        logger.error(f"Invalid configuration: {err}")
        sys.exit(1)

    # Create server with library-specific name
    server_name = f"docr-{library}"
    mcp = FastMCP(server_name)

    # Load docr
    try:
        docr = load_docr(config)
        logger.debug(f"Loaded docr: {docr.__class__.__name__}")
    except Exception as err:
        logger.error(f"Error loading docr: {err}")
        sys.exit(1)

    # Register cleanup handler
    def cleanup():
        """Cleanup resources on shutdown."""
        logger.debug("Cleaning up resources...")
        docr.close()

    atexit.register(cleanup)

    # Fetch and index documentation
    logger.info(f"Loading {config.name} documentation...")
    try:
        entries = docr.fetch_index_entries(config.index)
        logger.info(f"Indexed {len(entries)} entries")
    except Exception as err:
        logger.error(f"Error fetching index: {err}")
        sys.exit(1)

    # Build search index
    search_index = SearchIndex(entries)

    # Get tool descriptions from config
    search_desc = config.get_tool_description("search_docs", f"Search {config.name} documentation")
    fetch_desc = config.get_tool_description("fetch_doc", f"Fetch {config.name} documentation page")

    # Register tools
    @mcp.tool(description=search_desc)
    def search_docs(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search documentation pages.

        Args:
            query: Search query string
            top_k: Maximum number of results to return (default: 5, max: 100)

        Returns:
            List of matching documents with title, URL, and relevance score
        """
        # Validate top_k bounds
        if top_k < 1 or top_k > 100:
            logger.warning(f"top_k={top_k} out of bounds, clamping to [1, 100]")
            top_k = max(1, min(100, top_k))

        return search_index.search(query, top_k)

    @mcp.tool(description=fetch_desc)
    def fetch_doc(url: str) -> Dict[str, Any]:
        """Fetch full documentation content.

        Args:
            url: Documentation URL to fetch

        Returns:
            Document content and metadata
        """
        try:
            doc = docr.fetch_content(url)
            # Convert Pydantic model to dict for MCP
            return {"url": doc.url, "content": doc.content, "metadata": doc.metadata}
        except Exception as fetch_err:
            logger.error(f"Error fetching content from {url}: {fetch_err}")
            # Sanitize error message - don't expose internal details
            error_msg = "Failed to fetch documentation"
            if "timeout" in str(fetch_err).lower():
                error_msg = "Request timeout"
            elif "404" in str(fetch_err):
                error_msg = "Documentation not found"
            elif "connection" in str(fetch_err).lower():
                error_msg = "Connection error"
            return {"url": url, "content": "", "error": error_msg, "metadata": {"error": True}}

    @mcp.tool()
    def get_server_info() -> Dict[str, Any]:
        """Get information about this MCP server.

        Returns:
            Server metadata and configuration
        """
        return {
            "name": server_name,
            "library": library,
            "library_name": config.name,
            "version": "0.1.0",
            "description": config.description,
            "indexed_entries": len(entries),
        }

    return mcp


def main() -> None:
    """Main entry point for the MCP server."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="docr-mcp: Universal MCP server for documentation")
    parser.add_argument("--library", required=True, help="Library to serve documentation for (e.g., strands, aws)")

    args = parser.parse_args()

    # Create and run server
    mcp = create_server(args.library)
    mcp.run()

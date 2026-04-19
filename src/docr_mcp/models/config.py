"""Configuration models."""

from typing import Dict, Optional

from pydantic import BaseModel, Field


class IndexConfig(BaseModel):
    """Configuration for documentation index."""

    source: str = Field(..., description="Source location (URL, file path, etc.)")
    timeout: int = Field(default=30, description="HTTP timeout in seconds", ge=1, le=300)

    model_config = {"extra": "allow"}  # Allow additional fields for parser-specific config


class ToolConfig(BaseModel):
    """Configuration for MCP tool."""

    description: str = Field(..., description="Tool description for LLM")

    model_config = {"frozen": True}


class LibraryConfig(BaseModel):
    """Configuration for a documentation library."""

    name: str = Field(..., description="Library display name")
    description: str = Field(..., description="Brief description of the library")
    parser: str = Field(..., description="Docr name to use (e.g., 'strands', 'aws')")
    index: IndexConfig = Field(..., description="Index configuration")
    tools: Optional[Dict[str, ToolConfig]] = Field(default=None, description="Tool configurations")

    model_config = {"frozen": False}

    def get_tool_description(self, tool_name: str, default: str) -> str:
        """Get tool description or return default.

        Args:
            tool_name: Name of the tool
            default: Default description if not found

        Returns:
            Tool description string
        """
        if self.tools and tool_name in self.tools:
            return self.tools[tool_name].description
        return default

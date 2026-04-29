"""Configuration models."""

from typing import Dict, List, Optional

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


class AuthConfig(BaseModel):
    """Configuration for authentication."""

    cookie: Optional[str] = Field(default=None, description="Cookie string for authentication")
    allowed_domains: Optional[List[str]] = Field(default=None, description="Allowed domains for security")

    model_config = {"extra": "allow"}  # Allow additional auth methods in future


class LibraryConfig(BaseModel):
    """Configuration for a documentation library."""

    name: str = Field(..., description="Library display name")
    description: str = Field(..., description="Brief description of the library")
    parser: str = Field(..., description="Docr name to use (e.g., 'strands', 'aws')")
    auth: Optional[AuthConfig] = Field(default=None, description="Authentication configuration")
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

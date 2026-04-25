.PHONY: help add-strands add-vercel add-twilio add-openai add-stripe add-anthropic add-strands-local add-vercel-local add-twilio-local add-openai-local add-stripe-local add-anthropic-local

PROJECT_DIR := $(shell pwd)

help:
	@echo "docr-mcp - Add documentation MCP servers to Claude Code"
	@echo ""
	@echo "Production (from PyPI):"
	@echo "  make add-strands           - Add Strands Agents documentation"
	@echo "  make add-vercel            - Add Vercel documentation"
	@echo "  make add-twilio            - Add Twilio documentation"
	@echo "  make add-openai            - Add OpenAI documentation"
	@echo "  make add-stripe            - Add Stripe documentation"
	@echo "  make add-anthropic         - Add Anthropic documentation"
	@echo ""
	@echo "Development (local code):"
	@echo "  make add-strands-local     - Add Strands with local development code"
	@echo "  make add-vercel-local      - Add Vercel with local development code"
	@echo "  make add-twilio-local      - Add Twilio with local development code"
	@echo "  make add-openai-local      - Add OpenAI with local development code"
	@echo "  make add-stripe-local      - Add Stripe with local development code"
	@echo "  make add-anthropic-local   - Add Anthropic with local development code"

add-strands:
	@echo "Adding Strands Agents MCP server to Claude Code..."
	@claude mcp add docr-mcp-strands -- uvx docr-mcp --library strands
	@echo "✅ Done! Restart Claude Code to activate."

add-vercel:
	@echo "Adding Vercel MCP server to Claude Code..."
	@claude mcp add docr-mcp-vercel -- uvx docr-mcp --library vercel
	@echo "✅ Done! Restart Claude Code to activate."

add-strands-local:
	@echo "Adding Strands Agents MCP server (local development)..."
	@claude mcp add docr-mcp-strands-local -- uv --directory $(PROJECT_DIR) run docr-mcp --library strands
	@echo "✅ Done! Restart Claude Code to activate."

add-vercel-local:
	@echo "Adding Vercel MCP server (local development)..."
	@claude mcp add docr-mcp-vercel-local -- uv --directory $(PROJECT_DIR) run docr-mcp --library vercel
	@echo "✅ Done! Restart Claude Code to activate."

add-twilio:
	@echo "Adding Twilio MCP server to Claude Code..."
	@claude mcp add docr-mcp-twilio -- uvx docr-mcp --library twilio
	@echo "✅ Done! Restart Claude Code to activate."

add-twilio-local:
	@echo "Adding Twilio MCP server (local development)..."
	@claude mcp add docr-mcp-twilio-local -- uv --directory $(PROJECT_DIR) run docr-mcp --library twilio
	@echo "✅ Done! Restart Claude Code to activate."

add-openai:
	@echo "Adding OpenAI MCP server to Claude Code..."
	@claude mcp add docr-mcp-openai -- uvx docr-mcp --library openai
	@echo "✅ Done! Restart Claude Code to activate."

add-openai-local:
	@echo "Adding OpenAI MCP server (local development)..."
	@claude mcp add docr-mcp-openai-local -- uv --directory $(PROJECT_DIR) run docr-mcp --library openai
	@echo "✅ Done! Restart Claude Code to activate."

add-stripe:
	@echo "Adding Stripe MCP server to Claude Code..."
	@claude mcp add docr-mcp-stripe -- uvx docr-mcp --library stripe
	@echo "✅ Done! Restart Claude Code to activate."

add-stripe-local:
	@echo "Adding Stripe MCP server (local development)..."
	@claude mcp add docr-mcp-stripe-local -- uv --directory $(PROJECT_DIR) run docr-mcp --library stripe
	@echo "✅ Done! Restart Claude Code to activate."

add-anthropic:
	@echo "Adding Anthropic MCP server to Claude Code..."
	@claude mcp add docr-mcp-anthropic -- uvx docr-mcp --library anthropic
	@echo "✅ Done! Restart Claude Code to activate."

add-anthropic-local:
	@echo "Adding Anthropic MCP server (local development)..."
	@claude mcp add docr-mcp-anthropic-local -- uv --directory $(PROJECT_DIR) run docr-mcp --library anthropic
	@echo "✅ Done! Restart Claude Code to activate."

# Authenticated Documentation Configurations

This directory contains configuration templates for authenticated/private documentation that requires authentication (cookies, session tokens, etc.).

## Available Auth Methods

### Cookie-based Authentication

For documentation sites that use cookie-based authentication (e.g., Okta SSO, session cookies, JWT cookies).

**Use cases:**
- Internal company wikis
- Private product documentation
- SSO-protected knowledge bases

**Quick Start:**

1. **Copy the example config:**
   ```bash
   cd config/authenticated/
   cp cookie.example.yml my-internal-docs.yml
   ```

2. **Get your auth cookies from browser DevTools:**
   - Open your browser and log in to the authenticated docs site
   - Open DevTools (F12 or right-click > Inspect)
   - Go to Network tab → refresh the page
   - Click on any request to your docs domain
   - Look at Request Headers → Cookie
   - Copy the entire cookie string

3. **Update your config file** (`my-internal-docs.yml`):
   ```yaml
   name: "My Internal Docs"
   description: "Internal company documentation"
   parser: cookie
   
   auth:
     cookie: "session=abc123; token=xyz; ..."  # Paste your cookies here
     allowed_domains:
       - "internal.mycompany.com"              # Your docs domain
   
   index:
     source: "https://internal.mycompany.com/sitemap.xml"  # Or llms.txt
   ```

4. **Run the server:**
   ```bash
   uv run docr-mcp --library my-internal-docs
   ```

**Important notes:**
- Cookies may expire - refresh them if you get auth errors
- Never commit config files with real cookies to git (already in `.gitignore`)
- Domain whitelist prevents accidental access to other sites

## Future Auth Methods

We plan to support additional authentication patterns in future releases:

- **Bearer Token** - for API token authentication (not yet implemented)
- **HTTP Basic Auth** - for username/password authentication (not yet implemented)
- **API Key** - for API key in headers (not yet implemented)

Currently, only cookie-based authentication is implemented. To add other auth methods, extend `BaseDocr` and override `_get_client_config()`.

## Security Best Practices

1. **Never commit credentials**: Config files with real cookies are automatically excluded by `.gitignore`
2. **Domain whitelist**: Always specify `allowed_domains` to prevent SSRF attacks
3. **HTTPS only**: The docrs enforce HTTPS-only connections
4. **Rotate credentials**: Regularly refresh cookies and tokens when they expire
5. **Local use only**: These configs are for local development - don't deploy them to public servers

## Contributing

To add a new authentication method:

1. Create a new docr in `src/docr_mcp/docrs/authenticated/` (e.g., `bearer.py`)
2. Implement `BaseDocr` interface with auth logic
3. Create example config in this directory (e.g., `bearer.example.yml`)
4. Update this README with usage instructions
5. Add tests in `tests/docrs/authenticated/`
6. Register the docr in `src/docr_mcp/docrs/__init__.py`

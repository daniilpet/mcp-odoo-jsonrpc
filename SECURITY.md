# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public issue
2. Use [GitHub Security Advisories](https://github.com/daniilpet/mcp-odoo-jsonrpc/security/advisories/new)
3. Include: description, reproduction steps, potential impact

We will respond within 48 hours and provide a fix timeline.

## Security Model

This project connects AI assistants to corporate Odoo ERP systems.
See [ADR-005: Security Model](docs/adr/005-security-model.md) for details.

### Key security features

- **Restricted mode** (default): AI sees only structural data (IDs, stages, hours).
  No task names, descriptions, or messages are exposed.
- **Full mode**: explicit opt-in via `ODOO_TRUST_MODE=full`
- **Project filter**: `ODOO_ALLOWED_PROJECTS` limits accessible projects
- **Secure credentials**: `session_id` stored in system keyring when available
- **No hardcoded secrets**: all credentials via environment or keyring

### Known limitations

- `session_id` cookie provides full access to user's Odoo account
- Session expiration requires re-authentication
- Odoo JSON-RPC is an internal protocol without stability guarantees

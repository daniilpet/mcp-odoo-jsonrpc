# Contributing

Contributions are welcome! This project provides MCP and CLI access
to Odoo ERP tasks and timesheets via JSON-RPC.

## Scope

Current scope is **project tasks + timesheets** for Odoo 17.
Other Odoo modules (CRM, Sales, Inventory, etc.) are out of scope
for now but may be added in the future.

## Development Setup

```bash
git clone https://github.com/your-username/mcp-odoo-jsonrpc.git
cd mcp-odoo-jsonrpc
pip install -e ".[dev]"
playwright install chromium  # for browser login
```

## Architecture

The project follows DDD with Conformist + Anti-Corruption Layer pattern:

```
ACL Transport (httpx) → ACL Protocol (JSON-RPC) → ACL Mapper → Domain Models
                                                                          ↓
                                                              MCP Server / CLI
```

See [Architecture docs](docs/architecture/context-map.md) for details.

## Making Changes

1. Create a branch: `feature/your-feature` or `fix/your-fix`
2. Follow existing code patterns and conventions
3. Ensure `ruff check src/` passes
4. Test with a real Odoo instance if possible
5. Submit a Pull Request

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(acl): add support for project.milestone model
fix(mapper): handle missing employee_id in timesheets
docs(adr): add ADR-006 for timesheet aggregation
```

## Adding New Odoo Endpoints

1. Capture the request/response from Odoo DevTools or `dev/capture.py`
2. Document in `docs/api/odoo-jsonrpc-reference.md`
3. Add specification constants in `acl/protocol.py`
4. Add mapper function in `acl/mapper.py`
5. Add domain model if needed in `domain/models.py`
6. Add MCP tool in `server.py` and CLI command in `cli.py`

## Security

- Never log or print `session_id` values
- Respect `TrustMode.RESTRICTED` — restricted specs must not fetch sensitive fields
- New tools must support both restricted and full modes
- See [ADR-005](docs/adr/005-security-model.md)

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

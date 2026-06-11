# PYPOST-144: Developer Documentation Updates

## Files Updated

- `doc/dev/tech-debt/PYPOST-21.md` — section 2 (Direct Global Access) marked resolved.

## Summary for Developers

`HTTPClient` and `MCPServerImpl` no longer import a module-level `template_service`
singleton. Both accept `template_service: TemplateService | None = None` and store
`self._template_service`.

See also `ai-tasks/PYPOST-45/70-dev-docs.md` for the full dependency chain and testing
patterns.

### Quick reference

```python
from unittest.mock import MagicMock
from pypost.core.http_client import HTTPClient
from pypost.core.mcp_server_impl import MCPServerImpl

mock_ts = MagicMock()
client = HTTPClient(template_service=mock_ts)
server = MCPServerImpl(template_service=mock_ts)
```

Tests: `TestHTTPClientInjection`, `TestMCPServerImplInjection`.

# PYPOST-719: Dev Docs

No new documentation file needed. MCPServerManager test patterns are self-evident
from `tests/test_mcp_server_manager.py`. The approach of mocking `create_app` and
`uvicorn.Server.serve` for pure unit tests is documented inline in the
`TestMCPServerManagerUnit` class docstring.

# PYPOST-81: Dev Docs

## Updated Files

No `doc/dev/` changes required. Style placement is self-evident in source and covered by
PEP 8 / `.cursor/lsr/do-python.md`.

## Key point for maintainers

In `pypost/core/mcp_server_impl.py`, keep `logger = logging.getLogger(__name__)` as the
first module-level statement after all import blocks (stdlib, third-party, then `pypost`).

# PYPOST-157: Dev Docs

## Updated

- `doc/dev/mcp_integration.md` — documented that `MessagesEndpoint` has no Response dependency and
  that 405 on wrong methods is owned by Starlette `Route` filtering (PYPOST-157).

## Notes

Complements PYPOST-155 (Route-based POST) and PYPOST-156 (module extraction).

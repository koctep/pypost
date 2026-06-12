# PYPOST-159: Dev Docs

## Updated

- `doc/dev/mcp_integration.md` — added **Legacy SSE ASGI efficiency (PYPOST-159)** subsection
  documenting Mount vs Route wrapping, direct ASGI on POST `/messages`, and intentional
  `request_response` on GET `/`.

## Notes

Complements PYPOST-155 (Route method filtering), PYPOST-156 (module extraction), and PYPOST-161
(ASGI registration tests). No routing code changes.

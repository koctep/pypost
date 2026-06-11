# PYPOST-144: Code Cleanup

## Lint / Format

- `./scripts/lint.sh tests/test_mcp_server_impl.py` — pass
- `./scripts/check-line-length.sh tests/test_mcp_server_impl.py` — pass

## Verification

```bash
rg "from pypost\.core\.template_service import template_service" pypost/
# no matches

rg "template_service = TemplateService\(\)" pypost/core/template_service.py
# no matches
```

## Notes

- No production code changes required; injection landed in PYPOST-45.
- Only new test class `TestMCPServerImplInjection` added for this ticket.

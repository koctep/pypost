# PYPOST-179: Dev Docs (Step 7)

## Updated

- `doc/dev/testing.md` — fixture generator section with run and `--check` commands.
- `config/test/README.md` — regenerate instructions before copying to user data dir.

## Operator commands

```bash
# Regenerate committed fixtures
.venv/bin/python scripts/generate_mcp_test_fixtures.py

# Verify fixtures match builders (CI-friendly)
.venv/bin/python scripts/generate_mcp_test_fixtures.py --check
```

## Related

- PYPOST-180 groundwork tests: `tests/test_mcp_test_collection.py`
- PYPOST-181 integration tests: `tests/test_mcp_test_collection_integration.py`

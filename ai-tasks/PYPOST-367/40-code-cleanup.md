# PYPOST-367: Code Cleanup

## Lint

- `./scripts/lint.sh tests/test_mcp_server_impl.py` — pass
- `./scripts/check-line-length.sh tests/test_mcp_server_impl.py` — pass

## Formatting

- Imports grouped: stdlib, third-party (`mcp`, `starlette`), project.
- Module docstring updated to mention routing coverage.

## Dead Code

- None introduced.

## Test Timeouts

- Module-level `pytestmark = pytest.mark.timeout(60)` covers all test classes.

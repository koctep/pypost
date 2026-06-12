# PYPOST-671: Code Cleanup

## Scope

Single-file change: `.github/workflows/test.yml` (Run tests step + downstream script inputs).

## Checks

- [x] No trailing whitespace or formatting drift.
- [x] `pytest.ini` untouched — local defaults preserved.
- [x] Verifier step still reads `pytest.log` (now from `--log-file`, not tee).
- [x] Duration audit step reads `pytest-output.txt` (tee of pytest stdout).
- [x] No duplicate or dead workflow steps introduced.

## Validation

```bash
# Workflow syntax (if act or manual CI run unavailable, review diff only)
grep -A3 'log_cli=false' .github/workflows/test.yml
grep 'pytest-output.txt' .github/workflows/test.yml
```

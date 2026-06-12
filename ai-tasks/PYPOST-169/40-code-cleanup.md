# PYPOST-169: Code Cleanup

## Checklist

- [x] Module docstring references PYPOST-169 and PYPOST-563.
- [x] Shared helpers (`_free_port`, `_wait_for_port`) reused — no duplication.
- [x] Explicit `pytest.mark.timeout(120)` at module scope (integration tier).
- [x] Bounded `_wait_for_port` and `urlopen(..., timeout=5.0)`.
- [x] No unused imports; LF endings; lines ≤ 100 characters.

## Files Touched

- `tests/test_metrics_server_integration.py`

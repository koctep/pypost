# PYPOST-414: Code Cleanup

## Scope

Verification task — no production or test code edits in PYPOST-414.

## Pre-existing cleanup (PYPOST-403)

| File | Change |
|------|--------|
| `pypost/core/http_client.py` | Default `TemplateService()` when argument is `None` |
| `pypost/core/history_manager.py` | `flush()` + retained `_save_thread` reference |
| `tests/test_http_client_sse_probe.py` | `TemplateService()` in `setUp` |
| `tests/test_history_manager.py` | `hm.flush()` before temp-dir teardown |

## PYPOST-414 review

- No dead code introduced.
- No duplicate fixes applied.
- No formatting-only churn.

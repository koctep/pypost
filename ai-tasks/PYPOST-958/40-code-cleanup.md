# PYPOST-958: Code Cleanup Report

## Lint / Format

- `make lint` — clean on touched test module and inventory gate.
- Module-level `pytestmark = [timeout(60), agent_e2e]` on new scenario module.
- Constants mirror `tests/test_agent_e2e_http_mapping_multi_url.py` panel helpers.

## Scope

Test-only change:

- `tests/test_agent_e2e_http_mapping_compound_keys.py` (new)
- `tests/test_agent_e2e_http.py` (inventory gate)

No production files modified.

## Notes

- `_CANNED_SHARED_POST_OK` uses `make_canned_http_result(url=_SHARED_URL, …)`
  so POST compound key resolves to the same URL filled in the editor.
- Reuses shared `wait_response_after_snapshot` — no local `_wait_response` copy.

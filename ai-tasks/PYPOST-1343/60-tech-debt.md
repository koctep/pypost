# PYPOST-1343: Technical Debt Analysis

## Shortcuts Taken

- **GitLab bodies not rewritten to `to_json`.** Curated GitLab write fields are strings
  (labels are comma-separated). Rewriting every `to_json_string` call would churn locked
  tests without a type-preservation win. Docs note `to_json` is available for future typed
  fields. Acceptable for this task's DoD.
- **No dedicated `to_json` failure metric/log.** Non-serializable values raise via
  `json.dumps`; existing template/request error paths surface the failure. Matches
  `to_json_string` / pure helper style.

## Code Quality Issues

- Optional field guards in GitHub/GitLab bodies remain verbose
  (`mcp is defined and mcp.request is defined and … is not none`). A future "emit JSON
  object from present args" helper (called out in PYPOST-1334 TD-6) would shrink templates
  further; out of scope here.
- `_synthetic_request` in `tests/test_github_mcp_collection.py` still builds bodies with
  `to_json_string` for every body arg. That is only for in-memory checker twins, not the
  on-disk collection; low risk.

## Missing Tests

- No live GitHub workflow_dispatch test proving remote acceptance of JSON boolean/number
  input values (offline suite locks PyPost render behavior only). Same offline policy as
  other MCP collections.
- No explicit test that `to_json` raises `TypeError` on a non-serializable object (fail-
  closed behavior is `json.dumps` default). Optional hardening.

## Performance Concerns

None. `json.dumps` on small MCP argument graphs is negligible vs HTTP.

## Follow-up Tasks

1. **Optional — exercise `to_json` TypeError path in unit tests** (Lowest)
   Assert a clearly non-serializable value fails closed. No Jira filed (tiny).
2. **Pre-existing lint gate** — `NON-BLOCKER — pre-existing`
   `tests/test_mcp_server_registry.py:308` E501 (111 > 100) breaks `make lint` /
   `lint-tests` before `flake8 pypost/`. Introduced with PYPOST-1362; not caused by this
   task. Consider wrapping the comment or updating the test-lint baseline.
3. No new Debt tickets required for the core helper; PYPOST-1334 TD-6 is addressed by this
   issue.

### Validation

- Focused: `make test PYTEST_ARGS='tests/test_json_string_to_json.py
  tests/test_function_registry.py tests/test_github_mcp_collection.py
  tests/test_gitlab_mcp_collection.py
  tests/test_pypost_1077_verification_artifacts.py::test_function_catalog_expectation_is_the_exact_catalog_frozenset'`
  — all passed
- `make verify-ai-tasks` — OK

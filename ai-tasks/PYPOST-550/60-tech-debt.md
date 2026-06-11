# PYPOST-550: Technical Debt Analysis

## Shortcuts Taken

- **Callable supplier over explicit sync mechanism** — `EnvPresenter` caches
  `_current_variables` on the main thread and exposes a lambda supplier. This mirrors
  `TabsPresenter` but duplicates the cache pattern; a shared env-variable snapshot
  service could reduce duplication in a future refactor.
- **Module-level merge helper** — `_merge_execution_variables` is a standalone function
  rather than a method, for easy unit testing. Acceptable trade-off; no functional debt.

## Code Quality Issues

- **`MCPServerManager._variable_supplier`** stores the supplier reference but only forwards
  it to `_impl`; the manager field is unused after `set_variable_supplier`. Harmless but
  could be removed or used for diagnostics.
- **`EnvPresenter.current_variables` property** reads directly from the Qt combo box while
  MCP uses `_current_variables` cache via the supplier. Both should stay in sync because
  `_on_env_changed` updates the cache, but the dual source is a mild consistency risk if
  future code updates the combo without calling `_on_env_changed`.

## Missing Tests

- **EnvPresenter supplier wiring** — No test asserts that `set_variable_supplier` is called
  on init or that the registered supplier returns `_current_variables` after
  `_on_env_changed`. Covered indirectly via integration tests on `MCPServerImpl`, but
  presenter wiring is untested.
- **Manager forwards supplier** — No unit test for `MCPServerManager.set_variable_supplier`
  propagating to `_impl`.
- **Full GUI↔MCP parity E2E** — Parity is proven at `RequestService` level
  (`test_execute_request_sync_parity_with_request_service`) and via live SSE integration,
  but no end-to-end test runs the real `EnvPresenter` → `MCPServerManager` → agent
  round-trip with env placeholders.
- **Env var named `mcp`** — Collision semantics are unit-tested on `_merge_execution_variables`
  but not documented for end users.

## Performance Concerns

- **Supplier invoked per `call_tool`** — Intentional for freshness (FR-4). Cost is a
  `dict()` copy of typically small env-var maps; negligible for expected usage.
- **No concern** for thread safety beyond the documented main-thread cache + snapshot copy
  pattern.

## Follow-up Tasks

| Item | Suggested action | Jira |
| --- | --- | --- |
| EnvPresenter supplier test | Add `test_registers_variable_supplier_on_init` and `test_supplier_returns_current_variables_after_env_change` in `tests/test_env_presenter.py` | [PYPOST-575](https://pypost.atlassian.net/browse/PYPOST-575) |
| Manager supplier propagation | Add unit test in `tests/test_mcp_server.py` (or existing manager tests) | [PYPOST-576](https://pypost.atlassian.net/browse/PYPOST-576) |
| User docs for `mcp` env key | Documented in `doc/dev/mcp_integration.md` (PYPOST-550 Step 7) | — |
| Shared env snapshot | Optional refactor: extract env-variable cache from `EnvPresenter`/`TabsPresenter` into a small core service | [PYPOST-577](https://pypost.atlassian.net/browse/PYPOST-577) |

## Deviations from Architecture

None. Implementation matches the Step 2 plan: supplier injection, merge at MCP adapter
boundary, main-thread cache, snapshot copy, `mcp` namespace wins on merge.

## Explicit Non-Debt

- No changes to `RequestService`, `TemplateService`, or `HTTPClient` — by design.
- Hidden-variable masking unchanged; MCP inbound path correctly omits `hidden_keys`.
- All new and touched tests declare explicit `pytest.mark.timeout` markers.

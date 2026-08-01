# PYPOST-934: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: `test_agent_dialog_settle_timeout_includes_step_and_modal_diag`
forces dialog-settle timeout via an impossible predicate inside the modal-safe
`QTimer.singleShot` callback, mirrors the PYPOST-919 rewrap (`step=SETTLE_STEP`,
`**_modal_diag()`), and asserts step + modal scalar keys on
`UiWaitTimeoutError.diagnostics`. Module stays green under
`make test-agent-e2e` (2 tests, ~0.8 s). Happy-path proof unchanged.
Closes [PYPOST-919](https://pypost.atlassian.net/browse/PYPOST-919) TD-1.

## Shortcuts Taken

- **Inline rewrap duplication.** The companion copies the happy-path
  `UiWaitTimeoutError` rewrap block (~15 lines) instead of extracting a shared
  helper. Intentional minimal scope; second proof in the module now satisfies
  the PYPOST-936 trigger (see Follow-up Tasks).
- **Timer-before-`exec` settle.** Same modal-safe scheduling as PYPOST-919 —
  required because `SettingsDialog.exec()` blocks `ui_click`; not a test
  crutch.
- **Key presence, not value asserts.** Companion checks `dialog_title` and
  `active_modal_type` keys exist (values may be `None` or Settings-scoped).
  Matches golden Send companion posture for `response_excerpt`; near-zero budget
  may expire before the modal is fully visible.
- **No `caplog` on DEBUG `ui_wait_timeout`.** Exception diagnostics are the
  primary regression signal — same as golden forced-timeout companion and
  PYPOST-838 posture.
- **Single session per test.** One `agent_e2e_session` fixture use per test
  function; avoids known multi-session-after-modal segfault risk
  ([PYPOST-429](https://pypost.atlassian.net/browse/PYPOST-429) lineage).
- **`settle_error` list for async callback.** Timer callback exceptions cannot
  use outer `pytest.raises` around blocking `ui_click`; list capture is local
  and clear.

## Code Quality Issues

- **Duplicated rewrap + timer skeleton** across happy-path and companion
  callbacks. Acceptable for two tests; extract when PYPOST-936 lands.
- **Hardcoded dialog title** `"Settings"` in `_settings_dialog_present()` —
  inherited from PYPOST-919; couples predicate to `setWindowTitle`. Low risk;
  widget id decouples ([PYPOST-935](https://pypost.atlassian.net/browse/PYPOST-935)).
- **`FORCED_SETTLE_TIMEOUT_S = 0.05`** mirrors golden inline budget — not
  centralized; fine at two call sites.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Settings open → dialog present (happy path) | Covered (PYPOST-919) |
| Forced timeout → `step` + modal scalars | **Covered** (this story) |
| Fail-closed `reject()` on forced path | Covered (`finally` in companion) |
| DEBUG `ui_wait_timeout` via `caplog` | Not asserted (optional; golden parity) |
| Specific modal title/type values at timeout | Not asserted (by design) |
| Full product dialog matrix | Out of scope |
| Settings functional behavior | Out of scope (existing suites) |
| Explicit timeout markers | **Present** — module `pytestmark` includes `timeout(60)` |

No timeout-marker blockers (`.cursor/lsr/do-testing.md`).

## Performance Concerns

None. Forced settle uses a 0.05 s budget inside a 60 s module timeout; two
agent_e2e tests complete in under one second offscreen. No new production log
volume or metrics.

## Deviations from Architecture

None material. Delivered path matches `20-architecture.md`: sibling test in
existing module, impossible predicate + near-zero budget, async exception
capture, fail-closed dismiss, scalar diagnostics asserts. Deferred items were
pre-named in architecture and remain sibling-owned.

## Follow-up Tasks

### Closed by this story

| ID | Priority | Item | Notes |
| --- | --- | --- | --- |
| TD-1 | Medium | Agent e2e timeout companion for dialog settle diagnostics | **Done** — `test_agent_dialog_settle_timeout_includes_step_and_modal_diag` |
| | | | Source: [PYPOST-919](https://pypost.atlassian.net/browse/PYPOST-919) TD-1 |

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| `SETTINGS_DIALOG` widget identity | [PYPOST-935](https://pypost.atlassian.net/browse/PYPOST-935) (PYPOST-919 TD-2) |
| Shared modal settle helper | [PYPOST-936](https://pypost.atlassian.net/browse/PYPOST-936) (PYPOST-919 TD-3) — second proof now in module |
| Qt/PySide segfault infrastructure | [PYPOST-429](https://pypost.atlassian.net/browse/PYPOST-429) lineage |
| `QListView` / generic item view in `ui_select` | [PYPOST-939](https://pypost.atlassian.net/browse/PYPOST-939) (unrelated surface) |

### NON-BLOCKER

| ID | Priority | Item | Notes | Jira |
| --- | --- | --- | --- | --- |
| TD-2 | Low | Dev doc cross-reference for forced-timeout companion | **Done** (Step 8) — timeout companion note in `doc/dev/agent_dialog_settle.md` | — |
| TD-3 | Low | `caplog` assert on `ui_wait_timeout` for forced path | Only if DEBUG log regression becomes a recurring CI blind spot; golden companion also omits | Jira: [PYPOST-968](https://pypost.atlassian.net/browse/PYPOST-968) |

### Accepted / out of scope (do not ticket)

- Migrate `SettingsDialog` / `open_settings` from `exec()` to `open()` —
  product change; architecture explicitly out of scope.
- Full dialog matrix / Settings functional e2e via agent — requirements out
  of scope.
- Second-session Qt segfault after modal — pre-existing infrastructure under
  PYPOST-429, not new debt from this story.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | Timer-before-exec required for live modal; inline rewrap intentional |
| Missing tests with timeout markers | **None** — `timeout(60)` on module |
| Deviations from architecture | None |
| Hardcoded values | Title string + 0.05 s budget — Low; title tracked under PYPOST-935 |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — PYPOST-919 TD-1 coverage gap is closed; remaining items are
identity hygiene (PYPOST-935), optional helper extraction (PYPOST-936), and
optional `caplog` polish (TD-3), not acceptance gaps.

# PYPOST-919: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: `agent_e2e` coverage opens Settings via `SETTINGS_BUTTON`,
settles with shared `wait_until` on `QApplication.activeModalWidget()`,
rewraps timeout with `step=wait_dialog_after_settings_open`, and dismisses
the modal so CI cannot hang. Sibling module keeps the Send golden
single-purpose (FR6). No production API changes.

## Shortcuts Taken

- **Sibling `agent_e2e` module, not inside Send golden.** Placement matches
  architecture (Jira allows golden **or** `agent_e2e`). Send → response
  assertions untouched.
- **Timer-before-`exec` settle.** `QTimer.singleShot` runs
  `wait_until` + `reject()` before/during `ui_click` because
  `SettingsDialog.exec()` blocks the click slot. Industry + in-repo pattern;
  not a production crutch.
- **Happy-path only.** Optional timeout companion (assert diagnostics
  include `step`) deferred — a second `agent_e2e_session` after the modal
  path segfaulted locally during Step 4. FR3 diagnosability is implemented
  in the rewrap path but not asserted by a dedicated red/green timeout
  test.
- **Presence via title + type, not widget id.** Predicate uses
  `windowTitle() == "Settings"` and `isinstance(..., SettingsDialog)`.
  `SettingsDialog` still has no `objectName` / `SETTINGS_DIALOG` identity
  (architecture deferred).
- **No change to production `exec()`.** Migrating Settings to `open()` +
  async finish remains out of scope (accepted product posture).

## Code Quality Issues

- **Hardcoded dialog title string** `"Settings"` in the settle predicate —
  couples the test to `SettingsDialog.setWindowTitle`. Low risk while the
  title is stable; a widget id would decouple (TD-2).
- **Modal settle pattern inlined** in one test module. Fine for a single
  proof; extract a shared helper only if more product-dialog settle
  scenarios appear (TD-3).
- **`settle_error: list[BaseException]`** carries exceptions across the
  nested event loop — clear and local; no production impact.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Settings open → dialog present via `wait_until` | Covered |
| Fail-closed `reject()` so `exec` returns | Covered (happy path) |
| Timeout rewrap includes `step` + modal scalars | Implemented; **no**
  companion assert (TD-1) |
| Full product dialog matrix | Out of scope |
| Settings functional behavior | Out of scope (existing suites) |
| Explicit timeout markers | **Present** — module
  `pytestmark` includes `timeout(60)` |

No timeout-marker blockers (`.cursor/lsr/do-testing.md`).

## Performance Concerns

None. One bounded `wait_until` (10 s budget) inside a 60 s module timeout;
dialog creation is synchronous. No new production metrics or log volume.

## Deviations from Architecture

None material. Delivered path matches
`20-architecture.md` (sibling module, `activeModalWidget` predicate,
`SETTLE_STEP`, fail-closed dismiss). Deferred optional items below were
already named in architecture / Step 4 notes.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| This story (product dialog settle) | PYPOST-919 (closing) |
| Source Medium debt | [PYPOST-852](https://pypost.atlassian.net/browse/PYPOST-852) TD-1 |
| Qt/PySide segfault infrastructure | [PYPOST-429](https://pypost.atlassian.net/browse/PYPOST-429) and related |

### NON-BLOCKER

| ID | Priority | Item | Notes | Jira |
| --- | --- | --- | --- | --- |
| TD-1 | Medium | Agent e2e timeout companion for dialog settle diagnostics | Mirror golden `test_agent_golden_settle_timeout_includes_step_and_excerpt`: force near-zero settle budget inside the timer callback and assert `UiWaitTimeoutError.diagnostics["step"] == "wait_dialog_after_settings_open"` (+ modal scalars). Prefer same-process / no second full session if multi-session after modal still segfaults. | Jira: [PYPOST-934](https://pypost.atlassian.net/browse/PYPOST-934) |
| TD-2 | Low | `SETTINGS_DIALOG` widget id on `SettingsDialog` | Set `objectName` via `widget_ids` so agents can wait by identity instead of title + `isinstance`. Only needed if identity-based dialog waits become common. | Jira: [PYPOST-935](https://pypost.atlassian.net/browse/PYPOST-935) |
| TD-3 | Low | Shared modal settle helper for agent e2e | Extract timer + `wait_until` + fail-closed dismiss if a second product-dialog settle proof appears; avoid premature abstraction for one test. | Jira: [PYPOST-936](https://pypost.atlassian.net/browse/PYPOST-936) |

### Accepted / out of scope (do not ticket)

- Migrate `SettingsDialog` / `open_settings` from `exec()` to `open()` —
  product change; architecture explicitly out of scope.
- Full dialog matrix / Settings functional e2e via agent — requirements out
  of scope.
- Second-session Qt segfault after modal — pre-existing infrastructure;
  tracked under PYPOST-429 lineage, not new debt from this story.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | Timer-before-exec is required for live modal; intentional |
| Missing tests with timeout markers | **None** — `timeout(60)` on module |
| Deviations from architecture | None |
| Hardcoded values | Title string only — Low follow-up (TD-2) |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — product dialog settle after Settings open is proven under
`make test-agent-e2e`; remaining items are optional diagnostics coverage and
identity hygiene, not acceptance gaps.

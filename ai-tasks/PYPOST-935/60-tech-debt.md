# PYPOST-935: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: `SETTINGS_DIALOG` (`pypost_settings_dialog`) is exported
from `widget_ids`, applied on every constructed `SettingsDialog` via
`set_widget_id`, locked by a construction-level unit test, and consumed by
dialog-settle `_settings_dialog_present()` (`objectName` check on
`activeModalWidget()`). Existing dialog-settle `agent_e2e` (2 tests)
remains green. Developer identity catalog and dialog-settle docs updated.
Closes [PYPOST-919](https://pypost.atlassian.net/browse/PYPOST-919) TD-2.

## Shortcuts Taken

- **Modal excluded from `KEY_WIDGET_IDS`.** Settings dialog is not under
  the main window during `exec()`; construction assert is the primary proof
  (architecture decision — same policy as plus-tab chrome ids).
- **Settle still uses `activeModalWidget()`, not `find_widget`.** Dialog is
  not a descendant of `session.window` during modal `exec()`; identity
  decouples presence from title/`isinstance` only.
- **Window title `"Settings"` retained for humans.** Automation prefers
  `objectName`; title remains in `_modal_diag()` for readable timeout output.

## Code Quality Issues

None that block close. Optional later: extract duplicated timer + rewrap
skeleton when [PYPOST-936](https://pypost.atlassian.net/browse/PYPOST-936)
lands (second proof already exists in the module).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Constructed `SettingsDialog` exposes `SETTINGS_DIALOG` | **Covered** |
| Dialog-settle happy path with identity predicate | Covered (PYPOST-919) |
| Forced timeout → `step` + modal scalars incl. `dialog_object_name` | Covered (PYPOST-934) |
| Main-window spot-check for modal id | Out of scope (modal policy) |
| Other product dialogs (confirm/message boxes) | Out of scope (requirements) |
| Settings functional behavior | Out of scope (existing suites) |
| Explicit timeout markers | **Present** — `timeout(60)` on both modules |

No timeout-marker blockers (`.cursor/lsr/do-testing.md`).

## Performance Concerns

None. One `set_widget_id` call at dialog construction; no new polls, logs,
or metrics.

## Follow-up Tasks

### Closed by this story

| ID | Priority | Item | Notes |
| --- | --- | --- | --- |
| TD-2 | Low | `SETTINGS_DIALOG` widget id on `SettingsDialog` | **Done** — closes PYPOST-919 TD-2 |

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Product dialog settle (happy path) | [PYPOST-919](https://pypost.atlassian.net/browse/PYPOST-919) (closed) |
| Dialog-settle timeout companion | [PYPOST-934](https://pypost.atlassian.net/browse/PYPOST-934) (closed) |
| Shared modal settle helper extraction | [PYPOST-936](https://pypost.atlassian.net/browse/PYPOST-936) (PYPOST-919 TD-3) |
| Qt/PySide segfault infrastructure | [PYPOST-429](https://pypost.atlassian.net/browse/PYPOST-429) lineage |

### Accepted / out of scope (do not ticket)

- Migrate `SettingsDialog` / `open_settings` from `exec()` to `open()` —
  product change; parent stories explicitly out of scope.
- Add identities to other product dialogs (confirm boxes, message boxes) —
  requirements out of scope.
- Add `SETTINGS_DIALOG` to main-window `KEY_WIDGET_IDS` spot-check — modal
  lookup pattern documented instead.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None — additive identity stamp |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None |
| Hardcoded values | Title string in `_modal_diag()` only (human-readable diag) |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — PYPOST-919 TD-2 identity hygiene is delivered; remaining
items are sibling-owned helper extraction (PYPOST-936), not acceptance gaps.
No new unticketed follow-ups.

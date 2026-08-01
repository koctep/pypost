# PYPOST-920: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Stable `RESPONSE_STATUS` / `RESPONSE_BODY` ids land in the catalog and
`KEY_WIDGET_IDS`, are applied in `ResponseView.init_ui`, spot-check covers
them (including second-tab roles), and golden settle uses display-form
`wait_for_text`. Architecture boundary held: siblings still on panel walk;
FR7 developer docs completed in Step 8. Items below are non-blocking.
**Do not create Jira tickets in this step** — list unticketed follow-ups
only (orchestrator skips Phase D ticket creation this run).

## Shortcuts Taken

- **Sibling e2e left on panel-walk settle.** Double-body, presentation
  matrix, env, and seed-post flows still use `wait_for_snapshot` +
  `joined_panel_values`. Architecture explicitly deferred full migration;
  golden proves the text-wait path.
- **Timeout-diagnostics lock stays on snapshot.**
  `test_agent_golden_settle_timeout_includes_step_and_excerpt` still forces
  `wait_for_snapshot(lambda _snap: False, …)` then wraps with
  `response_excerpt`. Architecture said keep snapshot unless a text-wait
  equivalent is equally clear — accepted asymmetry with the happy-path
  settle.
- **`AgentAppSession.wait_for_text` remains window-rooted.** First
  matching `objectName` under `session.window` wins (same as pre-existing
  `find_widget` / golden single-tab pattern). No `in_current_tab=` on text
  waits (actions already have that flag).
- **Full `make check` not re-run.** Step 5 validated lint + scoped spot-check
  / golden (6 passed). Same deferral pattern as PYPOST-834.
  (FR7 docs landed in Step 8 — see `70-dev-docs.md`.)

## Code Quality Issues

- None that block close. Implementation matches architecture:
  panel id stays in `__init__`; status/body stamped in `init_ui` after
  create; constants via `set_widget_id` (no inline id literals).
- **`PLUS_TAB_PLACEHOLDER` vs KEY catalog (evaluated, not new debt).**
  Placeholder is a catalog constant outside `KEY_WIDGET_IDS` (chrome; docs
  already say so). `RESPONSE_STATUS` / `RESPONSE_BODY` correctly joined
  `KEY_WIDGET_IDS`. No follow-up from this ticket unless maintainers want a
  broader KEY-membership policy note (already implied in identity docs).

Architecture vs implementation:

| Architecture | Implementation | Assessment |
| --- | --- | --- |
| `RESPONSE_STATUS` / `RESPONSE_BODY` in catalog + `KEY_WIDGET_IDS` | Present | Match |
| Panel `set_widget_id` in `__init__` | Unchanged | Match |
| Status/body `set_widget_id` in `init_ui` | After create | Match |
| Golden settle via display `wait_for_text` | `FIXTURE_BODY_DISPLAY` indent=2 | Match |
| Sibling panel walks unchanged | Confirmed | Match |
| Timeout diagnostics on snapshot | Kept | Intentional |
| FR7 docs in this ticket | Step 8 | Done (`ui_identity` / golden / cross-links) |

## Missing Tests

| Scenario | Status |
| --- | --- |
| Spot-check status/body under current `ResponseView` | Covered |
| Second-tab role ids for status/body | Covered |
| Locale-literal lock via `KEY_WIDGET_IDS` | Covered |
| Golden Send → `wait_for_text` status + display body | Covered |
| Forced timeout carries `step` + `response_excerpt` | Covered (snapshot path) |
| Sibling e2e migrated to status/body text waits | Not covered — follow-up |
| Multi-tab Send settle with tab-scoped `wait_for_text` | Not covered — follow-up |
| Explicit timeout markers on changed modules | Covered (`pytestmark = timeout(60)`) |

**No timeout-marker blockers.**

## Performance Concerns

None for this change. `set_widget_id` is O(1) at construction. Golden
`wait_for_text` polls named widgets instead of full-tree snapshots — cheaper
on the hot path. Sibling snapshot polls remain as before until migrated.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Medium | Migrate sibling agent e2e off panel-walk settle onto `wait_for_text` (`RESPONSE_STATUS` / `RESPONSE_BODY`, display-form body) | Targets: `test_agent_e2e_double_response_body.py`, `test_agent_e2e_presentation_matrix.py`, `test_agent_e2e_http_env.py`, optionally `test_agent_e2e_http_seed_post.py` | [PYPOST-948](https://pypost.atlassian.net/browse/PYPOST-948) |
| TD-2 | Low | Add `in_current_tab` (or root override) to `AgentAppSession.wait_for_text` / related waits | Window first-match is fine for single-tab golden; multi-tab Send proofs need scoped waits (architecture Q&A) | [PYPOST-949](https://pypost.atlassian.net/browse/PYPOST-949) |
| TD-3 | Low | Align golden timeout-diagnostics lock with text-wait settle | Force a short `wait_for_text` miss (or equivalent) while keeping `step` + `response_excerpt` wrapping | [PYPOST-950](https://pypost.atlassian.net/browse/PYPOST-950) |

### Unticketed follow-ups (for orchestrator)

Mark clearly for later sync — **no browse links in this run**:

1. **TD-1** — Sibling e2e panel-walk → `wait_for_text` migration
   (double-body, presentation matrix, env, optional seed-post).
   Priority: Medium. Unticketed.
2. **TD-2** — Tab-scoped text waits on `AgentAppSession`.
   Priority: Low. Unticketed.
3. **TD-3** — Timeout-diagnostics test on text-wait path.
   Priority: Low. Unticketed.

Deferred by design (not Phase D debt from this review):

- Time / size / search chrome ids — architecture out of scope.
- New wait primitive family — out of scope.

## User documentation

N/A — no `doc/user/` changes (requirements out of scope). Developer docs
are Step 8.

## Blocker Review

**SAFE TO CLOSE** — FR1–FR7 satisfied by catalog + apply + spot-check +
golden text-wait settle + Step 8 docs. Listed gaps are non-blocking;
follow-ups above are **unticketed** (no Jira links).

## Worklog

```
tokens_used: 38000
role: execution
step: 7
step_name: Review
```

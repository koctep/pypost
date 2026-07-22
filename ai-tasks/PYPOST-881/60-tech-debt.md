# PYPOST-881: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Optional shared finish-teardown helper extraction remains unnecessary:
inventory still shows **exactly two** consumers (env + collection gateways)
with **no drift** in wait bound or teardown order. Closing as explicit YAGNI
deferral with evidence (PYPOST-829 TD-1 acceptance path).
**Do not create Jira tickets in this step** — no new follow-ups required.

## Shortcuts Taken

- **Did not extract shared helper.** Matches ticket guidance and architecture:
  extract only when a third consumer appears or drift becomes likely.
- **Treated intentional pending-model differences as non-drift.** Env has
  save/load pending; collection is load-only; WARNING field sets differ by
  design.
- **No red/green product change.** Step 3 N/A; decision documented instead of
  inventing a failing test for a non-change.
- **Full `make check` not run.** Docs/decision-only; full gate remains
  [PYPOST-882](https://pypost.atlassian.net/browse/PYPOST-882).

## Code Quality Issues

- None blocking. Duplicated `_WORKER_FINISH_WAIT_MS = 100` and the short
  finish-slot body are acceptable colocation for the original PYPOST-829 pair
  until a third consumer or real drift appears.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Shared finish-teardown helper API | Not applicable — API not introduced |
| H3 finish-path stress canary | Covered (existing; unchanged) |
| Inventory of third consumer / drift | Documented absent (manual inventory) |

Timeout markers: unchanged on existing modules. **No timeout-marker blockers.**

## Performance Concerns

None. No code path changes.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| — | — | None | Reopen/extract only if a third consumer appears or teardown drifts | — |

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| H3 finish-path fix (parent) | [PYPOST-829](https://pypost.atlassian.net/browse/PYPOST-829) |
| Full `make check` after 829 | [PYPOST-882](https://pypost.atlassian.net/browse/PYPOST-882) |
| Shared `qapp` / suite affinity | [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) |
| Sibling YAGNI helper deferral | [PYPOST-879](https://pypost.atlassian.net/browse/PYPOST-879) |

## Inventory evidence (close criteria)

```text
_WORKER_FINISH_WAIT_MS definitions: 2
  - pypost/core/qt/environment_storage_gateway.py (= 100)
  - pypost/core/qt/collection_storage_gateway.py (= 100)
Ordered finish-slot consumers: 2 (same modules)
Third consumer: none
Drift in wait bound / teardown order: none (2026-07-22)
Tabs/code_editor deleteLater connect-site: different pattern (not counted)
```

## User documentation

N/A — internal lifecycle hygiene decision; no `doc/user/` updates. Developer
docs are Step 8.

## Blocker Review

**SAFE TO CLOSE**

- DoD met via YAGNI deferral path: inventory recorded; extract-vs-defer
  decision explicit; no forced refactor; product unchanged.
- No missing pytest timeout markers.
- No BLOCKER or unticketed follow-ups for Phase D.
- Unticketed follow-ups needing Jira: **none**.

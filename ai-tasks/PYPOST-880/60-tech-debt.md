# PYPOST-880: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Full-suite verification after PYPOST-828 found **no harness regressions
attributable to timeout diagnostics**. DoD met by running the gate, classifying
failures, and leaving unrelated debt alone. **Do not create Jira tickets in
this step** — list unticketed follow-ups for the orchestrator.

## Shortcuts Taken

- **Plain `make check` stalled twice** on
  `test_environment_storage_gateway.py::…::test_save_async_emits_save_completed`
  past module `timeout(120)` (signal method ineffective inside nested Qt
  `exec()`). Completed the suite with
  `make test PYTEST_ARGS='tests/ -m "not slow" --timeout-method=thread'`.
  Same test passes in isolation and under that thread method; hang matches
  PYPOST-883 unreproduced-suite noise, not an 828 diagnostic defect.
- **Did not change default pytest-timeout method** in `Makefile` /
  `pyproject.toml` — that would expand into harness policy / 883 territory.
- **Did not fix SOLID LOC or ai-tasks baseline failures** — pre-existing /
  sibling noise, out of scope for this Debt item.

## Code Quality Issues

None introduced. No source edits.

## Missing Tests

| Scenario | Status |
| --- | --- |
| PYPOST-828 timeout diagnostics | Covered; reconfirmed |
| Gateway load/save waits with `process_until` | Covered; reconfirmed |
| Full `make check` green end-to-end | **Blocked by unrelated failures** (below) |
| Classic red for save_async full-suite hang | Owned by PYPOST-883 (not_reproduced) |

Timeout markers: unchanged. **No timeout-marker blockers.**

## Performance Concerns

None from this ticket. Suite wall ~3m16s with thread timeout method.

## Gate evidence (Step 4)

| Check | Result |
| --- | --- |
| `make lint` | Pass |
| Fast suite (`--timeout-method=thread`) | **1723 passed**, 4 failed, 21 deselected |
| Focused 828/consumer cluster | **26 passed** |
| `make verify-ai-tasks` | Fail — new violations for incomplete sibling task folders |

### Failures (not 828-caused)

1. `test_solid_audit_baseline` — `main_window.py` / `MainWindow` / `env_presenter.py`
   LOC over existing caps (429/385/467 vs 425/380/465).
2. `test_baseline_matches_current_scan` / `verify-ai-tasks` — baseline 257 vs
   current 261; new missing `70-dev-docs.md` on PYPOST-887/889/890/891.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Low | Refresh SOLID LOC caps or split modules | `main_window` + `env_presenter` over cap | — (see already-tracked SOLID work; ticket if none open) |
| TD-2 | Low | Refresh ai-tasks artifact baseline / finish incomplete folders | PYPOST-887/889/890/891 missing `70-dev-docs.md` | — (sibling in-progress tasks) |
| TD-3 | Lowest | Consider default `--timeout-method=thread` for Qt suite | Only if plain `make check` keeps stalling on nested `exec()` | — (do not ticket unless hang confirms again) |

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| save_async suite hang investigation | [PYPOST-883](https://pypost.atlassian.net/browse/PYPOST-883) |
| Gateway worker `deleteLater` / short wait | [PYPOST-829](https://pypost.atlassian.net/browse/PYPOST-829) |
| Align gateway tests on shared `qapp` | [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) |
| Wire `worker_operation` | [PYPOST-878](https://pypost.atlassian.net/browse/PYPOST-878) (done) |
| Shared `worker_timeout_detail` helper | [PYPOST-879](https://pypost.atlassian.net/browse/PYPOST-879) |

## User documentation

N/A — verification only; no `doc/user/` updates.

## Blocker Review

**SAFE TO CLOSE**

- DoD met: full gate re-run performed; no PYPOST-828 harness regression found
  or left unfixed; unrelated failures documented without scope expansion.
- No missing pytest timeout markers.
- Unticketed follow-ups needing Jira: **TD-1 only if no open SOLID-cap ticket
  covers current numbers**; TD-2/TD-3 should not be ticketed from this story
  (sibling WIP / optional policy).

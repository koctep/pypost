# PYPOST-882: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Full-suite verification after PYPOST-829 found **no finish-path regressions
attributable to the H3 teardown fix**. DoD met by running the gate,
classifying failures, and leaving unrelated debt alone. **Do not create
Jira tickets in this step** — list unticketed follow-ups for the
orchestrator (this run: no Jira calls by instruction).

## Shortcuts Taken

- **Did not insist on plain `make check`.** Sibling PYPOST-880 evidence:
  plain `make check` can stall on
  `test_environment_storage_gateway.py::…::test_save_async_emits_save_completed`
  under the default signal timeout method inside nested Qt `exec()`.
  Completed evidence with `make lint` +
  `make test PYTEST_ARGS='tests/ -m "not slow" --timeout-method=thread'`
  + `make verify-ai-tasks`. Same classification path as PYPOST-880.
- **Did not change default pytest-timeout method** in `Makefile` /
  `pyproject.toml` — harness policy / PYPOST-883 territory.
- **Did not fix SOLID LOC or ai-tasks baseline failures** — pre-existing /
  sibling noise, out of scope for this Debt item.

## Code Quality Issues

None introduced. No product/harness source edits (docs + task artifacts
only).

## Missing Tests

| Scenario | Status |
| --- | --- |
| PYPOST-829 H3 stress canary | Covered; reconfirmed |
| Gateway unit + responsiveness isolation | Covered; reconfirmed (18) |
| Full `make check` green end-to-end | **Blocked by unrelated failures** (below) |
| Classic red for save_async full-suite hang | Owned by PYPOST-883 (not_reproduced) |

Timeout markers: unchanged. **No timeout-marker blockers.**

## Performance Concerns

None from this ticket. Suite wall ~3m14s with thread timeout method;
focused H3 cluster ~14s.

## Gate evidence (Step 4)

| Check | Result |
| --- | --- |
| `make lint` | Pass |
| Fast suite (`--timeout-method=thread`) | **1723 passed**, 4 failed, 21 deselected |
| Focused 829 / H3 cluster | **18 passed** |
| `make verify-ai-tasks` | Fail — new violations for incomplete sibling task folders |

### Failures (not 829-caused)

1. `test_solid_audit_baseline` — `main_window.py` / `MainWindow` LOC over
   existing caps (429/385 vs 425/380); inventory also lists
   `env_presenter.py` over cap (same class of debt as PYPOST-880).
2. `test_baseline_matches_current_scan` / `verify-ai-tasks` — baseline
   257 vs current 261; missing `70-dev-docs.md` on
   PYPOST-887/889/890/891.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Low | Refresh SOLID LOC caps or split modules | `main_window` over cap | — (see PYPOST-880 TD-1) |
| TD-2 | Low | Refresh ai-tasks baseline / finish folders | Missing `70-dev-docs.md` on 887+ | — (sibling WIP) |
| TD-3 | Lowest | Default `--timeout-method=thread` for Qt | Only if plain check keeps stalling | — (optional) |

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| H3 finish-path product fix | [PYPOST-829](https://pypost.atlassian.net/browse/PYPOST-829) |
| Shared finish-teardown helper | [PYPOST-881](https://pypost.atlassian.net/browse/PYPOST-881) |
| Gateway tests shared `qapp` | [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) |
| save_async suite hang | [PYPOST-883](https://pypost.atlassian.net/browse/PYPOST-883) |
| Full-suite re-check after 828 | [PYPOST-880](https://pypost.atlassian.net/browse/PYPOST-880) |

## User documentation

N/A — verification only; no `doc/user/` updates.

## Blocker Review

**SAFE TO CLOSE**

- DoD met: full gate re-run performed (hang-aware path); no PYPOST-829
  finish-path regression found or left unfixed; unrelated failures
  documented without scope expansion.
- No missing pytest timeout markers.
- Unticketed follow-ups: **TD-1 only if no open SOLID-cap ticket covers
  current numbers**; TD-2/TD-3 should not be ticketed from this story
  (sibling WIP / optional policy).

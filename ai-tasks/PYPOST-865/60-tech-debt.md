# PYPOST-865: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

`--strict-markers` is enabled in `pyproject.toml` `addopts`, required
custom markers (`timeout`, `slow`, `agent_e2e`) remain registered, and
`tests/test_pytest_strict_markers.py` locks the flag + registry via
`tomllib`. Developer policy text is already in `doc/dev/testing.md`
(Step 8 may polish). No product runtime change.
**Do not create Jira tickets in this step** — no new follow-ups required.

## Shortcuts Taken

- **Config-parse guards, not subprocess behavioral proof.** Same family
  as `tests/test_pyproject.py`: assert policy in `pyproject.toml` rather
  than spawning pytest to prove an unknown mark fails collection.
  Pytest’s own `--strict-markers` semantics are trusted once the flag
  is locked present.
- **Hardcoded `_REQUIRED_MARKERS`.** Only the three suite marks known at
  enable time are asserted registered; new marks are enforced by
  collection failures under strict mode, not by expanding this tuple
  automatically.
- **Docs landed before Step 8.** Strict-markers section already present
  in `doc/dev/testing.md`; Step 8 owns final polish / artifact
  `70-dev-docs.md`.
- **Full `make check` not re-run in cleanup.** Focused guard tests +
  Step 4 collection smoke covered the change surface.

## Code Quality Issues

None material. Guard helpers (`_pytest_ini_options`,
`_marker_registered`) are small and match existing config-guard style.
Module `pytestmark = pytest.mark.timeout(10)` satisfies mandatory
timeout rules.

## Missing Tests

| Scenario | Status |
| --- | --- |
| `--strict-markers` present in `addopts` | Covered |
| `timeout` / `slow` / `agent_e2e` registered | Covered |
| Unknown custom marker fails collection | Not automated (pytest behavior + flag lock) |
| Explicit timeout markers on new tests | Covered (module `timeout(10)`) |

No timeout-marker blockers.

## Performance Concerns

None. `--strict-markers` is collection-time only; no measurable impact
on default `make test` (NFR1).

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| — | — | None | Optional subprocess unknown-marker proof is YAGNI | — |

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Enable `--strict-markers` (this task) | [PYPOST-865](https://pypost.atlassian.net/browse/PYPOST-865) |
| Origin debt from agent_e2e packaging | [PYPOST-858](https://pypost.atlassian.net/browse/PYPOST-858) |

### NON-BLOCKER — need NEW Jira Debt tickets (Phase D)

None. Unticketed follow-ups needing Jira: **none**.

## User documentation

N/A — pytest / CI hygiene only; no `doc/user/` impact. Developer docs
are Step 8 (`doc/dev/testing.md` already has the Strict markers section).

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | Config-guard shortcut only; intentional |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None — enable + registry + guard as planned |
| Hardcoded values | `_REQUIRED_MARKERS` tuple (acceptable) |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — FR1–FR5 / DoD met by enabling `--strict-markers`,
keeping registered markers valid, and locking policy with an automated
guard. No BLOCKER or unticketed Phase D follow-ups.

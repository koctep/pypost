# PYPOST-886: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Suite-wide migration of remaining `setUpClass` / local-`qapp` modules onto
shared `tests/conftest.py` `qapp` completed for the inventoried surfaces
(workers → presenters → editors, then remaining dialogs / tree / integration /
settings). Inventory guard reports **zero** remaining local lifecycle owners.
No product changes.
**Do not create Jira tickets in this step** — Phase D / tech-debt sync fills
the Jira column later (this run: no Jira calls per orchestrator).

## Shortcuts Taken

- **Kept `unittest.TestCase` + `usefixtures`.** Did not convert modules to
  free functions with a `qapp` parameter (style polish; PYPOST-885 class).
- **Did not touch `tests/conftest.py` `qapp` scope.** Reused module-scoped
  singleton; no pytest-qt plugin swap.
- **Batch mechanical migration.** Used careful AST/regex transforms; followed
  with blank-line cleanup and targeted restores where scanner/bind-host classes
  temporarily lost `usefixtures`.
- **Full `make check` not re-asserted.** Validation used focused
  `make test` / venv pytest clusters (priority batch **331 passed**; additional
  dialogs/UI batches green). Full-suite SOLID noise remains PYPOST-882.

## Code Quality Issues

- **Two shared-fixture consumption styles remain.** Free-function tests use
  `def test_...(qapp)`; `TestCase` modules use `usefixtures("qapp")`. Both are
  valid; unifying style is optional (PYPOST-885 family).
- **Specialized fixture `qapp_with_styles`.** Now depends on shared `qapp`
  rather than creating its own app; still applies/restores stylesheet locally —
  intentional.
- **Subprocess hang canary in `test_env_presenter.py`.** Child process still
  constructs `QApplication` inside an embedded script string — required for
  isolation; not suite fixture ownership.

No intentional coverage-intent regressions in migrated modules. Timeout markers
retained.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Priority workers / presenters / editors on shared `qapp` | Covered |
| Suite-wide inventory (no local `qapp` / setUpClass QApplication) | Covered (`test_suite_qapp_alignment.py`) |
| Dialogs / settings / style managers local-`qapp` removal | Covered (migrated) |
| Collection tree / main window / integration setUpClass removal | Covered (migrated) |
| Convert TestCase → free functions | Not required |
| Full `make check` green after SOLID noise clears | Deferred — PYPOST-882 |

**No timeout-marker blockers.**

## Performance Concerns

None introduced. Fixture alignment does not change wait budgets. Occasional
native segfault when combining many large Qt modules in one pytest process was
observed once during agent runs; per-module and focused clusters stayed green
(same class of Qt teardown sensitivity already noted historically).

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Lowest | Optional: convert remaining `TestCase` Qt modules to free functions with `qapp` param | Style-only; matches responsiveness | Already tracked: [PYPOST-885](https://pypost.atlassian.net/browse/PYPOST-885) |
| TD-2 | Lowest | Re-run full `make check` when SOLID baseline noise is clear | Scoped gate used here | Already tracked: [PYPOST-882](https://pypost.atlassian.net/browse/PYPOST-882) |
| TD-3 | Lowest | Optional: document intermittent multi-module Qt segfault sensitivity when combining large presenter+editor clusters | Process isolation tip for agents/CI triage; not a product defect | Unticketed |

### Unticketed follow-ups (for orchestrator)

1. **TD-3** — Optional docs/process note about intermittent segfaults when
   combining many large Qt modules in one pytest invocation (per-module runs
   green). Priority: Lowest. Suggest Debt issue only if maintainers want it
   tracked; otherwise fold into `gui_testing.md` troubleshooting in a future
   docs pass (this ticket already notes it lightly in Step 8).

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Gateway shared-`qapp` alignment | [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) (done) |
| Collection worker shared-`qapp` | [PYPOST-884](https://pypost.atlassian.net/browse/PYPOST-884) (done) |
| Suite-wide shared-`qapp` migration (this ticket) | [PYPOST-886](https://pypost.atlassian.net/browse/PYPOST-886) |
| Optional TestCase → free-function style | [PYPOST-885](https://pypost.atlassian.net/browse/PYPOST-885) |
| Full `make check` after sibling noise | [PYPOST-882](https://pypost.atlassian.net/browse/PYPOST-882) |
| Hang-resistant shared `process_until` | [PYPOST-827](https://pypost.atlassian.net/browse/PYPOST-827) (done) |

### Remaining inventory

**None** for local `def qapp()` / `setUpClass`+`QApplication` ownership (guard
green). Subprocess canary strings and stylesheet wrapper fixtures are not
counted as remaining debt.

## User documentation

N/A — test-harness consistency only; no `doc/user/` updates. Developer docs are
Step 8.

## Blocker Review

**SAFE TO CLOSE**

- DoD met: workers → presenters → editors migrated; remaining suite inventory
  also cleared; alignment guard green; focused batches green; no product change.
- TD-1–TD-2 already ticketed; TD-3 optional Lowest unticketed process note.
- No missing pytest timeout markers on scoped modules.

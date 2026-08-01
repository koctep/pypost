# PYPOST-922: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: documented `make test-agent-e2e` packaging path for the
**broader** agent e2e pack **beyond golden**, with `make help` framing,
umbrella / golden / testing docs, and contract locks. Runtime selection
was already broader; this story closed discoverability. **Do not create
Jira tickets in this step** — list unticketed follow-ups only.

## Shortcuts Taken

- **Reused existing `test-agent-e2e` target** (architecture Option A)
  instead of a sibling `test-agent-e2e-broader` name — one entry, wording
  must stay clear (locked by tests).
- **Substring / token doc locks** rather than structured doc schema —
  same pattern as other packaging/CI doc guards; brittle if prose is
  rephrased without tokens.
- **Full `make check` / full suite not re-run.** Validated flake8 on
  touched tests + 9 targeted contract tests.
- **Sibling docs** (`setup.md`, lifecycle, gui_testing, etc.) still use
  older “env pack” phrasing in places; primary FR surface is the three
  locked docs + help. Remaining soft wording is Step 8 / Low follow-up.

## Code Quality Issues

- Recipe-body / help parsers in `test_makefile.py` are local helpers;
  optional later share with other Makefile contract tests (Lowest).
- Makefile `##` help lines routinely exceed 100 characters (existing
  project pattern); not rewritten.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Help / `##` frames broader beyond golden | Covered |
| Default recipe marker, not golden-only path | Covered |
| Docs: primary packaging + beyond golden + PYTEST_ARGS narrow | Covered |
| PYPOST-922 attribution in packaging docs | Covered |
| Live full pack run / CI topology change | Out of scope |
| Every sibling `doc/dev/*` soft-wording update | Not locked — Step 8 |

Timeout markers: module `pytestmark` on both lock surfaces. **No
timeout-marker blockers.**

## Performance Concerns

- None. Docs / help / unit locks only; no runtime path change. Existing
  3.11 double-run of the pack remains owned by PYPOST-873 (DEFER).

## Follow-up Tasks

1. **Align remaining sibling doc soft-wording with broader-beyond-golden**
   - Priority: Low — **addressed in Step 8**
   - Updated `doc/dev/setup.md`, `gui_testing.md`, `agent_lifecycle.md`,
     `agent_e2e_env.md`, and `doc/dev/README.md` so help blurbs match
     `make help` / `testing.md` primary packaging wording.
   - Files: as listed above
   - Jira: unticketed (closed via Step 8; no ticket needed)

2. **Optional: share Makefile help/recipe parse helpers**
   - Priority: Lowest
   - Deduplicate `_test_agent_e2e_help_comment` /
     `_test_agent_e2e_default_recipe_body` if more make-entry locks land.
   - Files: `tests/test_makefile.py` (or a small test helper module)
   - Jira: [PYPOST-937](https://pypost.atlassian.net/browse/PYPOST-937)

3. **Optional: harden doc locks beyond raw substrings**
   - Priority: Lowest
   - Only if token churn becomes noisy; current 873-style locks match
     project discoverability-debt practice.
   - Files: `tests/test_agent_e2e_broader_packaging_doc.py`
   - Jira: [PYPOST-938](https://pypost.atlassian.net/browse/PYPOST-938)

## Blocker Verdict

**SAFE TO CLOSE** — no blockers relative to DoD. Follow-ups above are
non-blocking. No Jira Debt issues created in this step.

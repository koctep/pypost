# PYPOST-863: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Optional FR2/FR3 soft coverage is delivered: after ready, agent `ui_select`
activates the seeded env, tree-row QTest click opens Seed GET, snapshot
asserts active env / method / URL template, and TemplateService resolve
proves `{{base_url}}` with active variables. Present ≠ active is asserted
and documented. No production inventory or lifecycle changes.

## Shortcuts Taken

- **Test helper instead of production `ui_click_tree_item`.** Tree rows are
  not widgets; viewport `visualRect` click lives in
  `tests/helpers/agent_e2e_tree.py` to avoid growing the agent action API.
- **No HTTP Send.** Soft FR2/FR3 only; Send + stub remains PYPOST-859.
- **URL field keeps template form.** Resolve is via
  `TemplateService.render_string` + `env.current_variables`, not by expecting
  the line edit to show `https://example.test/get`.
- **Coverage green on first run.** Same stance as PYPOST-862: gap was missing
  verification, not a production defect.

## Code Quality Issues

- Tree helper searches only one level of children (collection → requests).
  Sufficient for the fixed seed catalog; deeper nesting would need a walk.
- Snapshot settle timeout fixed at 10s; module timeout remains 60s.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Present ≠ active before drive | Covered in new test |
| `ui_select` → active env in snapshot | Covered |
| Open Seed GET → method + URL in snapshot | Covered |
| `{{base_url}}` resolve via TemplateService | Covered |
| Open Seed POST / body | Not covered (optional) |
| Production tree-item `ui_*` API | Not in scope |
| Caplog for drive path | Not needed (no new events) |

No timeout-marker blockers.

## Performance Concerns

None. One extra offscreen drive on the shared seeded fixture path.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Seed inventory / identity proof | PYPOST-857 (done) |
| Caplog seed failure | PYPOST-862 |
| Inventory drift guard | PYPOST-864 |
| HTTP Send + stub | PYPOST-859 |

### NON-BLOCKER

#### Optional Seed POST drive-then-snapshot

- **Priority:** Low
- **Description:** Mirror GET proof for Seed POST (method + URL + body
  template) if env-pack scenarios need POST open guarantees.
- **Remediation:** Extend `tests/test_agent_e2e_seed.py` when needed.
- **Jira:** (none — leave unticketed until demanded)

#### Production tree-item agent action

- **Priority:** Low
- **Description:** If many scenarios need collection-tree clicks, promote
  `click_tree_row_by_text` into `pypost.agent.ui_actions` with DEBUG logging.
- **Remediation:** Only when helper duplication becomes painful.
- **Jira:** (none)

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | Test-only tree helper — intentional |
| Missing tests with timeout markers | **None** — module `timeout(60)` |
| Deviations from architecture | None |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — acceptance met: agent UI actions after ready,
drive-then-snapshot + resolve, no blank-ready name scan, present vs active
documented.

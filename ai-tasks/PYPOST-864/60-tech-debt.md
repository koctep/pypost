# PYPOST-864: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Lightweight inventory drift guard meets DoD: unit test asserts published
`SEED_*` constants appear in `doc/dev/agent_e2e_seed.md` Inventory section;
module timeout marker; docs updated. No production fixture changes.

## Shortcuts Taken

- **Presence asserts, not markdown table AST.** Full Option C (committed
  golden JSON + round-trip) deferred; token presence is enough for the
  fixed four-row catalog (same rationale as PYPOST-857).
- **Full-file scan after section header check.** Requires
  `## Inventory after bootstrap` then asserts tokens anywhere in the file
  (not only table cells). Acceptable; false negatives for tokens only in
  unrelated sections are unlikely for this page.
- **Does not assert POST body literal.** `SEED_POST_BODY` is not required
  in the inventory table (notes say "JSON body"); ids/names/URLs/`base_url`
  are the published contract.
- **Step 3 used `pytest.fail` placeholder** then Step 4 replaced with real
  asserts (same pattern as PYPOST-862).

## Code Quality Issues

- Token list is duplicated as a tuple of `(const_name, value)` in the test;
  intentional for clear failure messages — not a shared production API.
- Doc Configuration table mentions the guard; Proof + Troubleshooting also
  point at the module (slight repetition for discoverability).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Each published id/name/URL/`base_url` in doc | Covered |
| Inventory section header present | Covered |
| Missing doc file fails clearly | Covered (`is_file` assert) |
| Bidirectional: doc row not in code | Not covered (optional) |
| Committed golden JSON round-trip | Out of scope (full Option C) |
| `SEED_POST_BODY` in inventory table | Not required |

No timeout-marker blockers.

## Performance Concerns

None. Pure unit read of one markdown file.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Seed inventory / identity proof | PYPOST-857 (done) |
| Caplog seed failure | PYPOST-862 |
| Drive-then-snapshot soft proof | PYPOST-863 |
| HTTP determinism | PYPOST-859 |

### NON-BLOCKER

#### Bidirectional / table-row parse

- **Priority:** Low
- **Description:** Also fail when the inventory table lists an id/name that
  is not among current `SEED_*` constants (stale doc rows), or parse table
  rows into structured tuples.
- **Remediation:** Extend
  `tests/test_agent_e2e_seed_inventory_doc.py` if stale-row drift appears.
- **Jira:** (none — leave unticketed until demanded; no Jira this run)

#### Include `SEED_POST_BODY` in inventory doc + guard

- **Priority:** Low
- **Description:** Spell out `{"ping": true}` in the inventory notes and
  assert it in the drift guard if body drift becomes painful.
- **Remediation:** Doc + one tuple entry when needed.
- **Jira:** (none)

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | Presence-only guard — intentional |
| Missing tests with timeout markers | **None** — module `timeout(10)` |
| Deviations from architecture | None — lightweight Option C subset |
| Hardcoded values | Inventory tokens from fixture constants |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — FR1–FR4 satisfied by unit drift guard + docs. Remaining
gaps are optional hardening, not blockers.

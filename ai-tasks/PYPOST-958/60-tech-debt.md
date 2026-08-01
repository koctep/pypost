# PYPOST-958: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: marked `agent_e2e` GUI module
`tests/test_agent_e2e_http_mapping_compound_keys.py` drives GET and POST to
one resolved URL under compound Mapping keys and asserts distinct panel
outcomes. Inventory gate locks the scenario callable. Harness table and HTTP
docs updated. No product runtime change.

## Shortcuts Taken

- **Happy path only.** No timeout companion or caplog smoke — optional
  siblings exist in the mapping multi-URL module family (955 / 957).
- **Blank session + explicit fill.** Matches 901 / seed POST boundary.
- **Seed catalog bodies.** Reuses `SEED_GET_OK_BODY` / `SEED_POST_OK_BODY` for
  panel asserts; only routing keys differ (compound vs distinct URLs).

## Code Quality Issues

None material. Module structure mirrors PYPOST-901 with compound-key map.

## Missing Tests

| Scenario | Status |
| --- | --- |
| GUI same-URL GET+POST compound keys | **Covered** (958) |
| Unit compound keys | Covered (902) |
| GUI distinct URLs | Covered (901) |
| Compound-key timeout companion | Not covered — optional follow-up |
| Compound-key caplog smoke | Not duplicated — 957 covers Mapping install |

## Follow-Up Items

| Item | Priority | Notes | Jira |
| --- | --- | --- | --- |
| Compound-key GUI timeout companion | Lowest | Force near-zero settle after compound GET/POST; assert step + excerpt | — (optional; ticket only if CI lock needed) |

No unticketed blockers. Optional timeout companion deferred — same rationale
as PYPOST-955 POST companion (982): happy-path closes parent debt.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing timeout markers | **None** — module `pytestmark timeout(60)` |
| Deviations from architecture | None |
| Hardcoded values | Test URLs intentional |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE**

# PYPOST-954: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: churn assessed; **HARDEN via shared helper**
(`tests/helpers/packaging_doc_lock.py`) with import contract test; 918
packaging doc locks green (4/4); sibling 922 module refactored for DRY;
`doc/dev/testing.md` updated with 954 decision and semantic HARDEN revisit
triggers.

## Shortcuts Taken

- **Helper DRY instead of semantic harden** — 918 token churn is low; shared
  assert plumbing is the proportionate hardening (938 trigger #3).
- **Refactored 922 module in same change** — avoids leaving duplicate `_read`
  while helper exists.
- **Full `make check` not re-run** — validated focused 14-test packaging lock
  suite.

## Code Quality Issues

- None introduced. Substring tokens remain the accepted trade-off until
  semantic HARDEN triggers fire.

## Missing Tests

| Scenario | Status |
| --- | --- |
| 918: PYPOST-918 attribution | Covered (unchanged tokens) |
| 918: out-of-process + packaging path | Covered |
| 918: no-mix MCPServerImpl tokens | Covered |
| 918: MCP doc cross-links | Covered |
| Helper unit tests | Covered (`test_packaging_doc_lock_helper.py`) |
| Import contract on lock modules | Covered |
| Semantic / schema-based doc assert | Deferred until HARDEN triggers |
| Meta-lock on HARDEN decision prose | Not added — testing.md section sufficient |

**No timeout-marker blockers.**

## Performance Concerns

None. Disk-read unit tests only.

## Follow-up Tasks

### Blockers

None.

### Non-blockers (deferred)

1. **Semantic / structured doc packaging locks**
   - Priority: Lowest — only if documented revisit triggers fire (≥2 prose-only
     lock edits in 90 days, false substring failure, or third module bypassing
     helper)
   - Files: `tests/helpers/packaging_doc_lock.py`, lock modules
   - Jira: **not ticketed this run**

## Blocker Verdict

**SAFE TO CLOSE** — no blockers relative to DoD.

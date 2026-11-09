# PYPOST-1492: Refresh SOLID audit markdown snapshot (mixins.py LOC drift)

## Goals

Keep the committed SOLID audit baseline metrics snapshot synchronized with live, discovered
module size metrics so automated quality gates report true architectural health rather than
stale-document mismatches.

During PYPOST-1324 Step 4 triage, a pre-existing NON-BLOCKER failure was recorded: the SOLID
audit markdown snapshot no longer matched current measurements (filed symptom: `mixins.py`
recorded LOC 1053 versus discovered 1055). That mismatch is unrelated to library-interrupt
work; it is governance-document drift. Leaving it unresolved continues to fail a named
regression test, undermines trust in SOLID / maintainability gates, and distracts maintainers
investigating unrelated changes.

**Business reason (mandatory):** Restore a trustworthy, exact-match contract between the
checked-in SOLID metrics snapshot and the live codebase inventory so CI and local `make`
quality gates stay green when architectural caps are still respected, without weakening those
caps or assertion rigor.

**Implementation language:** Python

## User Stories

- As a **developer** running repository quality gates, I want the SOLID audit snapshot
  regression test to pass when module sizes remain within established caps, so false-positive
  baseline mismatches do not block or obscure real failures.
- As an **architectural maintainer**, I want the committed SOLID baseline metrics document to
  reflect actual measured LOC for monitored modules, so governance records stay accurate and
  reviewable.
- As a **CI / release operator**, I want snapshot equality checks to fail only on real drift
  that has not been intentionally refreshed, so pipeline signal remains reliable.

## Definition of Done

1. **Snapshot Match**: The committed SOLID audit baseline metrics markdown matches the live
   discovered metrics for all monitored modules (exact document equality as enforced by the
   existing snapshot regression test).
2. **Named Gate Green**: The SOLID audit snapshot equality test
   (`TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics` in
   `tests/test_solid_audit_baseline.py`) passes via `make test` with the documented
   pytest target.
3. **Caps Preserved**: No architectural / module size caps are raised solely to silence the
   failure; measured sizes remain within existing caps where they already are.
4. **Assertion Rigor Preserved**: Snapshot and cap verification contracts are not deleted,
   skipped, commented out, or weakened.
5. **Make-Only Verification**: Confirmation uses repository Make targets only
   (`make test`, and related baseline Make targets as applicable)—no raw `pytest` / `python`
   invocations as the workflow interface.
6. **No Product Behavior Change**: Application runtime behavior, public APIs, and user-facing
   features are unchanged; this task addresses governance snapshot currency only.

## Task Description

### Problem

The SOLID audit baseline metrics markdown is a checked-in governance snapshot. A regression
test requires that snapshot to equal the metrics discovered from the current source tree.
After legitimate module growth (without exceeding caps), the snapshot was not refreshed, so
the equality check fails even though architectural ceilings remain intact.

**Filed failure (PYPOST-1324 triage, base `4a40ff6b`):**

- Test: `tests/test_solid_audit_baseline.py` —
  `TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
- Repro: `make test PYTEST_ARGS=tests/test_solid_audit_baseline.py`
- Excerpt at filing: snapshot `mixins.py` LOC 1053 != discovered 1055
- Classification: pre-existing NON-BLOCKER; not caused by PYPOST-1324 library-interrupt changes

**Current reproduction (Step 1 verification):** the same named test still fails. Live discovery
differs from the committed snapshot (observed drift includes `http_client.py` baseline LOC
versus discovered LOC, still under its existing cap). Exact drifted rows may evolve as the
tree changes; the business obligation is full snapshot resynchronization, not a one-row patch
tied only to the original excerpt.

### Scope (in)

- Bring the SOLID audit baseline metrics markdown into exact agreement with current discovered
  metrics for the monitored inventory.
- Confirm the named SOLID snapshot regression test and related Make-driven verification pass
  without relaxing contracts.

### Scope (out)

- Raising or relaxing module / class size caps.
- Refactoring production modules solely to shrink LOC for this ticket.
- Dialog-audit inventory / aggregate coherence work tracked elsewhere (for example
  PYPOST-1475).
- Changing application features, UI behavior, or library-interrupt semantics from PYPOST-1324.
- Weakening, deleting, or bypassing solid-audit baseline tests.

### Main Entities

- **SOLID Metric Snapshot**: Checked-in baseline metrics document recording measured LOC and
  related governance figures for monitored modules.
- **Discovered Module Metrics**: Live size measurements taken from the current source tree for
  the same monitored inventory.
- **Architectural Cap**: Hard upper bound on module or class size used to prevent
  architectural erosion; distinct from the recorded baseline LOC value.
- **Snapshot Equality Gate**: Automated contract that the committed snapshot text matches live
  formatted discovery output.

### Functional Requirements

- **FR-1**: After this task, the committed SOLID audit baseline metrics document must match
  live discovered metrics for every monitored module in the inventory.
- **FR-2**: The existing snapshot equality regression test must pass under the Make-driven
  test entry point.
- **FR-3**: Cap-enforcement behavior for modules already within caps must continue to pass
  without raising those caps for this fix.
- **FR-4**: Developers must retain a Make-only path to verify baseline / snapshot health as
  part of normal repository quality workflows.

### Non-Functional Requirements

- **NFR-1 Accuracy**: Snapshot numbers must be truthful reflections of the current tree, not
  hand-edited approximations that diverge from discovery.
- **NFR-2 Safety**: Governance rigor (caps and equality contracts) must not be diluted.
- **NFR-3 Non-disruption**: No change to product runtime behavior or external user workflows.
- **NFR-4 Tooling**: Repository operations for build, test, and baseline verification follow
  the Make-only standard.

### Constraints and Assumptions

- **Constraint**: Jira-driven scope is PYPOST-1492 only; no unrelated refactors.
- **Constraint**: Make-only repository operations; no raw `pytest` / `flake8` / `pip` as the
  operator interface.
- **Constraint**: Do not increase caps or weaken assertions to force a green result.
- **Assumption**: Observed LOC values remain within existing caps; the defect is stale
  snapshot content, not a new architectural violation requiring redesign.
- **Assumption**: Prior feature work that changed LOC was intentional; this Debt item only
  restores snapshot currency.

## Q&A

- **Q: Why refresh the snapshot instead of deleting or softening the equality test?**
  **A:** The equality contract forces intentional acknowledgment of metric changes. Softening
  it would allow silent drift and weaken SOLID / maintainability governance.

- **Q: Why is this a Debt / NON-BLOCKER rather than a product bug?**
  **A:** Application behavior is unaffected. The failure is a governance document out of sync
  with discovery; it was triaged as pre-existing during PYPOST-1324 and ticketed separately so
  interruptibility work was not blocked.

- **Q: Does fixing only the historically cited `mixins.py` row satisfy Done?**
  **A:** No. Done requires the full committed snapshot to match live discovery so the named
  equality test passes. The filing excerpt identifies the original symptom; current drift may
  involve other monitored modules.

- **Q: Are architectural caps being raised?**
  **A:** No. Caps stay as-is unless a separate, justified ticket addresses a true cap breach.
  This task assumes sizes remain within existing ceilings.

- **Q: Who accepts Step 1?**
  **A:** Under the autonomous Top-Down runner, an independent review gate accepts Step 1; the
  execution agent leaves STEP 1 as `[/]` until that gate passes.

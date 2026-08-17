# PYPOST-1071: Restore a trustworthy fast-suite baseline

## Programming Language

Python is the implementation language of the application. English Markdown records this
workflow's requirements.

## Goals

The fast test suite originally reported nine repeatable failures across six independent causes.
PYPOST-1077 has since restored four established application contracts: dialogue-audit coverage,
the approved function catalog, the read-only Jira capability contract, and encrypted-startup
state restoration.

Five failures remain in two baseline domains: four SOLID-maintainability checks and one committed
AI-task-artifact check. These failures make the suite baseline unreliable because release
stewards cannot tell whether a red result represents an actionable regression or stale reference
data.

**Business goal:** Restore a dependable fast-suite result in which accepted repository state and
real regressions are clearly distinguished, without weakening the maintainability or artifact
integrity protections that the baseline checks provide.

## User Stories

- As a **release steward**, I want the fast suite to produce a trustworthy result, so I can make
  release decisions without discounting known baseline failures.
- As a **maintainer**, I want current maintainability drift to receive an explicit disposition,
  so growth is either accepted transparently or treated as actionable debt.
- As a **maintainer**, I want SOLID checks to keep detecting future unapproved growth, so resolving
  today's failures does not silently weaken regression protection.
- As an **AI-assisted workflow operator**, I want the committed task-artifact baseline to match
  the accepted repository inventory, so unexpected artifact drift remains detectable.
- As a **contributor**, I want the four contracts restored by PYPOST-1077 to remain protected, so
  baseline stabilization does not reintroduce those failures.

## Definition of Done

- [ ] Each of the five remaining baseline failures has an evidence-backed disposition.
- [ ] The SOLID-maintainability baseline represents an explicitly approved current state and
      continues to reject future unapproved regressions.
- [ ] The committed AI-task-artifact baseline represents the accepted current artifact inventory
      and continues to detect future unexpected drift.
- [ ] The four application-contract checks restored by PYPOST-1077 remain successful.
- [ ] The fast test suite completes without any of the original nine failures.
- [ ] No protected check is skipped, removed, or made ineffective merely to obtain a green result.

## Task Description

**Problem:** Persistent baseline failures train contributors to ignore red suite results and hide
the distinction between known drift and new regressions. The remaining failures concern the
repository's maintainability expectations and committed workflow-artifact inventory, both of
which require an explicit current-state decision rather than automatic acceptance.

**Original scope:** The Jira report identified nine isolated failures arising from six causes.
Four causes and their corresponding failures were resolved by PYPOST-1077 before this task began.

**Current scope (in):**

- Resolve the four remaining SOLID-maintainability baseline outcomes.
- Resolve the remaining committed AI-task-artifact baseline outcome.
- Preserve the protective meaning of both baseline domains.
- Confirm that all four checks restored by PYPOST-1077 remain successful.
- Confirm that the full fast suite no longer reports any of the original nine failures.

The five remaining verification outcomes are:

- `test_audit_module_inventory_within_caps`
- `test_main_window_class_loc_within_cap`
- `test_main_window_file_loc_within_cap`
- `test_markdown_snapshot_matches_current_metrics`
- `test_baseline_matches_current_scan`

**Scope (out):**

- Reworking the four established contracts already restored by PYPOST-1077.
- Broad application redesign unrelated to the six original causes.
- Removing, skipping, or broadly relaxing checks without an explicit approved disposition.
- Addressing unrelated failures that were not part of the original nine-test report.

**Constraints and assumptions:**

- The original failures reproduce independently and are not order-dependent flakiness.
- PYPOST-1077 is the accepted resolution for the dialogue-audit, function-catalog, Jira
  read-only-capability, and encrypted-startup contract failures.
- The five remaining failures reproduced identically in two later full-suite runs documented by
  PYPOST-1076.
- Baseline stabilization must preserve meaningful regression detection.
- Any accepted maintainability growth must remain visible and reviewable rather than implicit.
- Verification must be repeatable and bounded.

## Main Entities and Interactions

- **Fast test suite** — the release-quality signal that evaluates application and repository
  contracts together.
- **SOLID-maintainability baseline** — the accepted limits and inventory used to detect
  unapproved structural growth.
- **AI-task-artifact baseline** — the accepted committed workflow-artifact inventory used to
  detect unexpected drift.
- **Restored application contracts** — the four protected outcomes completed by PYPOST-1077.
- **Baseline disposition** — the explicit decision that classifies observed drift as accepted
  current state or actionable debt.
- **Release steward** — the person or process relying on the suite result.

The release steward uses the fast suite as a quality signal. The suite compares current
maintainability and artifact state with their accepted baselines while also verifying the four
restored contracts. Explicit dispositions keep accepted state distinguishable from regressions.

## Non-Functional Requirements

- **Reliability:** Repeated runs over the same repository state must produce consistent outcomes.
- **Regression resistance:** Stabilization must preserve detection of future unapproved drift.
- **Transparency:** Accepted baseline changes and unresolved debt must be explicit and reviewable.
- **Scope discipline:** Work must remain limited to the original failure set and its current
  five-failure remainder.
- **Verification safety:** Checks must remain enabled and retain their intended assertions.

## Q&A

**Q:** Why is this work needed if the failures are already known?

**A:** A permanently red baseline cannot reliably warn contributors about new regressions. The
suite must distinguish accepted current state from new problems.

**Q:** Why are only five failures in the current implementation scope?

**A:** PYPOST-1077 already restored four of the nine reported checks. Later full-suite evidence
shows that only the four SOLID-maintainability checks and the task-artifact baseline check remain.
See the [PYPOST-1077 contract requirements](../PYPOST-1077/10-requirements.md) and the
[PYPOST-1076 repeated full-suite evidence](../PYPOST-1076/40-code-cleanup.md).

**Q:** Does resolving a baseline failure automatically mean accepting the observed growth?

**A:** No. Each failure requires an explicit, evidence-backed disposition. The work must not hide
real maintainability debt or weaken future regression detection.

**Q:** May the task remove or skip a failing check to make the suite green?

**A:** No. A green result is acceptable only when the protected contract remains meaningful.

# PYPOST-1111: Regenerate audit and baseline metrics snapshots drifted by recent refactors

## Goals

In PyPost, automated architecture audit reports and regression baseline metrics serve as quality gates to protect against architectural erosion, monolithic coupling, and unintended code expansion. As new features (such as multi-server MCP management, upstream proxy support, and structured template expression resolution) are introduced, legitimate code growth occurs.

When audit snapshots and regression thresholds are not updated alongside approved feature additions, automated verification suites fail on false-positive regressions. This degrades developer productivity, erodes trust in automated quality gates, and blocks continuous integration and release delivery pipelines.

The goal of this task is to re-synchronize repository audit documentation, baseline metrics snapshots, and regression threshold guards with the actual current state of the codebase. This restores confidence in automated test suites and ensures quality gates remain green while continuing to guard against future unmonitored code inflation.

**Implementation language:** Python

## User Stories

- As a **PyPost Developer**, I want the automated test suite and regression quality gates to pass cleanly without false positive failures on historical snapshots, so that I can verify my code changes with certainty.
- As an **Engineering Lead / Architectural Maintainer**, I want architecture audit records and baseline metric snapshots to accurately reflect current verified codebase sizes and structures, so that architectural tracking and code health monitoring remain trustworthy.
- As a **Release Engineer**, I want CI verification gates to enforce valid, up-to-date regression boundaries rather than obsolete snapshot states, so that releases and pull requests are not blocked unnecessarily.

## Definition of Done

- [ ] Dialog inventory audit records and associated verification tests accurately reflect all current dialog components, line counts, and functional responsibilities in the codebase.
- [ ] Baseline metrics snapshots in architecture audit documents match actual automated measurements across all monitored core and UI components.
- [ ] Module size thresholds (caps) accommodate legitimate, approved feature expansion (including template expression resolution and multi-server MCP dialog features) with standard headroom policy (~10%), preventing uncontrolled growth while permitting legitimate enhancements.
- [ ] Automated regression tests (`tests/test_pypost_1077_verification_artifacts.py` and `tests/test_solid_audit_baseline.py`) pass cleanly without assertion failures.
- [ ] Full quality gate verification (`make check` / `make test` / `make lint` / `make verify-ai-tasks`) passes cleanly.

## Task Description

During full test suite runs, two pre-existing test failures occur due to metric drift between recorded audit snapshots and current codebase reality:

1. `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`:
   - Fails because `mcp_servers_dialog.py` legitimately grew when multi-server management, upstream proxy configuration, and custom environment header resolution were introduced, causing the dialog audit report (`ai-tasks/PYPOST-374/30-dialogs-audit-report.md`) and test assertions to drift from current source line counts.
2. `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline`:
   - `test_audit_module_inventory_within_caps` fails because `pypost/core/template_service.py` (241 lines) exceeds the historical cap of 225 lines after accommodating template expression resolution and structured failure provenance.
   - `test_markdown_snapshot_matches_current_metrics` fails because the recorded baseline snapshot (`ai-tasks/PYPOST-376/baseline-metrics.md`) differs from current automated measurements.

### System Boundaries and Domain Entities

- **Dialog Inventory**: High-level catalog of dialog user interface modules, their responsibilities, and their verified sizes.
- **Baseline Metrics Snapshot**: Authoritative historical and current measurement record of module sizes, class sizes, and complexity indicators.
- **Regression Size Cap**: Policy threshold defining acceptable file and class size limits with ~10% headroom to prevent accidental code bloat while allowing deliberate enhancements.
- **Quality Gate / Regression Guard**: Automated contract ensuring codebase reality aligns with architectural commitments and safety bounds.

### In Scope

- Synchronizing dialog inventory documentation and contract test assertions with current dialog modules and measured lines of code.
- Updating module size thresholds (caps) to accommodate legitimate feature additions with standard headroom.
- Synchronizing baseline metrics snapshots with measured codebase reality.
- Ensuring all quality gate suites run cleanly green.

### Out of Scope

- Refactoring dialog implementations or altering user-facing UI behavior.
- Modifying template service functionality, Jinja rendering behavior, or template expression grammar.
- Adjusting unrelated module caps or unrelated audit documents.

## Functional Requirements

- **Dialog Inventory Synchronization**:
  - The dialog audit documentation and associated contract tests must accurately reflect all active dialog modules, their current line counts, and their primary responsibilities.
  - Discovered dialog counts and aggregate lines of code must be mutually consistent between the report and contract tests.
- **Baseline Metrics Snapshot Synchronization**:
  - Recorded baseline metrics snapshots must match current measured values for all monitored modules and classes.
  - The snapshot regeneration mechanism must produce output that exactly matches the recorded baseline document.
- **Regression Cap Realignment**:
  - File size caps for legitimately expanded modules must be updated to incorporate approved feature additions plus standard headroom (~10%), preventing accidental creep while accommodating necessary logic.
  - Rationale for any cap adjustment must be documented in baseline configuration comments.
- **Quality Gate Enforcement**:
  - Regression test suites and quality gates must pass without error.

## Non-functional Requirements

- **Accuracy & Truthfulness**: Audit numbers and snapshots must be exact representations of the current source tree.
- **Safety & Bloat Prevention**: Size caps must remain strict upper bounds with defined headroom rather than unconstrained limits.
- **Zero Behavioral Disruption**: No changes to runtime behavior, public APIs, or user interactions.

## Constraints and Assumptions

- Implementation language: Python.
- Repository operations must be executed exclusively through `make` targets.
- Jira Task ID: PYPOST-1111.

## Q&A

- **Q: Why should `pypost/core/template_service.py` cap be increased instead of refactoring it down?**
  - **A:** Recent feature work (PYPOST-1119, PYPOST-1120) legitimately added essential functionality for template expression resolution and structured failure provenance. Refactoring is appropriate if code becomes uncohesive, but the immediate requirement is restoring green quality gates while acknowledging legitimate growth. Any future restructuring can be evaluated and ticketed as technical debt if needed.
- **Q: Why did `pypost/ui/dialogs/mcp_servers_dialog.py` change?**
  - **A:** It grew from 446 to 487 LOC to incorporate upstream proxy configuration and custom environment header resolution (PYPOST-1092 and PYPOST-1104). The dialog audit report and test expectations must be brought in line with this approved feature scope.

## STEP 1 Approval Basis

The applicable `sprint-runner` / `sprint-task-runner` workflow operates autonomously under the top-down methodology and preauthorizes continuation without an interactive user prompt. Acceptance will be verified via the autonomous review gate.

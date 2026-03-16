# PYPOST-40: Technical Debt Analysis

## Code Review Summary

**Reviewed:** `10-requirements.md`, `20-architecture.md`, `30-audit-report.md`

### Audit Deliverables

- **Requirements:** Clear scope (SOLID + maintainability), business goal stated, no technical
  solutions in requirements phase.
- **Architecture:** Audit methodology defined (phases 1–5), module scope table, prioritization
  framework. Flow diagram and report structure documented.
- **Audit Report:** Module inventory with LOC, SOLID assessment per principle with file:line
  references, maintainability dimensions, prioritized recommendations (P1/P2/P3), appendix with
  finding IDs.

### Audit Process Quality

- Manual code walkthrough; no automated static analysis (e.g. radon, pylint, mypy) was run.
- Severity ratings (High/Medium/Low) are qualitative; no formal metric thresholds.
- mcp_client_service.py was present in LOC count but not deeply analyzed in SOLID tables.

## Shortcuts Taken

- **Skipped automated tools:** radon (cyclomatic complexity, maintainability index), pylint
  (convention checks), or dependency-graph tools could have supplemented the manual audit.
- **Dialogs not fully audited:** `ui/dialogs/` (~400 LOC) summarized as a group; individual
  dialogs (SaveDialog, EnvDialog, SettingsDialog, etc.) were not assessed per SOLID.
- **utils/ not inventoried:** No Python files in utils/ were found; scope may be empty or
  under a different path. Not verified.
- **No regression baseline:** Audit does not establish a baseline metric (e.g. "MainWindow
  must stay under 500 LOC") for future comparison.

## Code Quality Issues (in Audited Codebase)

As documented in `30-audit-report.md`:

- MainWindow: 1040 LOC, many responsibilities (SRP violation).
- MetricsManager, template_service: Singletons/globals (DIP violation).
- RequestService, RequestWorker, MCPServerImpl: Direct instantiation of dependencies (DIP).
- RequestManager: item_type branching (OCP); MainWindow: dual storage/request_manager usage.

## Missing Tests

- No tests were written or modified for this task (audit only).
- The audit identified testability gaps: RequestService, HTTPClient, MainWindow are hard to
  unit test due to lack of dependency injection.

## Performance Concerns

- None specific to the audit. The audited codebase has known concerns (e.g. full tree
  reload on delete) documented in prior tech-debt reports (e.g. PYPOST-35).

## Follow-up Tasks

1. **Prerequisite (High priority):**
   - PYPOST-52 — Add test coverage for refactoring safety (blocks PYPOST-43)
2. **P1 (High priority):**
   - PYPOST-43 — Decompose MainWindow into presenters
   - PYPOST-44 — Replace MetricsManager singleton with injection
   - PYPOST-45 — Replace template_service global with injection
2. **P2 (Medium priority):**
   - PYPOST-46 — Introduce HTTPClient protocol and inject into RequestService
   - PYPOST-47 — Unify collection loading via RequestManager
   - PYPOST-48 — Replace item_type branching with strategy in RequestManager
   - PYPOST-49 — Split MetricsManager into MetricsRegistry and MetricsServer
3. **P3 (Low priority):**
   - PYPOST-50 — Abstract StorageManager behind StorageInterface
   - PYPOST-51 — Add ExecuteRequestProtocol for request execution
4. **Consider automated audit tooling:** Script or CI job that runs radon/pylint.
5. **Periodic re-audit:** Re-run audit after P1/P2 implementations to verify improvement.

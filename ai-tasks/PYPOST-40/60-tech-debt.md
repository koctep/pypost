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

- **No radon/pylint/deps graph** ([PYPOST-373](https://pypost.atlassian.net/browse/PYPOST-373)):
  Skipped automated tools (cyclomatic complexity, maintainability index, convention checks) that
  could have complemented the manual audit.
- **Dialogs audited as a group** ([PYPOST-374](https://pypost.atlassian.net/browse/PYPOST-374)):
  `ui/dialogs/` (~400 LOC) summarized together; individual dialogs were not scored per SOLID.
- **utils/ scope unclear** ([PYPOST-375](https://pypost.atlassian.net/browse/PYPOST-375)):
  No Python files found under `utils/`; may be empty or elsewhere — not verified.
- **No regression baseline metrics** ([PYPOST-376](https://pypost.atlassian.net/browse/PYPOST-376)):
  Audit does not set baseline metrics (e.g. MainWindow LOC cap) for future comparison.

## Code Quality Issues (in Audited Codebase)

As documented in `30-audit-report.md`:

- MainWindow: 1040 LOC, many responsibilities (SRP violation).
  — [PYPOST-377](https://pypost.atlassian.net/browse/PYPOST-377)
- MetricsManager, template_service: Singletons/globals (DIP violation).
  — [PYPOST-378](https://pypost.atlassian.net/browse/PYPOST-378)
- RequestService, RequestWorker, MCPServerImpl: direct dependency instantiation (DIP).
  — [PYPOST-379](https://pypost.atlassian.net/browse/PYPOST-379)
- RequestManager: item_type branching (OCP); MainWindow: dual storage/request_manager usage.
  — [PYPOST-380](https://pypost.atlassian.net/browse/PYPOST-380)

## Missing Tests

- No tests were written or modified for this task (audit only).
  — [PYPOST-381](https://pypost.atlassian.net/browse/PYPOST-381)
- **Testability gaps** ([PYPOST-382](https://pypost.atlassian.net/browse/PYPOST-382)):
  RequestService, HTTPClient, and MainWindow are hard to unit-test without dependency injection.

## Performance Concerns

- **Prior reports cover perf** ([PYPOST-383](https://pypost.atlassian.net/browse/PYPOST-383)):
  No new audit-specific concerns; known issues (e.g. full tree reload on delete) appear in earlier
  tech-debt notes (e.g. PYPOST-35).

## Follow-up Tasks

1. **Prerequisite (High priority):**
   - PYPOST-52 — Add test coverage for refactoring safety (blocks PYPOST-43).
     — [PYPOST-384](https://pypost.atlassian.net/browse/PYPOST-384)
2. **P1 (High priority):**
   - PYPOST-43 — Decompose MainWindow into presenters
   - PYPOST-44 — Replace MetricsManager singleton with injection
   - PYPOST-45 — Replace template_service global with injection
3. **P2 (Medium priority):**
   - PYPOST-46 — Introduce HTTPClient protocol and inject into RequestService
   - PYPOST-47 — Unify collection loading via RequestManager
   - PYPOST-48 — Replace item_type branching with strategy in RequestManager
   - PYPOST-49 — Split MetricsManager into MetricsRegistry and MetricsServer
4. **P3 (Low priority):**
   - PYPOST-50 — Abstract StorageManager behind StorageInterface
   - PYPOST-51 — Add ExecuteRequestProtocol for request execution
5. **Consider automated audit tooling:** Script or CI job that runs radon/pylint.
6. **Periodic re-audit:** Re-run audit after P1/P2 implementations to verify improvement.

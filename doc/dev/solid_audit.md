# SOLID and Maintainability Audit

This document describes the PyPost codebase audit for SOLID compliance and design for
maintainability (PYPOST-40). The audit provides a foundation for refactoring decisions and
technical debt prioritization.

## Audit Report

Full report: [ai-tasks/PYPOST-40/30-audit-report.md](../../ai-tasks/PYPOST-40/30-audit-report.md)

## Key Findings

- **MainWindow** (1040 LOC): Acts as a "god object" with many responsibilities. Decompose into
  presenters (CollectionsPresenter, TabsPresenter, EnvironmentPresenter).
- **Singletons/globals**: MetricsManager and template_service hinder testability and DIP.
  Replace with constructor injection.
- **Direct instantiation**: RequestService, RequestWorker, MCPServerImpl create dependencies
  directly. Introduce protocols and injection.

## Prioritized Recommendations

| Priority | Recommendation |
|----------|----------------|
| P1 | Decompose MainWindow; replace MetricsManager/template_service with injection |
| P2 | HTTPClient protocol; unified collection loading; item_type strategy; split MetricsManager |
| P3 | StorageInterface; ExecuteRequestProtocol |

## Related

- [Architecture Overview](architecture.md)
- [Technical Debt: PYPOST-40](tech-debt/PYPOST-40.md)

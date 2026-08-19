# PYPOST-1023: Architecture Design

## Docs Accuracy-Drift Governance

1. **Ownership**:
   - The author of any UI / configuration / shortcut change is responsible for updating corresponding `doc/user/` documentation within the same PR / commit.
   - Code reviewers enforce the checklist before approval.

2. **Trigger Events**:
   - UI label changes (menus, dialogs, buttons, fields).
   - Configuration default changes (ports, timeouts, retry backoffs).
   - Shortcut / key sequence changes (`QKeySequence`).
   - Workflow modifications.

3. **Verification Process**:
   - Topic page lookup via component mapping table.
   - Verbatim string comparison against Qt UI code.
   - Automated style and link linting via `make lint-docs` and `make check-docs-links`.

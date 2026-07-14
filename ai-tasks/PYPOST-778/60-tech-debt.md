# PYPOST-778: Technical Debt

## Non-blockers

- **Unpinned pydantic lower bound:** `pydantic>=2.11,<3` may resolve different patch versions
  between runs; pip-audit still scans the resolved tree at scan time.
  — Jira: [PYPOST-777](https://pypost.atlassian.net/browse/PYPOST-777)
- **No lock file:** Identical requirements can drift transitively over time.
  — Jira: [PYPOST-779](https://pypost.atlassian.net/browse/PYPOST-779)
- **Dev tools not scanned:** pytest/flake8 versions in CI are outside production `requirements.txt`.

## Exception process

When a CVE has no upstream fix, add a temporary `pip-audit --ignore-vuln <ID>` in the CI step
and document rationale in `doc/dev/dependencies_audit.md`. Remove when fixed version is available.

## Blockers

None — safe to close.

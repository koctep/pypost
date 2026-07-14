# PYPOST-749 — Requirements

> Parent: [PYPOST-688](https://pypost.atlassian.net/browse/PYPOST-688) audit R-P3-001

## Problem

Local `log_cli=true` vs CI `log_cli=false` is documented in `doc/dev/testing.md`, but the
observability audit summary does not cross-link to that section — and testing.md does not link
back to the observability audit's Test and CI Logging table. Maintainers must search both files
to connect pytest live logging policy with the audit baseline (72 ERROR + margin 5).

## Acceptance Criteria

1. `doc/dev/observability_audit.md` links to the pytest `log_cli` section in `testing.md`.
2. `doc/dev/testing.md` links to the Test and CI Logging section in `observability_audit.md`.
3. No application code changes.
4. `make check` passes.

## Out of Scope

- Changing pytest.ini or CI workflow log_cli settings
- Updating allowlist baseline counts
- Other observability doc cross-links (logging.md, metrics inventory — separate tickets)

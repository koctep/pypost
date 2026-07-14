# PYPOST-747 — Requirements

> Parent: [PYPOST-688](https://pypost.atlassian.net/browse/PYPOST-688) audit R-P2-005

## Problem

PyPost mixes **key=value structured events** (newer modules) with **legacy human-readable log
strings** (`Connection failed: GET url`, `ClassName: message`). Maintainers lack a single
reference for naming new events and migrating old ones.

## Acceptance Criteria

1. Add `doc/dev/logging.md` (or extend observability doc) documenting:
   - key=value event naming convention and formatting rules
   - domain-grouped event catalog (~330 calls across core domains)
   - legacy migration guide with before/after examples
2. Cross-link from [observability_audit.md](../../doc/dev/observability_audit.md) and dev README.
3. No application code changes unless trivial cross-links.
4. `make check` passes.

## Out of Scope

- Bulk migration of legacy log strings (tracked separately as PYPOST-751)
- JSON/structlog adoption
- New log level settings (already addressed in PYPOST-743)

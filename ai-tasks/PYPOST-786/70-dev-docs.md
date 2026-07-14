# PYPOST-786: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/licensing.md` | **New** — PySide6 LGPL-3.0 distribution obligations guide |
| `doc/dev/dependencies_audit.md` | Cross-link to `licensing.md`; R-P3-002 marked Done (PYPOST-786) |
| `doc/dev/README.md` | Table of contents entry under Audits |

## Key maintainer workflow

1. Before shipping any binary/installer that bundles Qt libraries, read
   [licensing.md](../licensing.md) § Distributor checklist.
2. Keep `requirements.in` PySide6 pin documented in release notes when binaries are built.
3. For source-only releases, no additional LGPL packaging steps beyond existing MIT `LICENSE`.

## Cross-links

- Parent audit: [dependencies_audit.md](../dependencies_audit.md), finding L-002
- Audit report: [ai-tasks/PYPOST-691/30-audit-report.md](../../ai-tasks/PYPOST-691/30-audit-report.md)

# PYPOST-686: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/test_audit.md` | **Created** — test suite health audit summary |
| `doc/dev/README.md` | Added table-of-contents entry for test audit |

## Key Points for Maintainers

- Full audit report: [30-audit-report.md](30-audit-report.md)
- Developer summary: [doc/dev/test_audit.md](../../doc/dev/test_audit.md)
- Suite scale: 135 modules, 1,423 fast tests, ~88% line coverage, 70% CI gate
- **100% timeout marker compliance** via `conftest.py` enforcement
- Primary risks: macOS segfault in `test_mcp_server_manager.py`, SOLID cap drift, Makefile Python
  version coupling, low coverage on server managers and some dialogs
- P1/P2/P3 follow-ups in [60-tech-debt.md](60-tech-debt.md) (orchestrator tickets separately)

## Related Docs

- [testing.md](../../doc/dev/testing.md) — pytest commands, CI parity, coverage threshold
- [do-testing.md](../../.cursor/lsr/do-testing.md) — agent timeout and caplog rules
- [gui_testing.md](../../doc/dev/gui_testing.md) — Qt offscreen patterns
- [testability.md](../../doc/dev/testability.md) — injection seams (PYPOST-382)
- [solid_audit.md](../../doc/dev/solid_audit.md) — LOC baseline caps

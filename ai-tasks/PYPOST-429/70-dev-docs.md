# PYPOST-429: Dev Docs

## Updated

| File | Change |
| --- | --- |
| `doc/dev/gui_testing.md` | Added ELF core dump troubleshooting rows and investigation link |
| `doc/dev/testing.md` | Cross-link to GUI core-dump guidance |
| `ai-tasks/PYPOST-429/investigation-report.md` | Full investigation artifact (canonical reference) |

## Rationale

Closes Sprint 134 TD-4: maintainers have a single place to understand the historical `core`
dump, reproduction outcome, and what to do if a native Qt crash happens again during local test
runs.

## Key finding (for readers)

The dump was a **local unreproducible native crash** during manual `test_tabs_presenter.py`
testing — not a current application defect. See `investigation-report.md` for evidence and
ranked hypotheses.

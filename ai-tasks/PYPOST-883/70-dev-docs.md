# PYPOST-883: Developer Documentation

## Updates

| Doc | Change |
| --- | --- |
| `doc/dev/gui_testing.md` | Probe C canary (PYPOST-883); troubleshooting; References |
| `doc/dev/environment_storage_async.md` | Findings note + canary path under Tests / H3 section |

## Review

Self-review against `70-dev-docs.mdc`:

- **Overview / architecture:** existing GUI + async-storage docs already
  cover `process_until` and H3; this story adds the unreproduced-hang
  canary pointer only.
- **Usage:** focused `make test` / pytest path for Probe C documented.
- **Troubleshooting:** hang triage row distinguishes H3 segfault canary
  vs PYPOST-883 save-completed + QComboBox GC canary.
- **No new standalone doc file** — change fits existing pages; README
  ToC unchanged.

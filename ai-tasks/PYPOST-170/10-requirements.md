# PYPOST-170: GUI action metric verification

## Goals

Close PYPOST-23 debt: maintainers need proof that user-facing GUI actions (Send click, Save,
Save As, Copy cURL) increment the correct Prometheus counters, not only that tracking methods
work in isolation.

## User Stories

- As a **maintainer**, I want tests that drive `RequestWidget` entry points and inspect the
  Prometheus registry, so metric wiring regressions in the editor are caught in CI.
- As a **reviewer**, I want assertions on counter names and values after real widget actions,
  matching the pattern used for method-body autoswitch metrics.

## Definition of Done

- [x] Send button click increments `gui_send_clicks_total` (registry scrape).
- [x] Save, Save As, and Copy cURL entry points increment labeled counters.
- [x] Tests use explicit pytest timeouts and offscreen Qt setup.
- [x] Developer testing docs list the new coverage.
- [x] PYPOST-23 metric-verification debt item addressed.

## Task Description

Follow-up from `ai-tasks/PYPOST-23/40-tech-debt.md`. Unit tests already call
`MetricsManager.track_*` directly; this task wires actions through `RequestWidget` and scrapes
the registry.

**In scope:** tests and documentation only.

**Out of scope:** production code changes, collection-tree metrics (already covered elsewhere).

## Q&A

| Question | Answer |
| --- | --- |
| Where do tests live? | New `tests/test_request_editor_gui_metrics.py`. |
| Mock or real metrics? | Real `MetricsManager` + `generate_latest` scrape. |

# PYPOST-264: Close debt — New-tab metrics source validation

## Goals

Close follow-up debt from [PYPOST-29](https://pypost.atlassian.net/browse/PYPOST-29): add a narrow
source validation layer for new-tab metrics so only known trigger labels appear in Prometheus.

## User Stories

- As an **operator**, I want **new-tab metrics grouped by stable source labels**, so I can compare
  plus-button vs keyboard usage without typos polluting cardinality.
- As a **developer**, I want **invalid caller strings mapped to `unknown`**, so future call sites
  cannot accidentally emit arbitrary label values.

## Definition of Done

- [x] Validates `plus_button`, `shortcut`, and maps unknown values to `unknown`
- [x] Regression tests in `tests/test_metrics_manager.py`
- [x] Normalization applied at the metrics API boundary (`track_gui_new_tab_action`)

## Task Description

Sprint 498 debt closure. Resolution delivered via prior tab-header refactor; this task verifies
and documents the existing `_normalize_new_tab_source` helper and locks behavior with tests.

## Q&A

| Question | Answer |
| --- | --- |
| Why not validate at every call site? | Single normalization at `MetricsRegistry.track_gui_new_tab_action` keeps call sites simple and guarantees consistent labels regardless of entry point. |
| Is `collections_context` in scope? | Yes — it is a known fourth label for collection-tree context-menu new-tab actions; included in the allowed set and covered by tests. |

# PYPOST-170: Technical Debt

## Resolved

- **Metric Verification** (PYPOST-23) — `RequestWidget` Send/Save/Save As/Copy cURL actions
  verified via Prometheus registry scrape in `tests/test_request_editor_gui_metrics.py`.

## Remaining (non-blocker)

- **Response search GUI metrics** — `track_gui_response_search_action` covered at unit level
  only; tab-level integration similar to PYPOST-357 search flow could be added later.
- **Variable validation GUI metrics** — unit tests exist; no widget-level scrape tests yet.

## Verdict

**SAFE TO CLOSE** — acceptance criteria met; tests pass with offscreen Qt.

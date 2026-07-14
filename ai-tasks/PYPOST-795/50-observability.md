# PYPOST-795: Observability

## Summary

No logging or metrics changes. This task documents existing close-indicator behaviour.

## Existing signals (unchanged)

- Tab layout regressions surface via `tests/test_tab_layout_regression.py`.
- Appearance pipeline logs remain on `StyleManager` (PYPOST-793) — no close-button-specific
  events.

## Validation

- Symptom "close button overlaps title" documented in
  `doc/dev/ui_font_and_styles.md` troubleshooting — points to global override misuse, not
  missing logs.

No new observability work required for this debt item.

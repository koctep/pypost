# PYPOST-795: Architecture — set_close_button_size evaluation

## Research

### Current implementation

```python
# pypost/ui/styles/custom_style.py
class PyPostStyle(QProxyStyle):
    def __init__(self, base_style=None):
        super().__init__(base_style)
        self.close_button_size: int | None = None

    def pixelMetric(self, metric, option=None, widget=None):
        if metric in self._CLOSE_INDICATOR_METRICS and self.close_button_size is not None:
            return self.close_button_size
        return super().pixelMetric(metric, option, widget)

    def set_close_button_size(self, size: int) -> None: ...
```

### Call graph (production)

```text
StyleManager.apply_theme("system")
  → app.setStyle(PyPostStyle())   # close_button_size stays None
  → pixelMetric(PM_TabCloseIndicator*) → baseStyle().pixelMetric(...)
```

No production path calls `set_close_button_size`. PYPOST-792 removed
`set_close_button_size(48)` from `main.py` and theme bootstrap.

### Test usage

| Test | Purpose |
| --- | --- |
| `test_close_indicator_defaults_to_base_style_metric` | Default `None` → native metrics |
| `test_close_indicator_override_is_opt_in` | `set_close_button_size(48)` → forced size |
| `test_apply_theme_system_uses_native_close_metrics` | Production `system` theme path |

### Documentation state (pre-task)

`doc/dev/ui_font_and_styles.md` already described close-indicator policy (PYPOST-792) and listed
the API briefly, but lacked an explicit **keep vs remove** decision and when-to-use guidance.

## Decision

**Keep API — document explicit override use case.**

| Option | Pros | Cons |
| --- | --- | --- |
| **Document (chosen)** | Preserves escape hatch; tests unchanged; aligns with PYPOST-792 intent | Small API surface with no current production caller |
| Remove | Fewer lines | Loses opt-in path; tests need rewrite; no user benefit |

### Rationale

1. PYPOST-792 deliberately kept the method as opt-in — removal contradicts that architecture.
2. Legitimate future uses: platform metric bugs, accessibility hit targets, isolated experiments.
3. Removing does not simplify production — `pixelMetric` branch on `None` stays either way.
4. Tests document and guard the opt-in contract.

## Changes

| Artifact | Change |
| --- | --- |
| `custom_style.py` | Expand `set_close_button_size` docstring (when / when not) |
| `doc/dev/ui_font_and_styles.md` | PYPOST-795 decision, when-to-use, example, Related link |

No changes to `StyleManager`, QSS, or production call sites.

## Invariants (unchanged)

- Default `close_button_size` is `None`.
- Production `system` theme never sets override.
- No global 48px close-indicator default.
- QSS must not style `QTabBar::tab` box model (PYPOST-792).

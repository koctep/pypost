# PYPOST-793: Observability Implementation

## Logging Implementation

### Added Logs

Describe added logging:

- **EMERG**: none.
- **ALERT**: none.
- **CRIT**: none.
- **ERR**: none.
- **WARNING**: none added (pre-existing `StyleManager.load_styles` warnings unchanged).
- **NOTICE**: none.
- **INFO**: none added in this task.
- **DEBUG**:
  - `StyleManager.apply_appearance` — `apply_appearance_start font_size=%d` before the
    theme → QSS → font pipeline runs.
  - `StyleManager.apply_appearance` — `apply_appearance_font_applied point_size=%d` after
    `app.setFont`, recording the applied default font size.
  - Pre-existing `StyleManager` DEBUG logs remain: `theme_applied`, `styles_loaded`.

### Log Structure

Log format used:

- Structured logs: yes — key=value fields (`font_size`, `point_size`, `theme`, `path`, etc.).
- Includes context: yes — requested vs applied font size; theme name for low-level theme logs.
- Log levels: DEBUG (appearance pipeline), WARNING (stylesheet load failures), INFO (unchanged
  in `MainWindow.open_settings` — `settings_applied`).

### Relocated Logs (PYPOST-404 → PYPOST-793)

Appearance DEBUG logs moved from `MainWindow.apply_settings` to
`StyleManager.apply_appearance` as part of consolidating pipeline ownership:

| Previous (`main_window.py`) | Current (`style_manager.py`) |
| --- | --- |
| `apply_settings_start font_size=%d` | `apply_appearance_start font_size=%d` |
| `apply_settings_font_applied point_size=%d` | `apply_appearance_font_applied point_size=%d` |

**Why two lines instead of one**: Same diagnostic contract as PYPOST-404 — the first records
the requested font size before Qt re-polish from `setStyleSheet`; the second records
`app.font().pointSize()` after `setFont`. A mismatch signals call-order or stylesheet regression.

**Why theme is not logged in `apply_appearance`**: Low-level `apply_theme` already emits
`theme_applied theme=%s style=... requested=%s` at DEBUG. Logging theme again at the facade
would duplicate messages on every settings save.

## Metrics Implementation (if applicable)

Not applicable. Appearance application is a synchronous UI operation on the main thread; no
new counters or histograms were added. Existing `MetricsManager` targets HTTP/network
observability.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — not applicable for this UI path.
- [ ] Grafana dashboards — not applicable.
- [ ] Alerting rules — not applicable.
- [ ] Log aggregation (ELK, Loki, etc.) — existing application logging; no new integration.

## Validation Results

Validation results:

- [x] Logs are correctly formatted — key=value DEBUG lines in `style_manager.py`.
- [x] Metrics are collected correctly — N/A.
- [x] Logging works in error scenarios — stylesheet read failures still log WARNING in
  `load_styles` (pre-existing).
- [x] Large data structures are not logged — only scalar fields (font size, point size, counts).
- [x] Metrics are available for monitoring — N/A.

## Notes

Enable DEBUG on the style manager module to trace appearance on startup and settings save:

```python
logging.getLogger("pypost.ui.styles.style_manager").setLevel(logging.DEBUG)
```

Expected output during `apply_appearance(app, theme="dark", font_size=12)`:

```
… pypost.ui.styles.style_manager DEBUG apply_appearance_start font_size=12
… pypost.ui.styles.style_manager DEBUG theme_applied theme=dark style=Fusion requested=dark
… pypost.ui.styles.style_manager DEBUG styles_loaded file_count=N bytes=M
… pypost.ui.styles.style_manager DEBUG apply_appearance_font_applied point_size=12
```

Regression signature (Qt re-polish bug returns):

```
… DEBUG apply_appearance_start font_size=12
… DEBUG apply_appearance_font_applied point_size=9   ← mismatch
```

`MainWindow.open_settings` still logs `settings_applied font_size=…` at INFO after user saves
Settings — unchanged; complements appearance DEBUG without duplicating the pipeline trace.

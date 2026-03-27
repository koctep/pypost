# PYPOST-424: Developer documentation — request timeout in settings

## Overview

This task exposes the existing **request timeout** (`AppSettings.request_timeout`) on the main
**Settings** dialog so operators can see and edit it like other connection-related options. The
data model, JSON persistence, and save path were already present; the fix is primarily **UI
layout** (one labeled row) plus **observability** on successful apply.

## Developer-facing changes

### Settings dialog (`pypost/ui/dialogs/settings_dialog.py`)

- The existing `timeout_spin` (`QSpinBox`, range **1–300** seconds) is added to the main
  `QFormLayout` with label **Request Timeout (seconds):**, placed **after** font/indent rows and
  **before** MCP/Metrics rows.
- **Single control**: There is only one spinbox for `request_timeout`; no duplicate widgets or
  alternate code paths.
- **Load**: On construction, `timeout_spin.setValue(current_settings.request_timeout)` runs as
  before; the row makes the loaded value visible.
- **Save**: `accept()` still builds `AppSettings` with
  `request_timeout=self.timeout_spin.value()` unchanged.

### Model and persistence (unchanged behavior, documented for clarity)

- **Canonical field**: `request_timeout` on `AppSettings` in `pypost/models/settings.py`
  (default **60** seconds unless overridden by stored config).
- **Persistence**: `pypost/core/config_manager.py` loads/saves the full `AppSettings` document;
  `request_timeout` is part of the same JSON as other settings.

### Observability (`pypost/ui/main_window.py`)

- After the user saves settings successfully, the existing **INFO** log
  `settings_applied` includes **`request_timeout=%d`** (seconds) together with font and indent
  fields, matching the applied `AppSettings` value.

## Save, load, and verification

### Behavior

1. **Open Settings**: The dialog shows the current stored timeout in the spinbox (same value as
   on-disk config when load succeeds).
2. **Save**: Accepting the dialog returns an `AppSettings` instance including `request_timeout`;
   `MainWindow` persists via `ConfigManager` and applies settings.
3. **Round-trip**: Changing the value and saving updates JSON; reopening the dialog reads the new
   value.

### Automated checks

Run from the repository root (see `scripts/test.sh` for the full-suite entrypoint):

```bash
scripts/test.sh
```

Targeted tests (optional, faster feedback):

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q \
  tests/test_settings_dialog.py \
  tests/test_settings_persistence.py
```

Relevant cases:

- **`tests/test_settings_dialog.py`**: `timeout_spin` is on `form_layout`, loads from
  `AppSettings`, and `accept()` / `get_settings()` propagate `request_timeout`.
- **`tests/test_settings_persistence.py`**: `test_save_then_load_roundtrip` (or equivalent)
  asserts `request_timeout` survives JSON save/load via `ConfigManager`.

### Quality scripts (same as prior steps)

```bash
scripts/lint.sh pypost/ui/dialogs/settings_dialog.py pypost/ui/main_window.py
scripts/check-line-length.sh pypost/ui/dialogs/settings_dialog.py pypost/ui/main_window.py
```

### Manual smoke (platform UX)

- Open **Settings**, confirm **Request Timeout (seconds)** is visible and matches expectations.
- Change the value, save, reopen **Settings**, and confirm the value persisted.
- Optionally restart the app and confirm the value still matches stored configuration.

## Observability and troubleshooting

### What to look for in logs

- Search for the **`settings_applied`** log line after a successful save/apply. It should include
  **`request_timeout=N`** where `N` is the effective timeout in seconds (same as the spinbox
  after reload).

### Common interpretations

- **Timeout not visible in UI**: Confirm `form_layout.addRow` for `timeout_spin` exists in
  `settings_dialog.py`.
- **Log missing `request_timeout`**: The running build may predate STEP 5; verify
  `main_window.py` extends `settings_applied` with `request_timeout`.
- **Value mismatch**: Compare on-disk JSON, `AppSettings.request_timeout`, and the log line after
  save; they should match.

### Distinguishing configuration vs. HTTP timeouts

- **`settings_applied`** / `request_timeout` refers to **stored application configuration**.
- Runtime **HTTP/request** timeouts are logged elsewhere in the request stack; do not conflate
  grep hits for operational network issues with this settings field.

### Metrics

- No new Prometheus-style metrics were added for this desktop settings change; reliance is on
  structured **INFO** logging for post-apply visibility.

## Related artifacts

| Artifact | Purpose |
| -------- | ------- |
| `ai-tasks/PYPOST-424/10-requirements.md` | Functional and non-functional requirements |
| `ai-tasks/PYPOST-424/20-architecture.md` | Layout, flow, and test strategy |
| `ai-tasks/PYPOST-424/50-observability.md` | Logging details and troubleshooting |
| `ai-tasks/PYPOST-424/60-review.md` | Technical debt and test adequacy |

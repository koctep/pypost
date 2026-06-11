# PYPOST-444 — Developer Documentation

> Date: 2026-06-11
> Parent: [PYPOST-444](https://pypost.atlassian.net/browse/PYPOST-444)

---

## 1. What Changed and Why

[PYPOST-423](https://pypost.atlassian.net/browse/PYPOST-423) added save-time validation for
retryable HTTP status codes in Settings. Parser unit tests and a QMessageBox helper unit test
existed, but no offscreen Qt test drove `SettingsDialog.accept()` for the blocked-save path.

PYPOST-444 adds that dialog-level test.

---

## 2. Test Class

`tests/test_settings_dialog.py` — `TestSettingsDialogRetryableCodesValidation`:

- Sets invalid retryable codes (`500,abc`) on the line edit.
- Calls `accept()`.
- Asserts `new_settings is None` (save blocked).
- Patches `show_invalid_retryable_status_codes` and asserts it was called with the parser
  message.
- Uses `caplog` to assert `retryable_codes_settings_validation_failed reason=invalid_token`.

---

## 3. Running Tests

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_settings_dialog.py::TestSettingsDialogRetryableCodesValidation -v
```

Full settings dialog module:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_settings_dialog.py -q
```

---

## 4. Related

- [PYPOST-423](https://pypost.atlassian.net/browse/PYPOST-423) — validation implementation
- `doc/dev/settings_dialog.md` — Settings dialog overview
- `doc/dev/gui_testing.md` — offscreen Qt patterns

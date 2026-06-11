# PYPOST-445 — Developer Documentation

> Date: 2026-06-11
> Parent: [PYPOST-445](https://pypost.atlassian.net/browse/PYPOST-445)

---

## 1. What Changed and Why

[PYPOST-424](https://pypost.atlassian.net/browse/PYPOST-424) exposed `request_timeout` in
Settings and added ConfigManager round-trip coverage via direct field mutation. Dialog tests
verified spinbox load/accept but not persistence across a simulated restart after the UI
save path.

PYPOST-445 adds that restart-level integration test.

---

## 2. Test

`tests/test_settings_persistence.py` — `test_request_timeout_survives_settings_dialog_save_and_restart`:

- Isolates config dir with `tempfile` + `user_config_dir` patch.
- Opens `SettingsDialog`, sets timeout to `135`, accepts.
- Saves via `ConfigManager.save_config()` (same API as `MainWindow.open_settings()`).
- Asserts `settings.json` contains `request_timeout: 135`.
- Creates fresh `ConfigManager()` (restart simulation) and reloads settings.
- Reopens `SettingsDialog` and asserts spinbox shows `135`.

---

## 3. Running Tests

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_settings_persistence.py::test_request_timeout_survives_settings_dialog_save_and_restart -v
```

Full settings persistence module:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_settings_persistence.py -q
```

---

## 4. Related

- [PYPOST-424](https://pypost.atlassian.net/browse/PYPOST-424) — request timeout UI exposure
- `doc/dev/settings_dialog.md` — Settings dialog overview
- `tests/test_settings_dialog.py` — dialog-level spinbox tests

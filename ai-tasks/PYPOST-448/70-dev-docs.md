# PYPOST-448 — Developer Documentation

> Date: 2026-06-05
> Parent: [PYPOST-448](https://pypost.atlassian.net/browse/PYPOST-448)

---

## 1. What Changed and Why

PYPOST-437 added INFO logging when the hidden flag is toggled:

```text
env_hidden_flag_changed env_name=Dev key=API_KEY hidden=True
```

Some organization policies prohibit logging identifying variable names. PYPOST-448 makes key-
name visibility configurable with a security-first default: key names are redacted unless the
user opts in via Settings.

---

## 2. New Module: `HiddenToggleLogPolicy`

`pypost/core/hidden_toggle_log_policy.py`

```python
from pypost.core.hidden_toggle_log_policy import HiddenToggleLogPolicy

HiddenToggleLogPolicy.format_key_name("API_KEY", log_hidden_key_names=False)  # "********"
HiddenToggleLogPolicy.format_key_name("API_KEY", log_hidden_key_names=True)   # "API_KEY"
```

Used only by `EnvironmentDialog._on_hidden_toggled` before `logger.info(...)`.

---

## 3. Settings Wiring

| Component | Role |
|-----------|------|
| `AppSettings.log_hidden_key_names` | Persisted preference (default `False`) |
| `SettingsDialog` | Checkbox: "Log variable key names when hidden flag is toggled" |
| `MainWindow.apply_settings` | Forwards to `EnvPresenter.apply_settings` |
| `EnvPresenter._open_env_manager` | Passes flag into `EnvironmentDialog` constructor |

---

## 4. Documentation Updated

- `doc/dev/hidden_variables.md` — configuration, breaking default, troubleshooting, tests

---

## 5. Follow-up Jira (not closed by this step)

- [PYPOST-490](https://pypost.atlassian.net/browse/PYPOST-490) — integration test
- [PYPOST-491](https://pypost.atlassian.net/browse/PYPOST-491) — extract `HIDDEN_MASK` to core
- [PYPOST-492](https://pypost.atlassian.net/browse/PYPOST-492) — Settings UI section grouping
- [PYPOST-489](https://pypost.atlassian.net/browse/PYPOST-489) — e2e persistence test extension

[PYPOST-488](https://pypost.atlassian.net/browse/PYPOST-488) (doc update) addressed by this
STEP 7 update to `hidden_variables.md`.

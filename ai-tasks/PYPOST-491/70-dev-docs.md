# PYPOST-491 — Developer Documentation

> Date: 2026-06-11
> Parent: [PYPOST-491](https://pypost.atlassian.net/browse/PYPOST-491)

---

## 1. What Changed and Why

`HIDDEN_MASK` (`********`) moved from `pypost/ui/widgets/mixins.py` to
`pypost/core/constants.py` so core logging policy no longer imports from the UI layer.

Consumers:

- `pypost.core.hidden_toggle_log_policy` — toggle log key redaction
- `pypost.ui.widgets.mixins` — hover preview masking
- `pypost.ui.dialogs.env_dialog` — environment manager value cell display

Behavior and mask value are unchanged.

---

## 2. Documentation Updated

| File | Change |
| --- | --- |
| `doc/dev/hidden_variables.md` | Architecture section documents `pypost.core.constants.HIDDEN_MASK` |
| `doc/dev/README.md` | No change — hidden variables entry already present |

---

## 3. Import Reference

```python
from pypost.core.constants import HIDDEN_MASK
```

Do not import `HIDDEN_MASK` from `pypost.ui.widgets.mixins` in new code.

---

## 4. Related Tests

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_hidden_toggle_log_policy.py \
  tests/test_env_dialog.py \
  tests/test_variable_hover.py \
  tests/test_env_persistence_e2e.py \
  tests/test_settings_hidden_toggle_logging_e2e.py -v
```

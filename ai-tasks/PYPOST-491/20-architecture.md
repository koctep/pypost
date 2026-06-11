# PYPOST-491: Extract HIDDEN_MASK to shared constants module

## Research

- `HIDDEN_MASK = "********"` was introduced in PYPOST-437 for environment variable UI masking
  and hover previews (`pypost/ui/widgets/mixins.py`).
- PYPOST-448 added `HiddenToggleLogPolicy` in core, importing `HIDDEN_MASK` from mixins to
  keep log redaction aligned with UI — creating core → UI dependency.
- `SensitiveDataMaskingPolicy` uses a separate `HIDDEN_PLACEHOLDER = "***"` for request
  history; intentionally different surface — do not merge in this task.

### Current consumers

| Module | Usage |
| --- | --- |
| `pypost/ui/widgets/mixins.py` | Defines constant; hover hidden-key masking |
| `pypost/ui/dialogs/env_dialog.py` | Value cell display and edit guards |
| `pypost/core/hidden_toggle_log_policy.py` | Toggle log key redaction |
| Tests | Assert mask in dialog, hover, policy, persistence e2e |

## Design

### New module

`pypost/core/constants.py`:

```python
HIDDEN_MASK = "********"
```

Minimal module for cross-layer constants. Keeps core as the neutral owner (policy already
lives in core; UI already imports from core for other types).

### Import graph (after)

```
pypost/core/constants.py  (HIDDEN_MASK)
    ↑
    ├── pypost/core/hidden_toggle_log_policy.py
    ├── pypost/ui/widgets/mixins.py
    └── pypost/ui/dialogs/env_dialog.py
```

No core → UI edge for the mask constant.

### Changes

| File | Change |
| --- | --- |
| `pypost/core/constants.py` | **New** — define `HIDDEN_MASK` |
| `pypost/ui/widgets/mixins.py` | Remove definition; import from `pypost.core.constants` |
| `pypost/core/hidden_toggle_log_policy.py` | Import from `pypost.core.constants` |
| `pypost/ui/dialogs/env_dialog.py` | Import from `pypost.core.constants` |
| Test files | Import from `pypost.core.constants` where asserting mask |

### Alternatives considered

| Option | Verdict |
| --- | --- |
| `pypost/core/constants.py` | **Selected** — simple, matches debt ticket suggestion |
| Colocate with `SensitiveDataMaskingPolicy` | Rejected — different placeholder semantics |
| Re-export from mixins for compat | Rejected — hides new canonical location |

## Testing Strategy

Run targeted regression:

```bash
QT_QPA_PLATFORM=offscreen pytest \
  tests/test_hidden_toggle_log_policy.py \
  tests/test_env_dialog.py \
  tests/test_variable_hover.py \
  tests/test_env_persistence_e2e.py \
  tests/test_settings_hidden_toggle_logging_e2e.py -v
```

No new tests required — behavior unchanged; existing assertions cover the constant value.

## Risks

- **Low**: pure import move; constant value unchanged.

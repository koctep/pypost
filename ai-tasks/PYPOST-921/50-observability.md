# PYPOST-921: Observability Implementation

## Verdict

**No new production logs or metrics required.** Plus-tab create already emits
`new_tab_action_triggered` (INFO) and increments
`gui_new_tab_actions_total{source=plus_button}` via
`TabsPresenter.handle_new_tab`. This story stamps a stable id on the existing
`+` button and adds golden coverage that exercises that path — identity apply
is silent, matching `PLUS_TAB_PLACEHOLDER` / `RESPONSE_PANEL` stamping.

## Logging Implementation

### Added Logs

None.

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A
- **WARNING**: N/A
- **NOTICE**: N/A
- **INFO**: N/A — do not log per-button id assignment
- **DEBUG**: N/A — prefer golden / unit failure over spam

### Why no new logs

| Change | Observability impact |
| --- | --- |
| `PLUS_TAB_BUTTON` in `widget_ids.py` | Catalog constant only |
| `set_widget_id(plus_btn, PLUS_TAB_BUTTON)` in `ensure_plus_tab` | Identity only |
| Golden plus-tab scenario | Reuses existing `handle_new_tab` INFO + metric |

### Existing path logging (reused, unchanged)

| Event | Level | Fields |
| --- | --- | --- |
| `new_tab_action_triggered` | INFO | `source`, `tabs_before` |
| `gui_new_tab_actions_total` | metric | `source=plus_button` |

Golden plus-tab create logs `source=plus_button tabs_before=0` after the
no-blank strip precondition.

## Metrics Implementation

None added. Existing labeled counter covers the create path.

## Validation

- Plus-tab golden run shows `new_tab_action_triggered source=plus_button
  tabs_before=0` in captured logs.
- No large payloads logged (URL/body stay out of id-apply path).

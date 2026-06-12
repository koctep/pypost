# PYPOST-112: Observability

## Existing logging (unchanged)

`MainWindow.apply_settings` retains DEBUG logs from PYPOST-106:

| Message | Level | Purpose |
| --- | --- | --- |
| `apply_settings_start font_size=%d` | DEBUG | Requested font size on entry |
| `apply_settings_font_applied point_size=%d` | DEBUG | Confirms app font after apply |

`open_settings` path logs `settings_applied font_size=%d` at INFO after save.

## Changes

No new log lines. Investigation task; observability contract unchanged.

## Metrics

None added.

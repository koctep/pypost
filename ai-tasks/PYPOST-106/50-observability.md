# PYPOST-106: Observability

## Existing logging (unchanged)

`MainWindow.apply_settings` already logs:

| Message | Level | Purpose |
| --- | --- | --- |
| `apply_settings_start font_size=%d` | DEBUG | Requested font size on entry |
| `apply_settings_font_applied point_size=%d` | DEBUG | Confirms app font after apply |

## Changes

No new log lines required. Font propagation mechanism changed but observability contract is
identical: developers can still trace font application via existing DEBUG messages.

## Metrics

None added — font settings are not a metrics surface.

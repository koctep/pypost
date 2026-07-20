# PYPOST-821: Observability

## Production observability

No changes. Tab close icons remain static SVG assets referenced from `main.qss`. No new
runtime logs or metrics are appropriate for a contrast-contract smoke test.

## Test observability

The smoke test asserts the post-PYPOST-796 dark-theme contrast contract:

- `close.svg` exists under `StyleManager.icons_dir`
- All SVG `stroke` values are `#999999` (not legacy `#666666`)
- Loaded QSS `QTabBar::close-button` references `close.svg`
- Hover rule still references `close-hover.svg`

No `caplog` or metrics assertions — this is an asset/path contract, not an error path.

## Validation Results

- [x] No production logging added (N/A)
- [x] Contract documented in test docstring and module constants
- [x] Large payloads not logged

## Notes

Visual dark-mode appearance on real macOS chrome remains a manual spot-check if icon design
changes beyond the stroke colour contract.

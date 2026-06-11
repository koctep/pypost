# PYPOST-395: Observability

## Logging

No new logging required. `JsonHighlighter` and theme resolution remain synchronous UI
paint-path helpers. Palette resolution is deterministic from `QPalette` with no I/O.

## Metrics

None added. Color rebinding on `apply_settings` is infrequent and not worth metric emission.

## Future

If `AppSettings` gains an explicit theme field, log a single DEBUG line when
`resolve_json_syntax_colors` switches palettes during `apply_settings`.

# PYPOST-68: Dev Docs

Updated `doc/dev/environments_dialog.md` with EnvPresenter public API summary.

## EnvPresenter public surface

Layout integration uses `widget` only. Font propagation: `apply_font(font)` or
`apply_settings(settings)` (reads app font). Environment selection for callers/tests:
`select_environment_index`, `environment_at`, `current_environment_index`,
`environment_count`, `environment_display_name_at`. MCP bar labels:
`mcp_status_text`, `mcp_tools_button_text`, `mcp_activity_button_text`.

Internal widgets (`_env_selector`, buttons, labels) are not exposed via properties.

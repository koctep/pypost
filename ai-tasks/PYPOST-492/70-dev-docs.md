# PYPOST-492: Dev Docs

## Updates

No `doc/dev/` changes required. Settings dialog layout is an implementation detail; behavior
and `AppSettings` fields are already documented under PYPOST-402/448 dev docs.

## Testing

```bash
pytest tests/test_settings_dialog.py -v
```

New class `TestSettingsDialogSecurityLoggingSection` asserts:

- Section header text "Security / Logging"
- Field order: retry codes → header → hidden-key checkbox → webhook URL → webhook auth

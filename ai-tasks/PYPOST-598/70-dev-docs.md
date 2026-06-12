# PYPOST-598 — Developer Documentation

## Summary

Updated `doc/dev/settings_dialog.md` with the split section-builder architecture introduced in
PYPOST-598 (D1 remediation).

## Components

| Module | Role |
| --- | --- |
| `pypost/ui/dialogs/settings_dialog.py` | Thin coordinator; public entry point and re-exports |
| `pypost/ui/widgets/settings/editor_section.py` | Font size, JSON indent |
| `pypost/ui/widgets/settings/request_section.py` | Request timeout, confirm-overwrite (split form rows) |
| `pypost/ui/widgets/settings/server_bind_section.py` | MCP/metrics host/port + bind validation |
| `pypost/ui/widgets/settings/encryption_config_section.py` | Tri-state encryption mode, key source, fallback |
| `pypost/ui/widgets/settings/encryption_migration_section.py` | Verify / re-encrypt / encrypt-plaintext actions |
| `pypost/ui/widgets/settings/retry_policy_section.py` | Default retry policy + codes validation |
| `pypost/ui/widgets/settings/security_alert_section.py` | Security/logging header, hidden-key logging, alerts |
| `pypost/ui/widgets/settings/_common.py` | Shared section header helper |

## Related

- [PYPOST-374](../PYPOST-374/30-dialogs-audit-report.md) — D1 finding (monolithic Settings dialog)
- [PYPOST-496](../PYPOST-496/70-dev-docs.md) — precedent: `EnvironmentDialog` facade + widgets
- [PYPOST-600](https://pypost.atlassian.net/browse/PYPOST-600) — encryption form-state dedup
- [PYPOST-602](https://pypost.atlassian.net/browse/PYPOST-602) — migration service injection

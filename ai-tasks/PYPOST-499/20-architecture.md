# PYPOST-499: Integration test for settings-to-encryption MainWindow flow

## Research

Production wiring (PYPOST-481):

| Stage | Component | Responsibility |
| --- | --- | --- |
| 1 | `SettingsDialog` | Encryption mode combo → `env_encryption_enabled` on `accept()` |
| 2 | `MainWindow.open_settings` | Save config, `env.wait_storage_idle()`, `storage.apply_encryption_settings` |
| 3 | `StorageManager` / `EnvironmentVariablesAdapter` | Resolve policy, rebuild codec, log `storage_encryption_config_applied` |

Existing coverage gaps mirror PYPOST-490 pattern: dialog and storage tested separately; no
connected MainWindow hop.

## Implementation Plan

1. Add `tests/test_settings_encryption_main_window_e2e.py`.
2. Reuse `_make_storage` pattern from `tests/test_storage_environments.py`.
3. Build partial `MainWindow` shell (patch heavy deps); inject real `StorageManager`.
4. Patch `SettingsDialog.exec` to `accept()` synchronously after configuring encryption combo.
5. Three parametrized cases: enabled, disabled, default (env fallback).
6. After `open_settings()`, save environment with hidden key; assert file payload encryption.

## Test Approach

Presenter-centric integration with thin MainWindow shell — not full GUI click-through.
Patch modal `exec()` like PYPOST-490. Verify policy via save round-trip and optional caplog
for `storage_encryption_config_applied`.

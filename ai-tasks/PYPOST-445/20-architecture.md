# PYPOST-445: Architecture

## Approach

Add one pytest integration test to `tests/test_settings_persistence.py` that exercises the
full settings save and restart path for `request_timeout` without modifying production code.

```mermaid
sequenceDiagram
    participant Test
    participant Dialog as SettingsDialog
    participant CM as ConfigManager
    participant Disk as settings.json
    participant CM2 as ConfigManager (restart)
    participant Dialog2 as SettingsDialog (reopen)

    Test->>CM: load_config() defaults
    Test->>Dialog: construct with settings
    Test->>Dialog: timeout_spin.setValue(135)
    Test->>Dialog: accept()
    Dialog-->>Test: AppSettings(request_timeout=135)
    Test->>CM: save_config(settings)
    CM->>Disk: write JSON
    Test->>CM2: new instance (restart)
    CM2->>Disk: read JSON
    CM2-->>Test: AppSettings(request_timeout=135)
    Test->>Dialog2: construct with reloaded settings
    Dialog2-->>Test: timeout_spin.value() == 135
```

## Test design

| Element | Choice |
| ------- | ------ |
| Fixture | Module-scoped `qapp` (new in this module) |
| Isolation | `tempfile.TemporaryDirectory` + patch `user_config_dir` |
| Changed value | `135` (distinct from default `60`) |
| Restart simulation | Fresh `ConfigManager()` after save |
| Assertions | Dialog accept output, JSON on disk, reload, spinbox on reopen |
| Timeout | Module `pytestmark = pytest.mark.timeout(120)` (existing) |

## Relationship to existing tests

| Test | Coverage |
| ---- | -------- |
| `test_save_then_load_roundtrip` | Direct `AppSettings` mutation + ConfigManager round-trip |
| `test_accept_includes_request_timeout_in_result` | Dialog accept only, no disk/restart |
| **New test** | SettingsDialog → save → restart → reopen |

## Out of scope

- MainWindow `open_settings()` wiring (covered indirectly via same save API).
- HTTP client timeout application at request execution time.

## Files touched

- `tests/test_settings_persistence.py` — new integration test + `qapp` fixture
- `doc/dev/settings_dialog.md` — document test coverage (STEP 7)

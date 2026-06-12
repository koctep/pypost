# PYPOST-374: Technical Debt Analysis

## Shortcuts Taken

- SOLID severity ratings are qualitative manual judgment (same as PYPOST-40); no radon/pylint.
- Widget internals (`EnvironmentListWidget`, etc.) not individually scored — only dialog shell.

## Code Quality Issues

Documented in [30-dialogs-audit-report.md](30-dialogs-audit-report.md):

| ID | Issue | Severity |
| --- | --- | --- |
| D1 | `SettingsDialog` multi-domain SRP violation (423 LOC) | High | [PYPOST-598](https://pypost.atlassian.net/browse/PYPOST-598) |
| D2 | `HotkeysDialog` hardcoded shortcuts vs app actions | Medium | [PYPOST-599](https://pypost.atlassian.net/browse/PYPOST-599) |
| D3 | Duplicated encryption mode parsing in `SettingsDialog` | Medium | [PYPOST-600](https://pypost.atlassian.net/browse/PYPOST-600) |
| D4 | Hardcoded About version | Low | [PYPOST-601](https://pypost.atlassian.net/browse/PYPOST-601) |
| D5 | `EncryptionMigrationService` constructed inside dialog | Low | [PYPOST-602](https://pypost.atlassian.net/browse/PYPOST-602) |

## Missing Tests

| Dialog | Gap |
| --- | --- |
| `about_dialog.py` | No automated tests |
| `hotkeys_dialog.py` | No automated tests |
| `mcp_activity_dialog.py` | No unit tests for formatters |
| `mcp_tools_overview_dialog.py` | No unit tests |
| `save_dialog.py` | Validation paths only via orchestrator mocks |

`env_dialog.py` and `settings_dialog.py` have substantial coverage — no blocker.

## Performance Concerns

None identified. Dialogs are modal, opened infrequently; `SettingsDialog` form size is a
maintainability concern, not runtime performance.

## Follow-up Tasks

| Priority | Description | Suggested Jira type |
| --- | --- | --- |
| P1 | Split `SettingsDialog` into section widgets / tabbed coordinator (D1) | Debt |
| P2 | Shared keyboard shortcut registry for HotkeysDialog (D2) | Debt |
| P2 | Extract encryption form builder in SettingsDialog (D3) | Debt |
| P3 | About version from package metadata (D4) | Debt |
| P3 | Unit tests for MCP dialog formatters and SaveRequestDialog validation (D5, D6) | Debt |

## Verdict

**SAFE TO CLOSE** — individual per-dialog SOLID audit delivered; inventory regression guard in
place; no unfixed blockers relative to acceptance criteria.

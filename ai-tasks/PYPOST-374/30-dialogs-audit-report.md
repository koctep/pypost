# PYPOST-374: Individual Dialog SOLID Audit Report

**Date:** 2026-06-11
**Scope:** `pypost/ui/dialogs/` (eight modules, 1,030 LOC total)
**Methodology:** Manual walkthrough aligned with [PYPOST-40](../PYPOST-40/20-architecture.md)
**Baseline comparison:** PYPOST-40 grouped inventory ~400 LOC, five dialogs named

## Executive Summary

The current individual-dialog inventory contains eight modules. `SettingsDialog` is a thin
composition root over dedicated settings sections, while `McpServersDialog` manages explicit,
persisted MCP server configurations. **Three MCP dialogs**
(`mcp_activity_dialog.py`, `mcp_servers_dialog.py`, and `mcp_tools_overview_dialog.py`) use
injected data or callbacks rather than direct transport ownership. The activity and tools dialogs
are read-only; the server manager supports configuration and lifecycle changes. The audit is
complete for the full current scope.

**Top recommendations:**

1. **P1** — Continue keeping settings behavior in focused section widgets.
2. **P2** — Keep the hotkey reference sourced from the shared action registry.
3. **P3** — Add focused empty-state and validation coverage where dialog behavior grows.

---

## Module Inventory

| Module | LOC | Class | Responsibility | Opened from |
| --- | ---: | --- | --- | --- |
| `about_dialog.py` | 43 | `AboutDialog` | Static app information | `main_window.py` |
| `env_dialog.py` | 109 | `EnvironmentDialog` | Environment manager shell | env presenter |
| `hotkeys_dialog.py` | 69 | `HotkeysDialog` | Shared shortcut reference table | `main_window.py` |
| `mcp_activity_dialog.py` | 117 | `McpActivityDialog` | MCP activity viewer | env presenter |
| `mcp_servers_dialog.py` | 333 | `McpServersDialog` + editor | MCP server manager | main window |
| `mcp_tools_overview_dialog.py` | 74 | Tool overview | MCP tools | env |
| `save_dialog.py` | 93 | `SaveRequestDialog` | Save-as picker | save orchestrator |
| `settings_dialog.py` | 192 | `SettingsDialog` | Settings composition | main window |

**Total:** 1,030 LOC (vs PYPOST-40 grouped ~400 LOC).

Regenerate counts: `scripts/audit_dialogs_inventory.py --markdown`

---

## SOLID Assessment by Dialog

### `about_dialog.py` — AboutDialog

| Principle | Rating | Notes |
| --- | --- | --- |
| SRP | OK | Displays static app information only |
| OCP | OK | No extension points needed |
| LSP | N/A | No inheritance |
| ISP | OK | Minimal QWidget surface |
| DIP | OK | Reads the package version only |

**Maintainability:** The displayed version is sourced from package metadata. **Test coverage:**
Display-only; low risk.

### `env_dialog.py` — EnvironmentDialog

| Principle | Rating | Notes |
| --- | --- | --- |
| SRP | OK | Thin composition root for environment list and variables widgets |
| OCP | OK | Behavior extends through focused widgets |
| LSP | N/A | No inheritance |
| ISP | OK | Delegates focused operations |
| DIP | Good | Receives environment data and import/export callbacks |

**Maintainability:** Widget delegation keeps environment editing separate from dialog layout.
**Test coverage:** Strong (`tests/test_env_dialog.py`, e2e).

### `hotkeys_dialog.py` — HotkeysDialog

| Principle | Rating | Notes |
| --- | --- | --- |
| SRP | OK | Presents shortcut rows only |
| OCP | OK | Rows come from the shared hotkey collector |
| LSP | N/A | No inheritance |
| ISP | OK | Self-contained |
| DIP | Good | Depends on the shared action-derived row collector |

**Maintainability:** The table no longer duplicates shortcut definitions. **Test coverage:**
Display behavior is low risk.

### `mcp_activity_dialog.py` — McpActivityDialog

| Principle | Rating | Notes |
| --- | --- | --- |
| SRP | OK | Read-only MCP activity table |
| OCP | OK | New columns extend pure formatters |
| LSP | N/A | No inheritance |
| ISP | OK | `set_entries` is focused |
| DIP | Good | Activity entries are injected |

**Maintainability:** Module-level formatters are unit-test friendly. **Test coverage:** Low
logic risk; direct formatter coverage remains a useful follow-up.

### `mcp_servers_dialog.py` — McpServersDialog

| Principle | Rating | Notes |
| --- | --- | --- |
| SRP | OK | Manages persisted MCP server rows and their editor workflow |
| OCP | Partial | Table columns and editor fields are local to the configuration model |
| LSP | N/A | No inheritance |
| ISP | Good | Receives narrow callbacks for configuration, status, lifecycle, and activity |
| DIP | Good | Uses injected callbacks and collections/environments rather than transport globals |

**Maintainability:** The 333-LOC dialog separates row management from `_McpServerEditor` input
validation. It exposes activity and tools as read-only views and keeps legacy conversion explicit.
**Test coverage:** Direct coverage in `tests/test_mcp_servers_dialog.py`.

### `mcp_tools_overview_dialog.py` — McpToolsOverviewDialog

| Principle | Rating | Notes |
| --- | --- | --- |
| SRP | OK | Read-only MCP tools table |
| OCP | OK | New columns extend the presentation mapping |
| LSP | N/A | No inheritance |
| ISP | OK | Constructor receives overview entries |
| DIP | Good | No service coupling |

**Maintainability:** Parallel to `McpActivityDialog`; a shared read-only table helper is optional.
**Test coverage:** Low logic risk.

### `save_dialog.py` — SaveRequestDialog

| Principle | Rating | Notes |
| --- | --- | --- |
| SRP | OK | Captures a save name and collection choice |
| OCP | Low | New collection handling is local to the dialog |
| LSP | N/A | No inheritance |
| ISP | OK | Exposes result fields only |
| DIP | Partial | Receives collections and delegates validation messages |

**Maintainability:** Caller-facing result fields remain a clear orchestrator contract.
**Test coverage:** Indirect through orchestrator coverage.

### `settings_dialog.py` — SettingsDialog

| Principle | Rating | Notes |
| --- | --- | --- |
| SRP | Good | Coordinates focused editor, request, bind, encryption, retry, and alert sections |
| OCP | Good | New settings can be added through a dedicated section |
| LSP | N/A | No inheritance |
| ISP | Good | Optional storage and migration dependencies stay scoped to encryption |
| DIP | Good | Receives storage and migration service seams |

**Maintainability:** At 192 LOC, the dialog delegates form construction, validation, and field
collection to dedicated widgets. **Test coverage:** Strong (`test_settings_dialog.py` and
encryption/migration UI tests).

---

## Cross-Cutting Maintainability

### Testability summary

| Dialog | Direct unit tests | Integration / mock coverage |
| --- | --- | --- |
| `about_dialog.py` | No | Manual/display-only |
| `env_dialog.py` | Yes | E2E persistence |
| `hotkeys_dialog.py` | No | Shared collector coverage |
| `mcp_activity_dialog.py` | No | Presenter opens with activity data |
| `mcp_servers_dialog.py` | Yes | Presenter and configuration mocks |
| `mcp_tools_overview_dialog.py` | No | Presenter opens with overview data |
| `save_dialog.py` | Indirect | Orchestrator mocks |
| `settings_dialog.py` | Yes | Main-window and encryption UI tests |

### Coupling

- Dialogs do not own MCP transport or metrics-manager globals.
- `SettingsDialog` composes focused settings sections and receives its optional storage/migration
  seams.
- MCP dialogs receive data or callback dependencies; the server manager keeps lifecycle work out
  of their UI tables.
- Launch sites use modal `exec()` patterns that presenters and orchestrators can mock.

---

## Prioritized Recommendations

### P1 — Near-term

| ID | Dialog | Recommendation | Impact | Effort |
| --- | --- | --- | --- | --- |
| D1 | `settings_dialog.py` | Preserve settings-section boundaries | Medium | Low |

### P2 — Next sprint / backlog

| ID | Dialog | Recommendation | Impact | Effort |
| --- | --- | --- | --- | --- |
| D2 | `mcp_activity_dialog.py` | Add formatter and empty-state tests as it grows | Low | Low |
| D3 | `mcp_tools_overview_dialog.py` | Share a helper after a third pattern | Low | Low |

### P3 — Nice-to-have

| ID | Dialog | Recommendation | Impact | Effort |
| --- | --- | --- | --- | --- |
| D4 | `save_dialog.py` | Add direct tests for empty names and new collections | Low | Low |

---

## Verdict

Individual audit **complete** for all eight modules. No dialog-level **blockers** for closing
PYPOST-374; findings are documented maintenance and test follow-ups. The primary maintenance
focus is preserving the current settings-section boundaries and callback-injected MCP dialog
design.

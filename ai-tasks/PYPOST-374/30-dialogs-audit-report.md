# PYPOST-374: Individual Dialog SOLID Audit Report

**Date:** 2026-06-11  
**Scope:** `pypost/ui/dialogs/` (seven modules, 923 LOC total)  
**Methodology:** Manual walkthrough aligned with [PYPOST-40](../PYPOST-40/20-architecture.md)  
**Baseline comparison:** PYPOST-40 grouped inventory ~400 LOC, five dialogs named

## Executive Summary

Individual dialog review shows **one high-severity SRP concern** (`SettingsDialog`, 423 LOC)
combining appearance, MCP/metrics, encryption migration, retry policy, and alerting. Five
dialogs are read-only or thin form shells with acceptable SOLID posture. **Two MCP read-only
dialogs** (`mcp_activity_dialog.py`, `mcp_tools_overview_dialog.py`) were absent from the
original audit and follow a strong data-injection pattern.

**Top recommendations:**

1. **P1** — Split `SettingsDialog` into section widgets or a presenter-backed tabbed dialog.
2. **P2** — Single source of truth for keyboard shortcuts (`HotkeysDialog` vs app actions).
3. **P3** — Resolve hardcoded About version; add focused unit tests for data-driven dialogs.

---

## Module Inventory

| Module | LOC | Class | Responsibility | Opened from |
| --- | ---: | --- | --- | --- |
| `about_dialog.py` | 40 | `AboutDialog` | Static app info | `main_window.py` |
| `hotkeys_dialog.py` | 91 | `HotkeysDialog` | Shortcut reference table | `main_window.py` |
| `save_dialog.py` | 91 | `SaveRequestDialog` | Save-as collection picker | `request_save_orchestrator.py` |
| `env_dialog.py` | 89 | `EnvironmentDialog` | Environment manager shell | `env_presenter.py` |
| `settings_dialog.py` | 423 | `SettingsDialog` | Global app settings + migration | `main_window.py` |
| `mcp_activity_dialog.py` | 117 | `McpActivityDialog` | MCP activity log viewer | `env_presenter.py` |
| `mcp_tools_overview_dialog.py` | 72 | `McpToolsOverviewDialog` | MCP tool catalog viewer | `env_presenter.py` |

**Total:** 923 LOC (vs PYPOST-40 grouped ~400 LOC — Settings growth + two MCP dialogs).

Regenerate counts: `scripts/audit_dialogs_inventory.py --markdown`

---

## SOLID Assessment by Dialog

### `about_dialog.py` — AboutDialog

| Principle | Rating | Notes |
| --- | --- | --- |
| SRP | OK | Displays static about content only |
| OCP | OK | No extension points needed |
| LSP | N/A | No inheritance |
| ISP | OK | Minimal QWidget surface |
| DIP | OK | No external services |

**Maintainability:** Hardcoded version string `"Version 0.1.0"` (line 22) — not tied to package
metadata. **Test coverage:** None (display-only; low risk).

---

### `hotkeys_dialog.py` — HotkeysDialog

| Principle | Rating | Notes |
| --- | --- | --- |
| SRP | OK | Reference list only; no shortcut registration |
| OCP | Low | New shortcuts require editing embedded list (lines 39–59) |
| LSP | N/A | No inheritance |
| ISP | OK | Self-contained |
| DIP | OK | No dependencies |

**Maintainability:** Shortcut table is **duplicated knowledge** vs `main_window` / presenter
`QAction` definitions — drift risk when shortcuts change. **Test coverage:** None.

---

### `save_dialog.py` — SaveRequestDialog

| Principle | Rating | Notes |
| --- | --- | --- |
| SRP | OK | Save-as name + collection selection |
| OCP | Low | "New collection" branch is inline (lines 66–89) |
| LSP | N/A | No inheritance |
| ISP | OK | Exposes result fields only |
| DIP | Partial | Receives `collections` list; validation via `collection_item_dialogs` helpers |

**Maintainability:** Validation delegated to shared dialog helpers (good). Mutable result fields
(`request_name`, `selected_collection_id`) are caller contract — documented by usage in
`request_save_orchestrator.py`. **Test coverage:** Indirect via orchestrator mocks only.

---

### `env_dialog.py` — EnvironmentDialog

| Principle | Rating | Notes |
| --- | --- | --- |
| SRP | OK | Thin composition root for list + variables widgets |
| OCP | OK | Behavior extended via `EnvironmentListWidget` / `EnvironmentVariablesWidget` |
| LSP | N/A | No inheritance |
| ISP | OK | Delegates to focused widgets |
| DIP | Good | Injects environments; callbacks for current env name |

**Maintainability:** Facade with many one-line delegates (lines 67–89) — acceptable after
PYPOST-496 widget extraction. **Test coverage:** Strong (`tests/test_env_dialog.py`, e2e).

---

### `settings_dialog.py` — SettingsDialog

| Principle | Rating | Notes |
| --- | --- | --- |
| SRP | **High violation** | Font, timeout, MCP, metrics, encryption, migration, retry, alerts in one class |
| OCP | Low | Each new setting modifies `__init__`, form rows, and `accept()` |
| LSP | N/A | No inheritance |
| ISP | Low | Callers get full settings surface; migration buttons optional via `storage` |
| DIP | Partial | Optional `StorageManager`; creates `EncryptionMigrationService` internally (113–115) |

**Maintainability:**

- 423 LOC — largest UI module in scope; `_encryption_settings_from_form` vs `accept()` duplicate
  encryption mode parsing (lines 307–323 vs 387–393).
- Structured logging present for encryption verify/re-encrypt and retry validation (good).
- **Test coverage:** Strong (`test_settings_dialog.py`, encryption/migration UI tests).

---

### `mcp_activity_dialog.py` — McpActivityDialog

| Principle | Rating | Notes |
| --- | --- | --- |
| SRP | OK | Read-only MCP activity table |
| OCP | OK | New columns would extend formatters |
| LSP | N/A | No inheritance |
| ISP | OK | `set_entries` API |
| DIP | Good | Entries injected; formatters are pure functions (95–117) |

**Maintainability:** Module-level formatters are unit-test friendly. **Test coverage:** None
direct; low logic risk.

---

### `mcp_tools_overview_dialog.py` — McpToolsOverviewDialog

| Principle | Rating | Notes |
| --- | --- | --- |
| SRP | OK | Read-only MCP tools table |
| OCP | OK | Same pattern as activity dialog |
| LSP | N/A | No inheritance |
| ISP | OK | Constructor receives entries |
| DIP | Good | No service coupling |

**Maintainability:** Parallel to `McpActivityDialog`; could share a small read-only table helper
(future, not required). **Test coverage:** None direct.

---

## Cross-Cutting Maintainability

### Testability summary

| Dialog | Direct unit tests | Integration / mock coverage |
| --- | --- | --- |
| `about_dialog.py` | No | Manual only |
| `hotkeys_dialog.py` | No | Manual only |
| `save_dialog.py` | No | Orchestrator mocks |
| `env_dialog.py` | Yes | E2E persistence |
| `settings_dialog.py` | Yes | Main-window e2e |
| `mcp_activity_dialog.py` | No | Presenter opens with live log |
| `mcp_tools_overview_dialog.py` | No | Presenter opens with overview service |

### Coupling

- Dialogs do **not** import `MetricsManager` or `template_service` globals (unlike core modules).
- `SettingsDialog` is the only dialog reaching into core services (`EncryptionMigrationService`,
  `StorageManager`, retry/encryption parsers).
- Launch sites use modal `exec()` pattern — testable via presenter/orchestrator mocks.

---

## Prioritized Recommendations

### P1 — Near-term

| ID | Dialog | Recommendation | Impact | Effort |
| --- | --- | --- | --- | --- |
| D1 | `settings_dialog.py` | Split into section widgets (General, Servers, Encryption, Retry/Alerts) or tabbed sub-dialogs with a thin coordinator | High | High |

### P2 — Next sprint / backlog

| ID | Dialog | Recommendation | Impact | Effort |
| --- | --- | --- | --- | --- |
| D2 | `hotkeys_dialog.py` | Derive shortcut list from a shared registry used by `main_window` / presenters | Medium | Medium |
| D3 | `settings_dialog.py` | Extract encryption form state builder to remove duplication between `accept()` and migration handlers | Medium | Low |

### P3 — Nice-to-have

| ID | Dialog | Recommendation | Impact | Effort |
| --- | --- | --- | --- | --- |
| D4 | `about_dialog.py` | Read version from package metadata (`importlib.metadata`) | Low | Low |
| D5 | `mcp_*_dialog.py` | Optional shared read-only table builder; add unit tests for formatters / empty state | Low | Low |
| D6 | `save_dialog.py` | Direct unit tests for validation paths (empty name, new collection) | Low | Low |

---

## Appendix: Finding References

| ID | File | Lines | Description |
| --- | --- | --- | --- |
| D1 | settings_dialog.py | 99–420 | SettingsDialog multi-domain SRP violation |
| D2 | hotkeys_dialog.py | 39–59 | Hardcoded shortcuts list |
| D3 | settings_dialog.py | 307–323, 387–393 | Duplicated encryption mode parsing |
| D4 | about_dialog.py | 22 | Hardcoded version placeholder |
| D5 | settings_dialog.py | 113–115 | Internal EncryptionMigrationService construction |
| D6 | — | — | MCP dialogs missing from PYPOST-40 inventory (scope drift) |

---

## Verdict

Individual audit **complete** for all seven modules. No dialog-level **blockers** for closing
PYPOST-374; findings are documented refactor and test follow-ups. Primary maintenance risk
remains `SettingsDialog` size and setting-domain mixing (D1).

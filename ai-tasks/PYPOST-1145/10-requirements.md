# PYPOST-1145: UI — Refactor SettingsDialog into categorized tabbed layout

## Goals

PyPost's Settings dialog has grown to nine configuration domains (editor, requests, server
bind, encryption, migration, retries, security, alerts, WebSocket). They are stacked in one
long vertical form, which is hard to scan and will worsen as preferences expand.

This tech-debt item reorganizes Settings into **categorized tabs** so operators can find
related options quickly and maintainers can add new domains without lengthening a single scroll
surface. Recorded in `ai-tasks/PYPOST-1136/60-tech-debt.md`.

**Implementation language:** Python (PySide6 / Qt widgets in `pypost/ui/dialogs/` and
`pypost/ui/widgets/settings/`).

## User Stories

- As a **PyPost operator**, I want Settings grouped into clear categories (General, Requests,
  Network, Security, Encryption), so that I can find a preference without scrolling through an
  entire page of unrelated fields.
- As a **maintainer**, I want each settings domain placed on an appropriate tab page, so that
  new sections can be added without degrading layout readability.
- As a **test author**, I want automated verification of the tab structure and section
  placement, so that regressions to a single long form are caught in CI.

## Definition of Done

The task is considered done when:

1. **Tabbed layout**
   - `SettingsDialog` presents settings in a `QTabWidget` with labeled category tabs aligned
     to `doc/user/settings.md` groupings.
   - Save/Cancel buttons remain outside the tab widget (dialog chrome unchanged).

2. **Behavior preservation**
   - All existing settings fields remain editable with the same labels, validation, and
     `accept()` persistence semantics.
   - Widget attributes on `SettingsDialog` remain for backward-compatible test and caller access.
   - `SETTINGS_DIALOG` widget identity is unchanged.

3. **Automated verification**
   - A dedicated test module asserts tab labels and section placement.
   - Existing settings tests pass with updated layout accessors where needed.
   - `make test` and `make lint` pass.

4. **Documentation**
   - Developer docs describe the tabbed coordinator layout and category mapping.

## Task Description

### Problem

`SettingsDialog` appends all section builders into one `QFormLayout`, producing a long
single-column form. WebSocket settings (PYPOST-1136) exacerbated the scroll length.

### Scope

**In scope:**

- `QTabWidget` (or equivalent stacked navigation) with categorized pages per domain group.
- Thin coordinator refactor in `settings_dialog.py`; section builder modules unchanged.
- Layout tests and developer documentation update.

**Out of scope:**

- Changing field labels, defaults, validation rules, or `AppSettings` schema.
- Side-navigation (`QListWidget` + `QStackedWidget`) — tabs are sufficient for current scale.
- User-facing `doc/user/settings.md` rewrite (structure already documents categories).
- Migrating `SettingsDialog` from modal `exec()` to `open()` (separate debt item).

## Q&A

**Q: Which tab categories?**
A: General (editor/appearance), Requests & Retries, Network (MCP/metrics + WebSocket),
Security & Alerts, Encryption (config + migration) — matching user-guide section groupings.

**Q: Must legacy `form_layout` API remain?**
A: Tests may use a cross-tab `form_layout_index_of()` helper; single-form `form_layout` is
replaced by per-tab forms.

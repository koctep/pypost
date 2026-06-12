# PYPOST-599: HotkeysDialog derives shortcuts from app actions

## Goals

The Help → Hotkeys dialog currently lists keyboard shortcuts from a hardcoded table. When
shortcuts change in `MainWindow` or the request editor, the help text can drift out of sync.
This task addresses finding **D2** from the [PYPOST-374 dialogs audit](../PYPOST-374/30-dialogs-audit-report.md)
so the dialog always reflects the shortcuts actually registered in the application.

## Programming Language

Python 3.10+ (PyPost project standard).

## User Stories

- As a **user**, I want the Hotkeys help dialog to list the same shortcuts the application
  actually responds to.
- As a **developer**, I want to change a shortcut in one place without updating a duplicate
  table in `hotkeys_dialog.py`.

## Definition of Done

1. `HotkeysDialog` no longer contains a hardcoded shortcut table.
2. Shortcuts shown in the dialog are derived from `QAction` metadata registered on the main
   window and request editor widgets.
3. Section groupings (General, Tabs, Request Editor) and row labels remain recognizable to
   users (e.g. "Quit Application", "Save Request").
4. Multi-key bindings (Settings: Ctrl+, and F12; Send: F5 and Ctrl+Return; tab switch
   Alt+1–9) display in the same condensed format as before.
5. Existing shortcut behavior is unchanged (tab switching, send, save, settings, etc.).
6. Automated tests cover hotkey collection and dialog population.

## Task Description

### Problem

`HotkeysDialog` embeds a static list of action names and key strings (lines 39–59). Application
shortcuts are registered separately in `MainWindow._setup_shortcuts`, the File menu quit action,
and `RequestEditor` save shortcuts. This duplicated knowledge creates drift risk.

### In Scope

- Single source of truth for shortcut registration and help display via `QAction` properties.
- Refactor shortcut registration in `MainWindow` and `RequestEditor` to tag actions.
- Update `HotkeysDialog` to collect and render tagged actions from its parent window.

### Out of Scope

- Localizing shortcut labels or menu text.
- Documenting contextual shortcuts outside the main window tree (e.g. F2 rename in environment
  list, Ctrl+F in response search) unless they are later registered with the same mechanism.
- Changing shortcut key bindings or adding new shortcuts.
- Other PYPOST-374 dialog refactors (Settings split, About version, etc.).

## Functional Requirements

1. Help → Hotkeys opens a table with Action and Shortcut columns grouped by section headers.
2. General shortcuts include Quit, Settings, and Environment Manager.
3. Tabs shortcuts include new/close/next/previous tab and Alt+1–9 switch.
4. Request Editor shortcuts include send, save, save as, focus URL, and panel switches.
5. Dialog content updates automatically when parent-window actions change.

## Non-functional Requirements

- **Maintainability** — Adding or changing a shortcut requires editing registration code only,
  not the dialog.
- **Regression safety** — Save/send/tab shortcut integration tests continue to pass.

## Constraints and Assumptions

- Structural refactor; user-visible shortcut bindings stay the same.
- `HotkeysDialog` parent is `MainWindow` (existing call site).
- Audit snapshot for finding D2: PYPOST-374 dialogs audit (2026).

## Main Entities

| Entity | Attributes (business) | Interactions |
| --- | --- | --- |
| Hotkeys dialog | Section headers, action rows, shortcut text | Opened from Help menu; read-only reference |
| Application shortcut | Section, label, one or more key bindings | Registered on main window / editors; drives behavior |
| Help menu | Hotkeys item | Opens hotkeys dialog |

## Q&A

| Question | Answer |
| --- | --- |
| Why not keep a static table? | D2 drift risk — PYPOST-374 audit and PYPOST-11 tech debt. |
| Must every widget shortcut appear? | Only shortcuts registered via the shared hotkey helpers for this task. |
| Source reference | [PYPOST-374 D2](../PYPOST-374/60-tech-debt.md); `ai-tasks/PYPOST-374/60-tech-debt.md` line 15. |

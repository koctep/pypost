# PYPOST-1290: Window-wide guard: each live key sequence bound once (+ ambiguous-activation log)

## Goals

In desktop applications supporting extensive keyboard shortcuts, duplicate shortcut registrations
lead to silent failures where conflicting key combinations are silently disabled without errors or
diagnostic feedback. During PYPOST-1285, Help dialog display rows created as shortcut-bearing actions
conflicted with live tab shortcuts (such as F5, Ctrl+Return, and Ctrl+L), disabling essential actions
without any diagnostic visibility.

The business objective is twofold:
1. Guarantee shortcut integrity across the entire application window so that user keystrokes never
   fail silently due to accidental duplicate key registrations.
2. Ensure runtime operational visibility so that if an ambiguous key sequence activation ever occurs,
   a diagnostic warning is recorded to alert operators and maintainers.

## User Stories

- As a user, I want every keyboard shortcut to trigger its designated action reliably, so that I
  never experience unresponsive keys caused by silent shortcut collisions.
- As a maintainer, I want an automated guard protecting all window-level shortcuts, so that future
  feature additions or documentation rows cannot introduce conflicting key bindings.
- As an operator diagnosing user reports, I want ambiguous shortcut activations logged at runtime,
  so that keyboard conflict issues can be identified and resolved immediately.

## Definition of Done

This task is considered `done` when:
1. An automated window-wide verification rule checks the entire main window and confirms that each
   live key sequence is registered at most once within its active window/application scope.
2. Informational/documentation rows in help views are strictly separated from live operational
   shortcuts and cannot conflict with or shadow functional shortcuts.
3. When the windowing framework detects an ambiguous key sequence activation at runtime, an
   observability warning event is emitted with the conflicting key sequence.
4. All existing keyboard shortcuts across HTTP, WebSocket, and MCP Client tabs continue to function
   as designed without regression.
5. All automated quality checks pass per repository standards.

## Task Description

### Problem Description
Keyboard shortcuts are essential for productivity in API testing and protocol session management.
When multiple components or documentation rows register identical key combinations, framework ambiguity
rules suppress shortcut execution. Because no error is raised by default, users perceive the application
as frozen or broken.

### Scope
- Enforcing single-binding integrity for all live window-level key sequences in the main application window.
- Adding runtime ambiguity logging when conflicting shortcuts are triggered.
- Covering both direct shortcut bindings and action-attached shortcuts.
- Excluding non-window global operating-system hooks outside the application process.

### Business Entities
- **Live Shortcut**: A functional keyboard shortcut that triggers an application action when pressed.
- **Documentation Row**: An entry in a help view or dialog showing available shortcuts for reference,
  which must never intercept keyboard events.
- **Key Conflict**: An invalid state where two or more functional actions claim the same key sequence
  in the same context.
- **Ambiguous Keystroke**: A runtime condition where a user presses a key sequence associated with
  multiple active handlers.

### Non-Functional Requirements
- **Reliability**: Zero tolerance for silent shortcut failure.
- **Performance**: Automated verification must run efficiently as part of standard test execution.
- **Auditability**: Unambiguous log entries whenever key conflicts occur.

### Constraints and Assumptions
- Implementation language: Python.
- Must integrate cleanly with the existing desktop UI framework and logging infrastructure.

## Q&A

- **Q: Why is an automated window-wide check necessary if PYPOST-1285 already fixed Help rows?**
  **A:** PYPOST-1285 only fixed the immediate documentation rows for protocol tabs. It did not prevent
  future developers from adding duplicate live shortcuts or new conflicting actions in other menus.
- **Q: Why should ambiguous activations be logged at runtime if tests prevent duplicates?**
  **A:** Dynamic actions, plugin additions, or platform-specific shortcut mappings could introduce
  unexpected collisions at runtime. Logging ambiguous activations ensures operational observability
  instead of silent user failure.

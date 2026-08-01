# PYPOST-917: Optional keystroke-realism fill mode

## Goals

Agent and automated harness flows must keep a fast, deterministic default
fill for golden-flow and seed drive proofs, while callers who need
keystroke-level realism (IME behaviour, validation-on-key, typing-driven
UI) can opt into a character-by-character fill path without changing
existing scripts.

This debt comes from [PYPOST-851](https://pypost.atlassian.net/browse/PYPOST-851)
/ [PYPOST-836](https://pypost.atlassian.net/browse/PYPOST-836) follow-up:
default fill replaces text in one shot; keystroke delivery today is only
via per-key send, which is awkward for whole-string realism.

## Programming Language

Python (PySide6), with English Markdown developer docs.

## User Stories

- As an **agent / e2e author**, I want the default fill to keep replacing
  field text in one shot so offscreen CI and golden flows stay stable
  and fast.
- As an **agent / e2e author**, I want an opt-in fill mode that types the
  string as keystrokes when I need IME, validation-on-key, or similar
  realism.
- As a **maintainer**, I want both modes documented so callers know when
  to use default fill vs keystroke fill vs single-key send.
- As a **CI owner**, I want automated tests for both fill modes so neither
  path regresses silently.

## Definition of Done

- Agent fill exposes an opt-in keystroke-realism mode; default remains
  one-shot text replacement.
- Existing fill call sites continue to work without opting in.
- Automated tests cover both the default and the opt-in mode.
- Developer docs describe when each fill mode applies (and how it relates
  to single-key send).
- Unticketed follow-ups (if any) live only in this task’s
  `60-tech-debt.md` (no Jira ticket creation in this run).

## Task Description

**Problem:** Agent fill always replaces the whole field value at once.
That is correct for deterministic harnesses, but agents that need
keystroke-level realism (IME, validation that runs per character) have
no opt-in whole-string path — only repeated single-key sends.

**Business need:** One opt-in agent fill mode for keystroke realism,
without changing the default fill that golden / seed / CI already rely on.

### In Scope

- Add an opt-in keystroke-realism fill mode on the agent fill capability
  (module API and session mirror).
- Keep default fill as one-shot text replacement.
- Document both modes for callers.
- Add automated coverage for both modes.
- Preserve existing fill call sites that do not opt in.

### Out of Scope

- Changing production UI widgets, IME plugins, or identity catalog.
- Replacing `ui_send_key` for single keys / hotkeys.
- Making keystroke fill the default for golden or seed flows.
- Out-of-process MCP packaging of UI actions.
- Creating Jira Debt tickets (orchestrator Phase D).
- Commit or Jira status transitions (orchestrator).

## Functional Requirements

- FR1: Default fill replaces the target field’s text in one shot (current
  behaviour for callers that do not opt in).
- FR2: Callers can opt into a keystroke-realism fill mode that delivers
  the string as typed characters.
- FR3: Opt-in is explicit; omitting it leaves default fill unchanged.
- FR4: Wrong widget type, missing target, or non-interactable control
  raises the same class of actionable agent UI errors as today.
- FR5: Session mirror supports the same opt-in as the module API.
- FR6: Developer docs describe default vs keystroke fill and when to use
  single-key send instead.
- FR7: Tests prove both default and opt-in fill modes.

## Non-Functional Requirements

- NFR1: Suit fixture-style tests (offscreen Qt); no live network.
- NFR2: Explicit pytest timeouts per `.cursor/lsr/do-testing.md`.
- NFR3: Logs must not dump fill text beyond existing action scalars
  (`widget_id`, outcome, duration); mode may be logged as a scalar if
  useful.
- NFR4: English docs; line length ≤ 100 where practical.
- NFR5: Default fill remains suitable for high-volume golden / seed
  drives (no mandatory keystroke path).

## Constraints and Assumptions

- Parent debt: PYPOST-836 / PYPOST-851 “Optional fill-via-keyClicks mode”.
- Widgets are already named via stable `objectName` / widget ids.
- Single-key / hotkey delivery remains a separate capability; this task
  is whole-string fill modes only.
- Sprint-task-runner batch: no user approval gates; no commit / Jira
  writes in this subagent run.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Agent / harness | Drives named UI after ready |
| Fill action | Sets text on a named input control |
| Default fill mode | One-shot text replacement (deterministic) |
| Keystroke fill mode | Opt-in character-by-character delivery |
| Text input control | Line edit / plain / rich text field |
| Single-key send | Separate action for one key or hotkey |

## Q&A

| Q | A |
| --- | --- |
| Why not always type keystrokes? | Default one-shot fill is faster and more stable under offscreen CI; acceptance requires opt-in only. |
| Why not only use single-key send? | Whole-string realism needs a first-class fill mode; per-key loops are awkward and undocumented for this use. |
| Must golden flows switch? | No — they keep default fill unless a scenario explicitly needs keystroke realism. |
| Jira / commit in this run? | No — parent orchestrator owns Phase D/F. |

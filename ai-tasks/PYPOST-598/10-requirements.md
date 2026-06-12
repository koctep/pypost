# PYPOST-598: Separate settings domains in the Settings dialog

## Goals

The Settings dialog has grown into the largest dialog in the application and combines many
unrelated configuration areas in one place. That coupling increases the risk and cost of
changes: a fix or enhancement in one area can unintentionally affect others, and reviewers
must understand the full surface to approve a small change.

This task addresses finding **D1** from the [PYPOST-374 dialogs audit](../PYPOST-374/30-dialogs-audit-report.md)
by separating those concerns so each settings domain can evolve independently while users
experience no change in behavior.

## Programming Language

Python 3.10+ (PyPost project standard).

## User Stories

- As a **developer**, I want each settings domain isolated so I can modify editor
  preferences, server bindings, encryption, retry defaults, or alerting without touching
  unrelated areas.
- As a **user**, I want the Settings dialog to offer the same options, labels, validation
  messages, and save/cancel behavior as today.
- As an **operator**, I want encryption maintenance actions (verify, re-encrypt,
  encrypt plaintext hidden values) to remain available when storage is provided, with the
  same confirmations and result reporting as today.

## Definition of Done

1. The Settings dialog still exposes every setting category currently available:
   editor/display preferences, request behavior, MCP and metrics server bindings,
   environment encryption configuration, encryption maintenance actions, default retry
   policy, security/logging options, and alert notification settings.
2. Saving settings produces the same persisted values and validation outcomes as before
   (including bind-address and retryable-status-code validation feedback).
3. Encryption maintenance actions behave as today when storage is available; controls stay
   disabled when storage is not provided.
4. The dialog remains openable from the main window with the same inputs and behavior as
   today.
5. All existing quality checks for the Settings dialog pass with no behavioral regressions.
6. A change limited to one settings domain does not require modifying unrelated domains.

## Task Description

### Problem

The Settings dialog currently combines multiple configuration domains in a single,
monolithic implementation. Domains include appearance, HTTP timeouts, MCP and metrics
server endpoints, environment encryption, encryption migration operations, default retry
policy, security and logging toggles, and alert webhook configuration.

### In Scope

- Reorganizing the Settings dialog so each domain above can be maintained independently.
- Preserving user-visible layout groupings (section headers such as "Encryption migration"
  and "Security / Logging" remain meaningful to users).

### Out of Scope

- Duplicated encryption form-state logic ([PYPOST-600](https://pypost.atlassian.net/browse/PYPOST-600), finding D3).
- Where migration services are constructed ([PYPOST-602](https://pypost.atlassian.net/browse/PYPOST-602), finding D5).
- Adding, removing, or renaming settings fields or changing their business meaning.
- Changing how settings are persisted or how the main window applies saved settings.
- Other dialog refactors from PYPOST-374 (e.g. HotkeysDialog, [PYPOST-599](https://pypost.atlassian.net/browse/PYPOST-599)).

## Functional Requirements

1. **Editor and display** — Font size and JSON indent size remain editable and persist on save.
2. **Request behavior** — Request timeout and confirm-before-overwrite toggle remain editable.
3. **MCP server** — Host and port remain editable with the same validation rules and error
   messages.
4. **Metrics server** — Host and port remain editable with the same validation rules and error
   messages.
5. **Environment encryption** — Tri-state encryption mode, key source selection, fallback list,
   contextual help text, and fallback parse warnings behave as today.
6. **Encryption maintenance** — Verify, re-encrypt all environments, and encrypt plaintext
   hidden values actions remain available with confirmations and result dialogs when storage
   is provided.
7. **Retry policy defaults** — Max retries, delay, backoff multiplier, and retryable status
   codes remain editable with the same validation.
8. **Security and logging** — Hidden-key-name logging toggle remains under a visible section.
9. **Alerting** — Alert log path, webhook URL, and webhook authorization header (including
   keep/clear semantics for stored secrets) behave as today.

## Non-functional Requirements

- **Maintainability** — A change limited to one settings domain should not require editing
  unrelated domain code.
- **Regression safety** — Existing automated checks for settings, encryption, migration UI,
  and main-window flows must pass.

## Constraints and Assumptions

- This task refactors structure, not product behavior.
- Setting fields and their business meaning are unchanged.
- The modal open-and-save flow from the main window is unchanged.
- Audit snapshot for finding D1: 2026-06-11.

## Main Entities

| Entity | Attributes (business) | Interactions |
| --- | --- | --- |
| Settings dialog | Window title, save/cancel actions, composed setting areas | Opened from main window; returns updated app settings on save |
| Editor preferences | Font size, JSON indent | Affect editor presentation after save |
| Request preferences | Timeout, overwrite confirmation | Affect HTTP request execution defaults |
| MCP server settings | Bind host, bind port | Affect local MCP endpoint |
| Metrics server settings | Bind host, bind port | Affect local metrics endpoint |
| Environment encryption settings | Enable/disable/default mode, key source, fallback chain | Affect how environment secrets are encrypted at rest |
| Encryption maintenance | Verify, bulk re-encrypt, encrypt plaintext actions | Operate on stored environments when storage is available |
| Retry policy defaults | Max retries, delay, backoff, retryable HTTP codes | Applied as defaults for new or retried requests |
| Security and logging | Log hidden variable key names on toggle | Affects diagnostic logging behavior |
| Alert notification settings | Log file path, webhook URL, authorization header | Affect where security alerts are delivered |

## Q&A

| Question | Answer |
| --- | --- |
| Why refactor if users see no change? | Reduce maintenance cost and regression risk as settings grow; D1 is P1 tech debt from PYPOST-374. |
| Should encryption parsing duplication be fixed here? | No — tracked as PYPOST-600 (D3). |
| Should migration service injection be fixed here? | No — tracked as PYPOST-602 (D5). |
| Must section headers stay visible? | Yes — users rely on visual grouping; content and order should remain recognizable. |
| Source reference | [PYPOST-374 dialogs audit](../PYPOST-374/30-dialogs-audit-report.md) finding D1; [tech-debt entry](../PYPOST-374/60-tech-debt.md). |

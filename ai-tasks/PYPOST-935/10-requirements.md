# PYPOST-935: SETTINGS_DIALOG objectName on SettingsDialog

## Goals

AI agents and automated harnesses already prove they can wait for the Settings
product dialog after opening it
([PYPOST-919](https://pypost.atlassian.net/browse/PYPOST-919)). That proof
today relies on window title and dialog type to recognize the modal — not on a
stable widget identity.

Other key PyPost surfaces expose canonical `pypost_*` identities so agents can
locate and wait on targets without coupling to display strings or Python types.
Settings is a real product dialog agents open frequently; it should follow the
same identity contract as the settings **button** and other stamped surfaces.

**Business why:** Give agents a stable, locale-independent way to recognize the
Settings dialog so dialog-settle and future dialog flows do not depend on title
text or `isinstance` checks that break when copy or class structure changes.

Source: [PYPOST-919](https://pypost.atlassian.net/browse/PYPOST-919) TD-2
(identity hygiene deferred from product dialog settle). Parent task folder:
`ai-tasks/PYPOST-919/`. Browse:
[PYPOST-935](https://pypost.atlassian.net/browse/PYPOST-935).

## Programming Language

Python (`.cursor/lsr/do-python.md`). UI identity on `SettingsDialog` and
related test/doc updates. Developer docs in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As an **AI agent / harness author**, I want the Settings dialog to expose a
  stable widget identity so I can wait for dialog presence by id instead of
  window title and type checks.
- As a **maintainer** of dialog-settle coverage, I want the existing Settings
  open → settle → dismiss proof to remain green after identity is added, with
  an optional switch to identity-based presence detection.
- As a **maintainer** of UI identity docs, I want the Settings dialog listed
  in the identity catalog so agents discover the constant without reading test
  predicates.
- As a **sibling story owner** (PYPOST-919 / PYPOST-934 dialog settle), I want
  this change to be additive identity hygiene — not a redesign of modal settle
  or wait helpers.

## Definition of Done

- `SettingsDialog` exposes a stable `SETTINGS_DIALOG` widget identity
  (`objectName` via the project’s `set_widget_id` convention).
- Existing dialog-settle `agent_e2e` coverage
  (`tests/test_agent_dialog_settle_e2e.py`, PYPOST-919 / PYPOST-934) remains
  passing after the identity is applied.
- Optional: dialog-settle presence predicate may use the new identity instead of
  (or in addition to) title + type — only if it simplifies the proof without
  weakening coverage.
- Developer identity documentation mentions the new constant.
- Unticketed follow-ups (if any) live only in this task’s `60-tech-debt.md`
  (no Jira ticket creation in this run).

Acceptance (from Jira): **SettingsDialog has `SETTINGS_DIALOG` objectName;
optional settle predicate update; existing dialog settle e2e still green.**

## Task Description

**Problem:** Product dialog settle (PYPOST-919) waits for Settings using
`QApplication.activeModalWidget()` combined with `windowTitle() == "Settings"`
and `isinstance(..., SettingsDialog)`. That couples automation to display copy
and Python class identity rather than the stable `pypost_*` objectName contract
used elsewhere (PYPOST-834).

**Business need:** Align Settings dialog with the project’s widget-identity
model so agents and tests can recognize the dialog the same way they recognize
the settings button, URL field, and response surfaces — durable across locale
and refactor.

### In Scope

- Add canonical `SETTINGS_DIALOG` constant and apply it on `SettingsDialog`
  construction via `set_widget_id`.
- Automated proof that the identity is present on a constructed Settings dialog.
- Keep existing dialog-settle `agent_e2e` tests green.
- Optional update of the dialog-settle presence predicate to prefer objectName.
- Minimal identity-catalog documentation.

### Out of Scope

- Redesigning dialog-settle flow, timer-before-`exec` pattern, or wait helpers
  (PYPOST-919 / PYPOST-837).
- Migrating `SettingsDialog` from `exec()` to `open()` (accepted product
  posture; PYPOST-919 out of scope).
- Full Settings functional testing (encryption, bind validation, theme, etc.).
- Adding identities to other product dialogs (confirm boxes, message boxes).
- Shared modal settle helper extraction (PYPOST-936).
- Creating Jira Debt tickets (unticketed items only in `60-tech-debt.md`).
- Commit or Jira status transitions / worklog MCP writes (orchestrator).

## Functional Requirements

- FR1: A canonical `SETTINGS_DIALOG` identity exists in the widget-id catalog.
- FR2: Every constructed `SettingsDialog` exposes that identity on
  `objectName` (and `accessibleIdentifier` mirror per project convention).
- FR3: Automated coverage asserts the identity on `SettingsDialog` after
  construction (or equivalent direct proof).
- FR4: Existing happy-path and timeout-companion dialog-settle `agent_e2e`
  tests continue to pass without regression.
- FR5: Optional: dialog-settle presence detection may use
  `objectName == SETTINGS_DIALOG` instead of title + `isinstance` when that
  does not weaken the proof.
- FR6: Identity documentation lists `SETTINGS_DIALOG` for agent authors.

## Non-Functional Requirements

- **Compatibility:** Additive only — `SETTINGS_BUTTON` and other identities
  unchanged; no new agent API required.
- **Locale independence:** Identity must not depend on window title or visible
  labels.
- **Minimalism:** One dialog, one constant, one apply site; no new wait
  subsystem.
- **CI suitability:** New assertion runs under standard `make test`; dialog
  settle remains under `make test-agent-e2e`.
- **Discoverability:** Catalog entry in `doc/dev/ui_identity.md`.

## Constraints and Assumptions

- Programming language: Python.
- Parent debt: PYPOST-919 TD-2 (Low); tracked as
  [PYPOST-935](https://pypost.atlassian.net/browse/PYPOST-935).
- Identity convention: `pypost_<surface>` via `set_widget_id`
  (`doc/dev/ui_identity.md`, PYPOST-834).
- `SettingsDialog` is application-modal; agents observe it via
  `activeModalWidget()` during settle — not as a child of the main window tree.
- Window title `"Settings"` may remain for humans; automation should prefer
  `objectName` once stamped.
- Step 1 review is treated as pre-approved under sprint-task-runner autonomy
  (no approval gate / no Jira updates in this step).

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Settings dialog | Product modal edited by users; target of stable identity |
| Widget-id catalog | Canonical string constants for agent lookup |
| AI agent / harness | Opens Settings, waits for dialog, may use identity |
| Dialog-settle coverage | Existing PYPOST-919 / PYPOST-934 proof that must stay green |
| Identity documentation | Maintainer-facing catalog of stamped surfaces |

Interaction overview:

1. User or agent opens Settings via the settings control.
2. Application creates `SettingsDialog` with stable `SETTINGS_DIALOG` identity.
3. Agent or test recognizes the modal by `objectName` (optionally via
   `activeModalWidget()`).
4. Existing dialog-settle scenario continues to pass with or without predicate
   migration to identity.

## Q&A

- Q: Why is this separate from PYPOST-919?
  A: PYPOST-919 proved dialog settle with title + type; TD-2 deferred widget
  id as optional identity hygiene. This ticket closes TD-2.

- Q: Must dialog-settle switch to the new id immediately?
  A: Optional per acceptance. Production stamp is required; predicate migration
  is recommended if it simplifies the test without weakening coverage.

- Q: Should `SETTINGS_DIALOG` join `KEY_WIDGET_IDS` / main-window spot-check?
  A: The dialog is modal and not under the main window during spot-check; a
  dedicated construction assertion is the primary proof (architecture decision
  in Step 2).

- Q: Does this change Settings user-visible behavior?
  A: No — `objectName` is for automation; window title and layout unchanged.

- Q: Create Jira follow-ups this run?
  A: No — list debt in `60-tech-debt.md` only.

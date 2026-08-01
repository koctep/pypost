# PYPOST-939: Support model-backed list views in agent select

## Goals

Agent and golden-flow harnesses must select rows on model-backed list views
(`QListView` and other flat `QAbstractItemView` targets) the same way they
already select `QListWidget` and `QTreeView` rows — by visible display text
or zero-based index — so future product UI that uses a plain list view does
not force ad-hoc model APIs in drive scripts.

This completes [PYPOST-916](https://pypost.atlassian.net/browse/PYPOST-916)
TD-1 follow-up from [PYPOST-916/60-tech-debt.md](../PYPOST-916/60-tech-debt.md).

## Programming Language

Python (PySide6), with English Markdown developer docs.

## User Stories

- As an **agent / e2e author**, I want to select a `QListView` row by display
  text so drive scripts match on-screen labels when the control is not a
  `QListWidget`.
- As an **agent / e2e author**, I want to select a model-backed list row by
  index when text is unstable.
- As a **maintainer**, I want the documented `ui_select` API to cover
  model-backed list views so callers do not bypass the agent primitive.
- As a **CI owner**, I want at least one automated non-`QListWidget` /
  non-`QTreeView` select path so the capability does not regress.

## Definition of Done

- Documented API path for `QListView` or generic flat `QAbstractItemView`.
- Automated tests cover at least one non-`QListWidget` / non-`QTreeView` case.
- Existing combo, `QListWidget`, and `QTreeView` select behaviour unchanged.
- Unticketed follow-ups (if any) live only in this task’s `60-tech-debt.md`.

## Task Description

**Problem:** Agent `ui_select` supports combo boxes, `QListWidget`, and
`QTreeView`. Golden flows that name a plain `QListView` (model view without
widget items) cannot use the agent select API today.

**Business need:** One agent-facing select capability for all common named
list/tree controls so harnesses stay consistent when product UI uses model
views.

### In Scope

- Extend agent select to `QListView` / flat model-backed `QAbstractItemView`.
- Document the API for callers.
- Add automated coverage for at least one non-widget-item view path.
- Keep existing combo / list widget / tree call sites working.

### Out of Scope

- Changing production UI widgets or identity catalog.
- Replacing tree viewport click helpers (selection ≠ open/activate).
- `QTableView` multi-column semantics beyond first-column DisplayRole.
- Jira ticket creation, commit, or status transitions (orchestrator skip).

## Functional Requirements

- FR1: Callers can select a `QListView` row by display text (column 0).
- FR2: Callers can select a model-backed list row by zero-based index.
- FR3: Combo, `QListWidget`, and `QTreeView` select paths remain unchanged.
- FR4: Missing model, wrong type, or missing option/index raises actionable
  agent UI errors.
- FR5: Developer docs describe the extended select API.
- FR6: Tests prove at least one non-`QListWidget` / non-`QTreeView` path.

## Non-Functional Requirements

- NFR1: Fixture-style offscreen Qt tests; no live network.
- NFR2: Explicit pytest timeouts per `.cursor/lsr/do-testing.md`.
- NFR3: Logs must not dump item payloads beyond existing action scalars.
- NFR4: English docs; line length ≤ 100 where practical.

## Constraints and Assumptions

- Parent debt: PYPOST-916 TD-1.
- Widgets are named via stable `objectName` / widget ids.
- Flat list views use column 0 DisplayRole for text match (same as tree walk
  contract for a single column).
- `QListWidget` continues to use widget-item APIs for efficiency.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Agent / harness | Drives named UI after ready |
| Select action | Chooses one row on a named control |
| Widget list | `QListWidget` with embedded items |
| Model list view | `QListView` backed by a data model |
| Display text | Visible label in column 0 |
| Index | Zero-based row position |

## Q&A

| Q | A |
| --- | --- |
| Why not only `QListWidget`? | Product may use plain `QListView`; TD-1 deferred this path. |
| Why after `QListWidget` dispatch? | Subclass shares API surface; widget path stays fast and unchanged. |
| Table views? | Out of scope unless a golden flow needs them; flat list view first. |

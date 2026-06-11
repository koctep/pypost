# PYPOST-408: Collections — sync names/metadata across duplicate isolated tabs

## Goals

PYPOST-405 let users open the same saved request in multiple independent tabs so unsaved
work in one tab does not overwrite what another tab shows. That isolation is correct for
in-progress edits, but users still need a trustworthy picture of what is saved on disk when
another tab or workflow updates the same request.

Today, renaming from the Collections sidebar updates tab titles across all tabs for that
request, yet saving substantive changes (URL, method, headers, body, or name via save) from
one tab leaves sibling tabs unaware. Users can unknowingly continue editing or saving stale
content and overwrite newer work. This task improves consistency and safety: tab labels stay
aligned with the saved name, and users are clearly informed when the persisted version of a
request they have open has changed elsewhere.

## Programming Language

Python (PySide6 / Qt), consistent with the PyPost desktop application.

## User Stories

- As a **PyPost user** with two tabs open for the same saved request, I want to **know when
  another tab has saved changes**, so I do not accidentally send or save outdated URLs or
  bodies believing they are current.
- As a **PyPost user**, I want **all tab titles for a request to show the same name** after
  a rename or save that changes the name, so I can identify tabs at a glance.
- As a **PyPost user** with **unsaved edits** in a tab, I want a **clear choice** when the
  saved version changed elsewhere (keep my draft or load the latest saved version), so my
  work is not discarded without consent.
- As a **PyPost user** who saved changes in one tab, I expect **the Collections tree to
  reflect the update** as it does today, without requiring me to manually refresh.

## Definition of Done

- When a saved request is **updated on disk** from one open tab, every **other open tab** for
  the same saved request is **notified** that the persisted version has changed.
- The notification makes clear **which request** changed and that the tab may show **outdated
  saved content** relative to disk (not merely a cosmetic label issue).
- If a notified tab has **no unsaved edits**, the user can **load the latest saved version**
  into that tab with a single explicit action offered as part of the notification flow.
- If a notified tab has **unsaved edits**, the user is offered a **choice**: continue with
  the local draft or replace the tab content with the latest saved version; the default path
  must **not silently discard** unsaved work.
- When a saved request **name changes** (via Collections rename or via save), **all open tabs**
  for that request show the **updated name** in the tab label.
- Saving from one tab continues to **update the Collections sidebar** for that request without
  regressing current behavior.
- Automated tests cover at least: save in tab A notifies tab B for the same request; rename
  or save-driven name change updates labels on all matching tabs; unsaved tab receives choice
  rather than silent overwrite.
- Developer documentation for isolated tabs is updated to describe the new behavior and
  remaining limitations (Step 7).

## Task Description

PyPost is a desktop HTTP client. Users open saved requests in tabs to edit and send traffic.
The “New tab” action (PYPOST-405) opens an independent working copy so parallel drafts do not
share unsaved state. The accepted trade-off in PYPOST-405 was that tabs could drift from the
on-disk copy after a save in another tab, with “last write wins” on subsequent saves.

That trade-off creates a **data-integrity and trust** problem: users lack feedback that disk
state changed. Sprint review flagged this as medium-priority follow-up work because stale URLs
and bodies are user-visible and can cause wrong requests or accidental overwrites.

This task addresses **awareness and naming consistency** across duplicate isolated tabs for the
same saved request identity. It does not attempt real-time collaborative editing or automatic
merging of conflicting drafts.

### In Scope

- Notifying open tabs when the **persisted** copy of a request they display has changed due
  to a save from another tab (or another save path for the same request id in the same
  session).
- Keeping **tab labels** consistent with the current saved request name across all tabs for
  that request.
- User flows when the notified tab has unsaved vs clean local state.
- Verification through automated tests and updated dev docs (in later steps).

### Out of Scope

- Merging concurrent edits or three-way diff resolution.
- Propagating **unsaved** in-memory edits from one tab to another.
- Changing **left-click** Collections navigation or tab-reuse behavior ([PYPOST-406]).
- Synchronizing **global environment variables** across tabs (they remain window-wide).
- Notifying tabs when **unrelated** requests or collections change.
- Push notifications when changes happen **outside** the running application (for example
  hand-edited files on disk while PyPost is open).

### Constraints and Assumptions

- Multiple tabs may reference the same saved request **identity** while holding separate
  in-memory drafts; isolation of unsaved state from PYPOST-405 remains required.
- “Saved request metadata” means the fields users edit before sending: name, URL, HTTP method,
  headers, body, and other request configuration persisted with the collection item—not
  transient response/history UI state.
- Users may legitimately keep an outdated draft after being notified; the product must not
  force reload, but must make the stale state obvious and avoid silent data loss on save
  where feasible (for example by reusing or extending existing overwrite confirmation when
  saving would replace a newer on-disk version).
- Collections sidebar refresh after save remains expected behavior.
- English UI strings should match existing dialog and confirmation tone.

## Functional Requirements

- The application must detect when a saved request’s persisted content changes while other
  tabs for that same request remain open.
- The application must inform users in those other tabs that the on-disk version is newer
  than what the tab loaded or last adopted from disk.
- The application must update tab labels on all open tabs for a request when its saved name
  changes, regardless of whether the rename originated from the Collections sidebar or from a
  save action.
- The application must preserve unsaved edits in a notified tab until the user explicitly
  chooses to load the latest saved version or saves/overwrites with informed consent.
- The application must allow a user to load the latest saved version into a notified tab when
  they choose to do so.
- The application must continue to refresh the Collections tree after saves without breaking
  tree selection or expansion behavior users rely on today.

## Non-functional Requirements

- **Predictability:** users can distinguish “my unsaved draft” from “what is saved on disk
  now” after a sibling tab saves.
- **Safety:** default flows do not discard unsaved work in a tab without an explicit user
  decision.
- **Responsiveness:** notification and optional reload must not noticeably block typing or
  sending from unaffected tabs.
- **Consistency:** naming and stale-state behavior apply uniformly to tabs opened via “New
  tab” and to multiple restored tabs for the same request id after restart, where applicable.

## Main Entities and Interactions

| Entity | Attributes | Role |
|--------|------------|------|
| **Saved request** | stable identity, name, URL, method, headers, body, other persisted fields | Canonical item stored in a collection; may be open in several tabs. |
| **Open tab** | tab label, in-memory draft, saved identity link, dirty/clean state | Editing surface; may diverge from disk after local edits or after a save elsewhere. |
| **Persisted version** | snapshot on disk at last successful save | Source of truth for what will be sent if the user reloads or overwrites without local edits. |
| **Stale-state notice** | which request changed, time/session context, offered actions | Informs the user that disk moved ahead of this tab’s adopted baseline. |
| **Collections sidebar** | tree of collections and requests | Reflects saved names and structure; reloads after saves today. |

Interaction overview:

1. User opens the same saved request in two or more isolated tabs.
2. User saves changes (for example a new URL) from tab A; persisted version updates.
3. Tab B (and any other matching tabs) receive a stale-state notice; tab labels update if
   the name changed.
4. If tab B is clean, user may load the latest saved version; if dirty, user chooses between
   keeping the draft or loading the saved version.
5. Collections sidebar shows the updated request after save, as today.

## Q&A

- **Q:** Why is this task needed if PYPOST-405 already delivered isolated tabs?  
  **A:** Isolation prevents unsaved cross-tab leakage, but users still need to know when the
  saved baseline changed. Without that, duplicate tabs create silent drift and overwrite risk.

- **Q:** Is full automatic sync of all metadata into every tab required?  
  **A:** The business need is **awareness and safe adoption**, not silent overwrite. Tabs may
  keep a local draft after notification; loading the latest saved version must be an explicit
  user action when edits exist.

- **Q:** Does rename-from-Collections already satisfy part of this task?  
  **A:** Yes for **tab titles** when renaming from the sidebar. This task also covers name
  changes via save and **non-name metadata** (URL, method, headers, body) where no notification
  exists today.

- **Q:** What if the user ignores the notice and saves from a stale tab?  
  **A:** The product should avoid silent clobbering of newer disk content—either by retaining
  existing overwrite confirmation patterns or an equivalent informed save path. Exact wording
  is a UX detail for later steps.

- **Q:** Should tabs reload automatically when they have no unsaved edits?  
  **A:** A one-step “load latest saved version” action should be offered; automatic reload
  without user confirmation is acceptable only if the tab is verified clean (no unsaved edits).
  If that distinction is ambiguous, prefer explicit user confirmation.

- **Q:** What about request deletion while multiple tabs are open?  
  **A:** Out of scope unless already handled elsewhere; this task focuses on **updates** to
  persisted content, not deletion flows.

- **Q:** Source of truth for scope?  
  **A:** Jira [PYPOST-408](https://pypost.atlassian.net/browse/PYPOST-408),
  `ai-tasks/PYPOST-405/60-review.md` (TD-3), and `doc/dev/open_request_in_isolated_tab.md`
  (limitations section).

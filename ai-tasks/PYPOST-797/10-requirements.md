# PYPOST-797: New tab (+) button does not open a new request tab

## Goals

PyPost users rely on the request tab bar to work on several HTTP requests in parallel. The
trailing **+** control is the primary visible affordance for opening another request tab
without leaving the current one. When that control does nothing, users cannot start a new
request from the tab bar and must fall back to less obvious paths or abandon multi-tab
workflows. This is a functional regression that blocks a core daily workflow and undermines
confidence in the tab bar after recent macOS layout fixes (PYPOST-792).

## User Stories

- As a PyPost user, I want to click the **+** control in the request tab bar to open a new
  empty request tab, so that I can draft or explore another request while keeping my current
  tab open.
- As a PyPost user on macOS, I want the **+** control to respond to a click the same way it
  did before the tab-bar layout work, so that navigation feels reliable and predictable.
- As a PyPost user, I want each new tab opened via **+** to become the active tab with a
  fresh, editable request, so that I can immediately enter a URL or edit the new request.
- As a PyPost user, I want existing request tabs (switch, close, titles) to keep working
  after this fix, so that correcting the **+** control does not break other tab-bar behavior.

## Definition of Done

- With at least one request tab open, clicking the **+** control in the request tab bar opens
  one new empty request tab.
- The newly opened tab is selected (active) and ready for editing.
- The **+** control remains the last item in the request tab bar after the new tab is added.
- Closing, switching, and labeling of existing request tabs behave as before the regression.
- Visual layout improvements from PYPOST-792 (readable tab labels, correctly sized close
  controls, separated **+** control) are preserved — no layout regressions.
- Verified on macOS using the reproduction steps from the Jira issue.
- Other supported platforms show no regressions in request tab-bar behavior.
- `make check` passes.

## Task Description

After PYPOST-792 restored native tab rendering and close-button metrics on macOS, the **+**
(new tab) control in the request tab bar no longer creates a tab when clicked.

**Steps to reproduce**

1. Launch PyPost on macOS.
2. Open at least one request tab.
3. Click the **+** button in the request tab bar.

**Expected:** A new empty request tab opens and becomes active.

**Actual:** Nothing happens — no new tab is created.

**Scope**

- In scope: restore **+** click behavior so it opens a new empty request tab; preserve
  PYPOST-792 tab-bar rendering; confirm no regressions to existing tab operations.
- Out of scope: redesigning the tab bar, changing what a "new" request contains beyond the
  current product default (empty/unnamed request), or altering unrelated UI regions.

**Constraints and assumptions**

- Implementation language: Python (existing PyPost desktop application).
- The defect was reported on macOS; acceptance must include macOS verification per the Jira
  reproduction steps.
- The **+** control is expected to behave consistently with the established product behavior
  for opening a new request tab (same outcome as the keyboard shortcut documented for users,
  if that path still works).
- PYPOST-792 is treated as the likely introduction point; the fix must not undo its visual
  corrections.

**Main entities (business perspective)**

| Entity | Role |
|--------|------|
| Request tab | An open HTTP request the user can edit and send; identified by a title in the tab bar. |
| Request tab bar | The strip of open request tabs plus the **+** control; primary navigation between requests. |
| New-tab control (**+**) | A persistent affordance at the end of the tab bar for creating another request tab. |
| Empty request | A new, unsaved request the user can configure (URL, method, body, etc.) in the new tab. |

## Q&A

- **Q**: Why fix this now (business reason)?
- **A**: Opening additional request tabs is a fundamental multi-request workflow. A dead **+**
  control blocks that workflow from the most visible entry point and signals that the tab bar
  is unreliable after a recent user-facing change.

- **Q**: Is only the **+** button in scope, or also the keyboard shortcut for a new tab?
- **A**: The Jira report targets the **+** button. The primary acceptance criterion is restoring
  **+** click behavior. If the keyboard shortcut still works, it must remain working; if it is
  also broken, fixing it is in scope only insofar as it shares the same "open new request tab"
  outcome — not as a separate feature change.

- **Q**: What should the new tab contain?
- **A**: The same default empty request the product already uses when a user opens a new tab
  through any supported path (no new fields, templates, or persistence rules).

- **Q**: Are sidebar tabs or request-editor sub-tabs (Params, Headers, etc.) in scope?
- **A**: No. PYPOST-792 addressed their layout; this task addresses only the functional
  failure of the request tab bar **+** control. Those regions serve as regression checks only.

- **Q**: Which platforms must be verified?
- **A**: macOS is mandatory per the report. Other supported platforms must not regress; spot
  verification on at least one non-macOS platform is recommended if feasible.

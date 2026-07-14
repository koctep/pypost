# PYPOST-792: macOS UI layout broken — overlapping tab labels and misaligned close buttons

## Goals

PyPost must look and behave like a polished, trustworthy tool on macOS. Today, three tab
regions render with overlapping or concatenated labels and oversized close controls, which
makes navigation hard, hides clickable targets, and makes the app appear broken to macOS
users from the first launch.

## User Stories

- As a PyPost user on macOS, I want the sidebar "Collections" and "History" tabs to be two
  clearly separated, readable labels, so that I can tell them apart and switch between them.
- As a PyPost user on macOS, I want each open request tab to show its title with a properly
  sized close button, so that I can read which request is open and close the intended tab
  without mis-clicks.
- As a PyPost user on macOS, I want the request editor sub-tabs (Params, Headers, Body,
  Script, MCP) to be distinct labels with normal spacing, so that I can find and click the
  section I need.

## Definition of Done

- Sidebar tabs render as two separate, readable labels ("Collections", "History") with
  visible spacing — never concatenated (e.g. `CollectionsHistory`).
- Request tab titles are fully readable; the close (`X`) control fits within the tab chrome
  and does not overlap the title text.
- Tab boundaries and spacing in the request tab bar are consistent; the new-tab (`+`)
  control is visually separated from adjacent tabs and clickable.
- Request editor sub-tabs (Params, Headers, Body, Script, MCP) render as five distinct
  labels with normal spacing and individually clickable hit targets — never one unbroken
  string (e.g. `ParamsHeadersBodyScriptMCP`).
- Verified on macOS in dark mode (the reported environment); light mode on macOS shows no
  equivalent defects.
- UI regions reported as unaffected (URL bar, Send button, response area) still render
  correctly — no regressions.
- Behavior on other supported platforms is unchanged.
- `make check` passes.

## Task Description

On macOS (dark mode), three PyPost UI regions render incorrectly, as confirmed by the
screenshot attached to the Jira issue (captured 2026-07-14):

1. **Sidebar navigation tabs** — the "Collections" and "History" labels overlap and read as
   a single string (`CollectionsHistory` / `Collections$History`).
2. **Request tab bar** — close (`X`) buttons are oversized and drawn on top of tab titles
   (e.g. over the word "test"), tab boundaries and spacing are inconsistent, and the
   new-tab (`+`) control is cramped against adjacent tabs.
3. **Request detail sub-tabs** — the section labels render without spacing or separators as
   one continuous label (`ParamsHeadersBodyScriptMCP`).

Steps to reproduce: launch PyPost on macOS, open at least one request (e.g. `GET test` from
a collection), and observe the three tab regions listed above.

The defect is macOS-specific per the report; the rest of the UI renders normally. The scope
of this task is limited to restoring correct rendering of the three affected tab regions —
no visual redesign, no new features, and no behavior changes on other platforms.

Implementation language: Python (existing PyPost desktop application).

## Q&A

- **Q**: Why fix this now (business reason)?
- **A**: The three affected regions are the primary navigation surfaces of the app. When
  labels are unreadable and close buttons cover titles, macOS users cannot navigate
  reliably and perceive the product as broken, which undermines trust in every release.
- **Q**: Is the fix limited to dark mode?
- **A**: Dark mode on macOS is the reported environment and must be verified explicitly,
  but the acceptance criteria require correct rendering on macOS regardless of theme and
  no regressions elsewhere.
- **Q**: Are other UI regions in scope?
- **A**: No. The URL bar, Send button, and response area render normally per the report and
  serve only as regression checks.

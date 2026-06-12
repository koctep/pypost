# PYPOST-64: history_panel setFixedHeight on detail fields

## Goals

Allow History panel detail-pane header and body fields to resize with the splitter and
respect font/DPI scaling instead of hard-coded pixel heights.

## User Stories

- As a user with larger fonts or high-DPI display, I want the history detail pane to
  show headers and body text without truncation when I drag the splitter.
- As a user browsing history, I want to allocate more vertical space to headers or body
  by resizing the list/detail split.

## Definition of Done

- `_detail_headers` and `_detail_body` no longer use `setFixedHeight`.
- Detail text fields expand within the lower splitter pane via size policies or layout
  stretch.
- Minimum heights scale with font metrics (not fixed 60/80 px).
- Existing History panel behaviour unchanged (filter, selection, load, copy, delete).
- Automated test verifies expanding vertical size policy on detail fields.

## Task Description

Follow-up from PYPOST-41 TD-7: detail `QTextEdit` widgets used fixed 60 px / 80 px
heights that ignore font size and prevent user resizing via the splitter.

## Q&A

- **Q:** Should minimum heights remain?  
  **A:** Yes — use font line spacing multiples so defaults stay readable without locking
  maximum size.

# PYPOST-845: Align plus_tab_placeholder to pypost_ prefix

## Goals

Trailing plus-tab chrome should use the same `pypost_` objectName prefix as
other automation identities for consistency.

## Programming Language

Python

## Definition of Done

- Placeholder widget objectName is `pypost_plus_tab_placeholder`.
- Constant lives in `widget_ids`; applied via `set_widget_id`.
- Unit test locks the name; docs list the id.

## Task Description

Rename historical `plus_tab_placeholder` (not a KEY catalog AC surface).

## Q&A

| Question | Answer |
| --- | --- |
| Add to KEY_WIDGET_IDS? | No — still chrome-only; document separately. |

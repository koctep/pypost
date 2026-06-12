# PYPOST-62: Technical Debt

## Blocker review

**SAFE TO CLOSE** — TD-5 from PYPOST-41 resolved; acceptance criteria met.

## Resolved

- Linear scan in `_selected_entry()` replaced with `_entries_by_id` dict rebuilt in
  `refresh()`.

## Remaining follow-ups

None for this task.

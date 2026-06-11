# PYPOST-106: Technical Debt Analysis

## Resolved

- **Manual font propagation loop** (PYPOST-12 / PYPOST-106): replaced with global QSS
  `font-size` + `QApplication.setFont`.

## Shortcuts Taken

- **Inline font-size in specific widgets** (`hotkeys_dialog`, `about_dialog`,
  `validation_controller`, `mcp_preview_edit`): not unified in this task. They may look
  disproportionate when user sets a very large app font.

## Missing Tests

- None for this change; regression coverage in `test_apply_settings_font.py` and
  `test_style_manager_font.py`.

## Follow-up Tasks

- Audit hardcoded `font-size` in widget-level QSS and align with global font scaling — optional
  UX polish, not a blocker.

## Verdict

**SAFE TO CLOSE** — no blockers.

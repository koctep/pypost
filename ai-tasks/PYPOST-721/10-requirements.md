# PYPOST-721: GUI tests for save and MCP overview dialogs

## Goals

Raise coverage for `save_dialog.py`, `mcp_activity_dialog.py`, and
`mcp_tools_overview_dialog.py` from below 20% to a level that protects against
regressions in dialog construction, validation, and table population logic.

## Definition of Done

- All three dialogs reach ≥90% coverage.
- Tests run offscreen per `doc/dev/gui_testing.md` conventions (no real display).
- Full test suite passes.

## Task Description

These three dialogs had no dedicated tests, meaning save validation logic
(collection creation vs. selection, empty-name guards) and MCP overview/activity
table population were unverified. Remediation: offscreen Qt tests using the
project's `qapp` fixture, constructing each dialog directly and asserting on
widget state.

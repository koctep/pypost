# PYPOST-1023: Define docs accuracy-drift checklist for UI label changes

## Programming Language

English Markdown for developer guide and process documentation.

## Goals

Follow-up from PYPOST-1015 (TD-4). When application code changes UI labels, defaults, hotkeys, or workflows, end-user documentation in `doc/user/` easily drifts out of date without clear developer ownership and an explicit verification checklist.

**Business goal:** Define an actionable Docs Accuracy-Drift Checklist in `doc/dev/user_guide.md` specifying triggers, ownership, UI-to-docs topic mapping, and a verification checklist including automated linting (`make lint-docs`, `make check-docs-links`).

## Definition of Done

- [ ] `doc/dev/user_guide.md` defines triggers and engineering ownership.
- [ ] Includes mapping from modified Qt/PySide UI components to `doc/user/` topic pages.
- [ ] Provides concrete verification steps (exact string matching, default checks, shortcut checks, `make lint-docs`, `make check-docs-links`).
- [ ] All relative links and anchors validate cleanly.

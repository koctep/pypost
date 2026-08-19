# PYPOST-1022: Add annotated screenshots/diagrams to User Guide interface/getting-started

## Programming Language

English Markdown for user documentation.

## Goals

Follow-up from PYPOST-1015 (TD-3). New users orienting in PyPost benefit from visual structural layout schematics of the main window in `doc/user/interface.md` and a first-run sequence flow in `doc/user/getting-started.md`.

**Business goal:** Provide clear, lightweight layout diagrams and first-run flow schematics in `doc/user/interface.md` and `doc/user/getting-started.md` while adhering to line length <= 100 and Markdown quality standards.

## Definition of Done

- [ ] `doc/user/interface.md` includes an overview layout diagram mapping the Menu Bar, Environment bar, Sidebar, Workspace tabs, and Response pane.
- [ ] `doc/user/getting-started.md` includes a first-run workflow diagram.
- [ ] All linters (`make lint-docs`, `make check-docs-links`) pass cleanly.

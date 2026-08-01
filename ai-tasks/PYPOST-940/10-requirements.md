# PYPOST-940: Harden fixture teardown for Qt item views

## Goals

Agent UI action tests create isolated Qt item views (tree, list view) with
attached models. Without consistent teardown, Qt can emit destructor warnings
or destabilize later tests that start a full agent session. This task ensures
test harnesses share one safe teardown pattern so the suite stays reliable.

## User Stories

- As a test author, I want a shared helper to detach models from item views
  before closing fixtures, so I do not duplicate fragile teardown logic.
- As a CI maintainer, I want ui_select fixture tests to run without Qt
  teardown warnings, so failures are easier to diagnose.

## Definition of Done

- A shared test helper detaches models from model-backed item views before
  fixture close.
- Tree and list-view fixtures in ui_select tests use the shared helper.
- ui_select tests pass with no Qt teardown warnings related to item views.

## Task Description

Follow-up from PYPOST-916 TD-2: tree fixtures already call `setModel(None)`
locally; list-view fixtures added the same pattern in PYPOST-939. Consolidate
into one helper under `tests/helpers/` and route existing item-view fixtures
through it.

## Q&A

- **Why not fix production code?** Teardown is a test-harness concern only;
  agent UI actions do not own widget lifecycle in tests.
- **Scope?** Shared helper + ui_select fixture adoption; no new product APIs.

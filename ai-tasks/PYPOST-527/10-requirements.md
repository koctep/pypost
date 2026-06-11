# PYPOST-527: Settings UI verify and re-encrypt actions for encryption migration

## Goals

PYPOST-487 delivered `EncryptionMigrationService` and a headless CLI so operators can verify
decrypt access and bulk re-encrypt stored environments during key-source or rotation rollouts.
Desktop users who configure encryption in Settings still had to run the CLI for verify and
re-encrypt — an optional architecture item (PYPOST-487 TD-3) deferred to this task.

This task adds Settings actions that delegate to the same migration service the CLI uses, with
confirmation before destructive re-encrypt, so operators can complete common migration steps
without leaving the application.

## Programming Language

Python 3.10+

## User Stories

- As an operator who enabled encryption or changed key source in Settings, I want to verify that
  all stored hidden values decrypt with the current configuration before I rely on the app in
  production.
- As an operator after key rotation, I want to bulk re-encrypt all environments under the active
  key from Settings, with a clear warning and backup, matching CLI safety properties.
- As a maintainer, I want Settings migration actions to call `EncryptionMigrationService` only —
  no duplicate migration logic in the UI layer.
- As a desktop user who does not use encryption migration, I want Settings to look and behave as
  before except for two optional actions grouped under encryption settings.

## Definition of Done

- Settings dialog exposes **Verify encryption** and **Re-encrypt all environments** actions.
- Actions use encryption-related fields from the current Settings form (including unsaved changes)
  and delegate to `EncryptionMigrationService` with the application `StorageManager`.
- Re-encrypt requires explicit confirmation before any write; verify is read-only.
- Success and failure outcomes are shown to the operator in a dialog with inventory summary and
  errors when present.
- Automated tests cover button presence, disabled state without storage, service delegation, and
  confirmation gating for re-encrypt.
- Developer documentation notes the Settings UI as an operator surface alongside the CLI.

## Task Description

Source: [PYPOST-487 technical debt TD-3](ai-tasks/PYPOST-487/60-tech-debt.md). Jira:
[PYPOST-527](https://pypost.atlassian.net/browse/PYPOST-527).

### In Scope

- Settings UI buttons/actions for verify and bulk re-encrypt.
- Confirmation dialog before destructive re-encrypt.
- Result presentation (information/warning message box).
- `MainWindow.open_settings` passes storage into Settings.
- Tests and dev docs update.

### Out of Scope

- `encrypt-plaintext` action in Settings (CLI remains; can be a follow-up).
- Dry-run re-encrypt from UI.
- Progress UI for long-running re-encrypt.
- Changes to migration service, storage contracts, or envelope format.
- Other PYPOST-487 follow-ups (CLI `--json`, inventory data-quality flags, no-op skip).

### Constraints and Assumptions

- Migration uses the same on-disk `environments.json` as the running app; operator should avoid
  concurrent edits during re-encrypt (same as CLI).
- Encryption policy for verify/re-encrypt reflects the Settings form at click time, not
  necessarily saved settings — operators may verify before saving new key source.
- Re-encrypt creates a timestamped backup by default (service `backup=True`).

## Functional Requirements

- Settings must offer verify and bulk re-encrypt actions when opened from the main window with
  storage available.
- Verify must call `verify_decrypt_access` and display the report without writing environments.
- Re-encrypt must show a confirmation dialog; on confirm, call `bulk_re_encrypt` with backup
  enabled.
- Actions must be disabled or unavailable when storage is not provided (e.g. isolated dialog tests).
- Outcomes must not expose key material; error text matches migration service operator messages.

## Non-functional Requirements

- **Safety**: re-encrypt must not proceed without confirmation; failed operations leave prior
  on-disk data recoverable (service atomic save + backup).
- **Consistency**: UI outcomes align with CLI verify/re-encrypt for the same settings and data.
- **Maintainability**: UI contains presentation and wiring only; migration logic stays in
  `EncryptionMigrationService`.

## Stakeholder Approval

Approved via sprint-task-runner autonomous mode (2026-06-11).

## Q&A

| Question | Answer |
| --- | --- |
| Why form settings instead of saved config? | Operators often change key source in Settings then want to verify before Save. Form values match their intent. |
| Why not add encrypt-plaintext? | PYPOST-527 scope is verify + re-encrypt per TD-3; encrypt-plaintext can follow if needed. |
| Why disable buttons without storage? | Keeps unit tests simple; production path always passes storage from MainWindow. |

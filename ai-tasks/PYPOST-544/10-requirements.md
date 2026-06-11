# PYPOST-544: Settings UI reencrypt_stats in migration dialog

## Goals

PYPOST-535 added `reencrypt_stats` (encrypted vs reused counts) to the migration CLI so operators
can audit bulk re-encrypt runs. Settings already exposes **Re-encrypt all environments** but the
result dialog omitted those counts, forcing desktop users to run the CLI for the same audit trail.

This task closes that gap so Settings and CLI present equivalent rewrite outcome detail.

## Programming Language

Python 3.10+

## User Stories

- As an operator who re-encrypts from Settings after key rotation, I want to see how many hidden
  values were re-encrypted versus reused so I can confirm the batch did meaningful work.
- As a maintainer, I want Settings result text to reflect `MigrationReport.reencrypt_stats` without
  duplicating migration logic in the UI layer.

## Definition of Done

- Settings re-encrypt success/failure dialog includes re-encrypted and reused counts when
  `MigrationReport.reencrypt_stats` is present.
- Verify dialog unchanged (verify reports have no rewrite stats).
- Automated test asserts stats appear in the information dialog body after confirmed re-encrypt.
- Developer documentation notes Settings parity with CLI stats.
- Existing encryption migration tests pass.

## Task Description

Source: [PYPOST-535 technical debt TD-1](ai-tasks/PYPOST-535/60-tech-debt.md). Jira:
[PYPOST-544](https://pypost.atlassian.net/browse/PYPOST-544).

### In Scope

- Extend `_format_migration_report` in Settings dialog.
- Unit test for stats in dialog body.
- Dev docs update for Settings operator surface.

### Out of Scope

- New migration service behavior or storage changes.
- Dry-run projected stats (PYPOST-545).
- `encrypt-plaintext` or `upgrade-v2` actions in Settings.

## Functional Requirements

- When `bulk_re_encrypt` returns a report with `reencrypt_stats`, the result dialog must show
  both counts in human-readable form.
- When `reencrypt_stats` is absent (e.g. verify), the dialog must not show empty or placeholder
  stat lines.

## Non-functional Requirements

- **Consistency**: Count labels align semantically with CLI `reencrypt_stats` fields.
- **Maintainability**: Presentation-only change in Settings; no new service APIs.

## Stakeholder Approval

Approved via autonomous sprint-task-runner mode (2026-06-11).

## Q&A

| Question | Answer |
| --- | --- |
| Why not share formatting with CLI? | CLI and Settings already use different label casing; a small UI formatter keeps scope minimal. |
| Should verify show stats? | No — verify is read-only and never populates `reencrypt_stats`. |

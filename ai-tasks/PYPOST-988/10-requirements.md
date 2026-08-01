# PYPOST-988: Export environments

## Programming language

Python

## Goals

PyPost can import environments from JSON (PYPOST-986), but users still had no in-app way
to produce those files. Export closes the loop: save selected or all environments to a
file compatible with import, for backup, sharing, or moving setups between machines.

## User Stories

- As a **user**, I want to export one or all environments to a file from Manage
  Environments, so I can back up or share my configuration without copying
  `environments.json` manually.
- As a **user**, I want the exported file to work with **Import…**, so export and import
  round-trip on my installation.
- As a **user**, I want to be warned before exporting Hidden secrets, so I know the file
  may contain sensitive values.
- As a **user**, I want clear success or error feedback after export.

## Definition of Done

- [x] **Export…** action in Manage Environments (near Import).
- [x] Scope choice: selected environment and/or all environments.
- [x] Save dialog; native PyPost JSON format (single object or list).
- [x] Hidden policy documented: include values with confirmation warning (not redacted).
- [x] Success/error feedback; automated tests; `doc/user/environments.md` updated.

## Scope (in)

- Export selected and/or all environments from the environment list UI.
- Native JSON format matching import (PYPOST-986).
- Warning when export includes Hidden variables.
- Tests and user documentation.

## Scope (out)

- Postman or third-party exporters.
- Import (already shipped).
- Collections export/import.

## Q&A

**Q:** Hidden/encrypted secrets — include or redact?

**A:** **Include** full values in native serialization, with a mandatory confirmation when
any exported environment has Hidden variables. Redaction would break round-trip import.
When encryption at rest is enabled, Hidden values are written as encrypted envelopes (same
as `environments.json`); when off, as plaintext strings. Document both cases for users.

**Q:** Single vs multiple environments file shape?

**A:** One environment → single JSON object; multiple → JSON list. Import already accepts
both (PYPOST-986).

## Worklog

tokens_used: 8000
role: execution
step: 1
step_name: Requirements

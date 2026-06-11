# PYPOST-486: Keep the desktop UI responsive during encrypted environment load and save

## Goals

Environment encryption at rest (PYPOST-447) protects hidden secret values on disk. When users
have many environments or many hidden keys, routine actions such as startup, saving environment
changes, or reloading after collection updates can freeze the application window noticeably.
This task ensures users can work with encrypted environment data without disruptive UI pauses
while keeping persistence safe and failures visible.

## Programming Language

Python 3.10+

## User Stories

- As a desktop user with encryption enabled, I want the application to stay responsive while
  environments load at startup so I can begin working without a frozen window.
- As a user managing many environments, I want saving environment changes without visible UI
  stalls so editing secrets and variables feels smooth.
- As a user who relies on encrypted storage, I want load/save failures to be reported clearly
  so I know when data was not persisted or could not be decrypted.
- As an operator monitoring the app, I want encryption activity and errors to remain observable
  so performance regressions and key problems are diagnosable after this change.

## Definition of Done

- Environment load with encryption enabled does not produce a visible UI freeze for
  large-environment scenarios (see Assumptions).
- Environment save with encryption enabled does not produce a visible UI freeze for
  large-environment scenarios.
- Persisted environment data remains intact: failed saves do not leave corrupt or partial files
  on disk.
- After a successful save, users retain a complete, usable `environments.json`; a failed save
  leaves the previous file unchanged.
- Encryption and decryption errors continue to surface to the user through existing application
  error paths.
- Encryption-related metrics and structured logs remain accurate for save, load, success, and
  failure cases.
- Automated tests verify responsiveness expectations and that persistence and error semantics
  are unchanged for representative large-environment scenarios.

## Task Description

Source: [PYPOST-447 technical debt — Performance Concerns](
https://pypost.atlassian.net/browse/PYPOST-447). Encryption and decryption are part of the
environment storage load/save path invoked from the desktop UI (startup, environment manager
save, variable updates, collection-driven reload). With large encrypted datasets, that work can
block the UI long enough for users to perceive a frozen window.

The business need is responsive desktop use with encryption enabled. Implementation must not
trade away safe persistence, clear failure reporting, or operational visibility.

### In Scope

- Responsive environment load when encrypted values must be decrypted.
- Responsive environment save when hidden values must be encrypted.
- Preserving safe persistence guarantees for `environments.json` (no partial or corrupt files
  after failed saves; complete replacement after successful saves).
- Preserving user-visible error reporting for encrypt/decrypt and unsupported-format failures.
- Preserving encryption observability (counters, structured logs, error labels).
- Verification with large-environment scenarios representative of the reported problem.

### Out of Scope

- Reducing how many values are encrypted per save (tracked separately as PYPOST-485).
- Changing encryption policy, key sources, or envelope format.
- New user-facing encryption settings or UI redesign.
- Extracting storage into a separate adapter service (PYPOST-482).
- Performance work unrelated to environment encryption load/save.

## Functional Requirements

- The application must load encrypted environment data without a visible UI freeze during
  large-environment scenarios.
- The application must save encrypted environment data without a visible UI freeze during
  large-environment scenarios.
- A failed save must not publish a partial or corrupted `environments.json` to users.
- After a successful save, the persisted file must be complete and usable; after a failed save,
  the previous file must remain unchanged.
- When encryption or decryption fails, the user must receive the same class of actionable
  feedback as today (missing key, corrupt payload, unsupported format).
- When encryption is disabled, load/save behavior must remain unchanged.
- When encryption is enabled, only hidden-key values must be encrypted on save and decrypted
  on load, matching current policy.

## Non-functional Requirements

- **Responsiveness**: routine environment load/save with encryption must not produce visible UI
  freezes for large-environment scenarios.
- **Reliability**: persistence must remain crash-safe; no regression in data integrity on failure
  paths.
- **Observability**: encryption/decryption counters, error labels, and structured log events
  must remain complete and accurate.
- **Backward compatibility**: existing plain-text and encrypted environment files must continue
  to load without migration.
- **Security**: decrypted secrets must remain in memory only for runtime use; responsiveness
  improvements must not broaden secret exposure surfaces.

## Constraints and Assumptions

- Encryption at rest from PYPOST-447 and settings-driven policy from PYPOST-481 remain the
  baseline behavior.
- Safe persistence guarantees for `environments.json` remain unchanged: failed saves must not
  leave partial or corrupt files; successful saves must yield a complete, usable file.
- Load/save is triggered from desktop flows including app startup, environment manager close,
  per-variable saves, and collection-change reloads.
- **Large-environment scenario**: many environments and/or many hidden keys sufficient to
  reproduce noticeable UI freezes in the current application.
- **Responsiveness acceptance**: for large-environment scenarios, routine load and save during
  startup, environment manager save, variable updates, and collection-driven reload must not
  produce a visible UI freeze — the window must remain responsive to user input without a
  perceptible stall.
- Python 3.10+ and project documentation line-length rules apply to artifacts.

## Main Entities and Interactions

- **Desktop user**: edits environments and expects a responsive application window.
- **Application UI**: initiates environment load and save during normal workflows.
- **Environment storage**: persists and restores environment definitions, including encrypted
  hidden values.
- **Encrypted environment value**: a hidden-key entry stored in encrypted form on disk and
  restored to plain text in memory after load.
- **Encryption operation**: transforms hidden values during save (encrypt) and load (decrypt).
- **Observability signals**: metrics and logs that record encryption activity and failures.

Interaction overview:

1. User opens the app or changes environments; the UI requests load or save of environment
   data.
2. Storage applies encryption policy to hidden keys during save and reverses it during load.
3. Persistence completes with a usable file or fails without damaging the prior file.
4. Failures are reported to the user; successes update in-memory state and observability
   signals.

## Q&A

- Q: The source issue is framed as synchronous encryption in the storage flow (and follow-up
  work may mention async approaches). Why reframe this as UI responsiveness?
  A: The technical framing describes where encryption work runs today, not the user outcome.
  Requirements discovery confirmed the business need: desktop users with encryption enabled must
  not experience frozen windows during startup, save, or reload. How responsiveness is achieved
  belongs in architecture, not requirements.
- Q: Why address this separately from PYPOST-485 (per-value encryption overhead)?
  A: PYPOST-485 targets how much work encryption does per save; PYPOST-486 targets visible UI
  freezes during load/save when that work runs on UI-driven paths.
- Q: What does safe persistence mean for users?
  A: Users never see a half-written `environments.json`; either the previous file remains or a
  complete, usable file replaces it after a successful save.
- Q: Must error behavior change to improve responsiveness?
  A: No. Users must still see clear failures when keys are missing or payloads are invalid;
  observability must remain intact for operators.
- Q: Does this task change who can read secrets on disk?
  A: No. The goal is responsiveness; encryption-at-rest protection and in-memory-only runtime
  use remain unchanged.

# PYPOST-1009: Encrypted-at-rest export round-trip

## Goals

Users who turn on encryption at rest expect Export to write Hidden values as
protected envelopes (the same kind of protection as local environment storage),
and they expect Import on **this same installation** to restore those
environments without losing names, variables, Hidden flags, or secret plaintext.

Today a pure export → import round-trip is locked only with encryption **off**.
That proof does not show that an encrypted export file actually contains
envelopes, or that the same machine can import it back when encryption is on.
A future change could write plaintext secrets into an "encrypted" export, or
produce a file this installation cannot import, and CI would still pass.

This task adds that missing proof: export with encryption enabled → inspect the
on-disk file for envelopes → re-import on the same machine with the same key →
data is intact. The business goal is confidence that encrypted backups remain
usable on the installation that created them, without exposing Hidden values as
plain strings in the file.

**Implementation language**: Python (verification/testing debt within the
existing Python codebase; no new language or stack is introduced).

## User Stories

- As a user with encryption at rest enabled, I want an exported environment file
  to store Hidden values as encrypted envelopes (not plaintext), so a copy of
  the file does not reveal those secrets the way a plaintext export would.
- As a user on the same machine that created the export, I want Import to
  restore the exported environments without data loss, so an encrypted backup
  is actually restorable when my key is still available.
- As a developer changing export, import, or at-rest protection, I want an
  automated integration test that fails if either the on-disk envelope or the
  same-machine re-import breaks, so regressions are caught in CI rather than
  by a user who cannot restore a backup.
- As a maintainer, I want this lock to use a temporary local key and
  encryption-enabled settings, so the suite exercises the real protected path
  without live key services.

## Definition of Done

- An automated integration test enables encryption at rest with a temporary
  local key, exports at least one environment that has Hidden values, and
  writes a real file.
- The on-disk file shows the encryption envelope for those Hidden values: they
  are not stored as the original secret strings. Non-Hidden values remain
  readable plaintext in the file (product rule: only Hidden values are
  protected at rest).
- Re-import of that file on the **same** installation (encryption still on,
  same key) succeeds with no parse/decrypt failures and restores environment
  name, variables (including Hidden plaintext after protection is lifted), and
  Hidden flags.
- The path is realistic: write file → inspect file → import from that file.
  In-memory-only payload checks, or a round-trip with encryption off, do not
  satisfy this ticket.
- The test runs under `make test` with an explicit pytest timeout per project
  testing rules.
- No user-visible Export/Import or encryption behavior change is required when
  current product behavior is already correct; if the new assertions fail
  against current code, that is a real defect and is fixed as part of this
  task.
- Sibling verification debt remains out of scope (presenter export wiring,
  shared JSON-root helper, Export button click).

## Task Description

PYPOST-988 shipped environment Export and a pure round-trip with encryption
off. User docs already promise that with encryption on, Hidden values are
written as envelopes and import correctly on this installation. That promise
is not locked by CI.

This ticket closes follow-up #2 from `ai-tasks/PYPOST-988/60-tech-debt.md`:
prove encrypted-at-rest export → file envelope → same-machine import.

### Scope (in)

- Automated proof of export with encryption enabled, using a temporary local
  key (the existing encryption-at-rest enablement path, including
  `PYPOST_ENV_ENCRYPTION_ENABLED` plus a temp key).
- Inspection of the written file: Hidden values have envelope shape; secret
  plaintext is absent from those fields.
- Successful re-import on the same machine with the same key, with no data
  loss for the exported environment(s).
- Preservation of existing encryption-off round-trip coverage.

### Scope (out)

- Changing Export UX, Hidden-secrets confirmation, file format, or
  single-vs-list JSON root shaping.
- Cross-machine import with a **different** key (documented to fail per entry;
  not this ticket's happy path).
- Full UI click of **Export…** (separate PYPOST-988 debt).
- Presenter → dialog export-serializer wiring (PYPOST-1008).
- Shared single-vs-list JSON helper (PYPOST-1010).
- Changing encryption settings UX, key sources, or at-rest algorithms.
- Collection export/import, third-party formats, or new production APIs.

### Constraints and assumptions

- Product behavior is already believed correct; this is verification debt
  unless a new assertion reveals a defect.
- Programming language: Python (existing PyPost desktop app).
- Source: follow-up #2 in `ai-tasks/PYPOST-988/60-tech-debt.md`, ticketed as
  [PYPOST-1009](https://pypost.atlassian.net/browse/PYPOST-1009).
  Parent: [PYPOST-988](https://pypost.atlassian.net/browse/PYPOST-988).
- "Same machine" means the same encryption-enabled installation and key that
  wrote the file — not a second key or a disabled-encryption import.
- A realistic path means an actual export file and the product import path,
  not a full GUI click tour.
- Approval for Step 1 artifacts is treated as granted under
  sprint-task-runner autonomy.

## Non-Functional Requirements

- The test must be hermetic: no network, no live keyring or secret-store
  services; temporary local key only.
- Must not make the suite flaky or unbounded (explicit timeout; no real
  modal dialogs required).
- Security: the test must fail if Hidden values appear as plaintext in the
  export file while encryption is enabled.
- Fast and focused: one encrypted round-trip scenario is enough; list-shape
  and encryption-off paths are already covered elsewhere.

## Main Entities

- **Environment** — named set of variables; some may be Hidden.
- **Hidden value** — secret variable that encryption at rest must protect in
  the export file.
- **Encryption envelope** — the on-disk protected form of a Hidden value when
  encryption at rest is on (same kind of protection as local environment
  storage).
- **Export file** — the JSON file Export writes; must carry envelopes for
  Hidden values when encryption is on.
- **Same-machine import** — Import on the installation that still has the
  key that produced the envelopes; must restore the environment intact.

## User scenarios

1. Encryption at rest is on. The user exports an environment that includes
   Hidden values. The saved file contains envelopes for those values, not
   the secret strings.
2. On the same installation, the user imports that file. The environment
   comes back with the same name, variables, Hidden flags, and secret
   plaintext.
3. A regression writes plaintext Hidden values into an encrypted export, or
   produces a file this installation cannot import. The new test fails and
   CI blocks merge.

## Q&A

**Q:** Why is this a business/quality goal, not "just more coverage"?

**A:** Encrypted export is a credential backup. Users need two guarantees:
the file does not leave Hidden values in the clear, and they can restore it
on the machine that still has the key. The existing round-trip never turns
encryption on, so neither guarantee is locked.

**Q:** Must product behavior change?

**A:** Only if the new assertions reveal a defect. The expected happy path is
test-only when current export/import already honor encryption at rest.

**Q:** Why not treat the existing `test_write_export_file_round_trips_through_import`
as enough?

**A:** That test explicitly leaves encryption disabled. It cannot see envelope
shape or same-machine decrypt-on-import.

**Q:** Is a full UI click path required?

**A:** No. PYPOST-988 listed UI click coverage as separate missing tests. This
follow-up is the encrypted file round-trip through a realistic
export-file → import path. Click-level Export remains out of scope.

**Q:** What does "envelope shape in the file" mean in business terms?

**A:** Hidden values in the written file must appear as encrypted-at-rest
envelopes (recognizably protected, not the original secret string), matching
what users already see in local environment storage when encryption is on.
Exact field layout is a later-step concern.

**Q:** Is import on a different machine / different key in scope?

**A:** No. That failure is already documented for users. This ticket locks
the successful same-installation restore.

**Q:** How does this relate to PYPOST-1008 and PYPOST-1010?

**A:** PYPOST-1008 locks presenter export wiring with plaintext fakes.
PYPOST-1010 is a shared JSON-root helper. This ticket only locks encrypted
export → file envelope → same-machine import.

# PYPOST-999: Test import Overwrite × Hidden protection round-trip

## Goals

When a user **overwrites** an existing environment by importing a file that
shares its name, PyPost keeps that environment’s identity so that selection and
at-rest protection continue to work as they did before the import. After such an
overwrite is saved, Hidden (secret) values that did **not** change must keep the
same durable protected form, while Hidden values that **did** change must receive
fresh protection under the installation’s current encryption setting and reload
to the new plaintext.

Today, unchanged-vs-changed Hidden protection on save is covered in isolation,
and Overwrite import is covered for identity preservation — but **no automated
test exercises the combination**: Overwrite import → save → reload. Maintainers
currently rely on inspection rather than CI to trust that this interaction stays
correct when either subsystem changes (for example, how protection is versioned
or how unchanged secrets are recognized across save).

This task closes that verification gap so a regression cannot silently break
“unchanged Hidden keeps the same durable protected form; changed Hidden gets
fresh protection and correct reload” after an Overwrite import.

**Implementation language**: Python (test-focused debt in the existing Python
codebase; no new language or stack).

## User Stories

- As a **user** who overwrites an environment via import and then saves, I want
  Hidden values I did not change to stay correctly protected at rest (same
  durable protected form, no accidental plaintext or wrong protection), so that
  import does not weaken secrets that were already safe.
- As a **user** who overwrites an environment via import with a new secret
  value, I want that changed Hidden value to be freshly protected under my
  current encryption setting and to reload as the new plaintext, so that the
  old stored form of a superseded secret is not left behind as if nothing
  changed.
- As a **maintainer**, I want an automated test under `make test` that locks
  the Overwrite-import → save → reload contract for both unchanged and changed
  Hidden values, so that future changes to import identity rules or secret
  protection on save cannot ship without CI catching a break.
- As a **maintainer**, I want this coverage to prefer a test-only change, so
  we do not churn production code unless the new assertions reveal a real bug.

## Definition of Done

- An automated test exercises: plan an Overwrite import against an existing
  environment that already has encrypted Hidden values at rest → persist →
  reload (or otherwise inspect durable storage after save).
- For at least one Hidden value whose plaintext is **unchanged** by the
  Overwrite import, the test proves the durable protected form is the **same**
  as before the import (not freshly rewritten for the same plaintext).
- For at least one Hidden value whose plaintext **changed** in the Overwrite
  import, the test proves the durable protected form is **new** (not the
  previous form for the old value), and a reload yields the new plaintext.
- The preserved environment identity across Overwrite remains part of the
  scenario (the same environment the user already had, not a silently new
  identity), consistent with the product rule that Overwrite keeps selection
  and protection continuity.
- The test runs under `make test` with an explicit per-test/module timeout per
  project testing rules, and passes against correct behavior.
- Prefer test-only change; production code only if the new test reveals a real
  defect.
- No change to user-facing import UX, conflict choices, or encryption settings
  is required for this debt unless a bug is found.

## Task Description

**Problem:** Import Overwrite was designed to preserve the existing
environment’s identity so that ongoing selection and at-rest secret handling
stay continuous. Separately, PyPost already keeps the same durable protected
form for Hidden values whose plaintext has not changed when saving. The
interaction of those two behaviors after Overwrite import is believed correct
by inspection, but CI does not prove it. A future change to either path could
break “unchanged secret keeps the same durable protected form; changed secret
gets fresh protection” without failing today’s import or save-protection tests
alone.

**Goal:** Add automated verification that after an Overwrite import is planned
and saved (with encryption enabled), durable storage and a subsequent reload
show the correct outcomes for unchanged and changed Hidden values on the
preserved environment identity: same durable protected form when unchanged;
fresh protection plus correct reload when changed. CI locks that combination.

**Scope (in):**

- Automated round-trip coverage for Overwrite import + save + reload (or
  equivalent durable inspection) with encryption enabled.
- Assertions covering both an unchanged Hidden value (same durable protected
  form) and a changed Hidden value (fresh protection and correct reload).
- Documentation of the product expectation in the test (and a short
  `doc/dev` note in Step 8 if the project’s import/encryption testing tables
  warrant it).

**Scope (out):**

- Changing Overwrite conflict UX or adding new conflict decisions.
- Changing the general unchanged-secret protection policy for non-import saves
  (already covered elsewhere).
- UI click-level Import button tests, presenter wiring tests, or other
  PYPOST-986 follow-ups (tracked separately).
- Third-party import formats, collection import, or export features.

**Constraints and assumptions:**

- Programming language: Python.
- Source: [PYPOST-986](https://pypost.atlassian.net/browse/PYPOST-986)
  tech-debt follow-up 1
  (`ai-tasks/PYPOST-986/60-tech-debt.md`).
- Behavior under test is expected to already be correct; this is primarily
  verification debt. Production fixes are in scope only if the new assertions
  fail against current code.
- Encryption must be exercised with a local test key / fixture — no live
  external key services.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Environment | Named profile the user overwrites by import |
| Environment identity | Same environment across Overwrite (selection + protection) |
| Hidden value | Secret variable that must stay protected at rest |
| Unchanged secret | Hidden value with same plaintext before and after Overwrite |
| Changed secret | Hidden value whose plaintext differs after Overwrite |
| Overwrite import | Replaces contents while keeping environment identity |
| Persist / reload | Save after import; read durable state to verify protection |

Interaction: user (or test) has an encrypted environment → Overwrite import
updates its variables → save → durable storage shows the same protected form for
unchanged secrets and fresh protection for changed secrets → reload returns
correct plaintexts. Overwrite keeps identity; CI locks the combo.

## Non-Functional Requirements

- **Security**: the test must never assert or accept a path that leaves a
  Hidden value as durable plaintext when encryption is enabled; changed
  secrets must not keep a superseded protected form as if still current.
- **Determinism**: no network or live external crypto services; local
  encryption fixtures only.
- **CI speed**: single focused scenario; no large-environment performance
  benchmark (those exist elsewhere).
- **Clarity**: the test documents why Overwrite identity + same-form protection
  for unchanged secrets matter together so future maintainers do not “simplify”
  either side without CI feedback.

## Q&A

**Why is this a Debt / testing story?**
PYPOST-986 shipped Overwrite import with identity preservation intended to
cooperate with same-form protection for unchanged secrets on save; only the
combination lacks a locking test.

**Why not rely on existing save-protection tests alone?**
Those tests do not go through Overwrite import planning; import tests do not
assert same durable protected form vs fresh protection after save.

**Why Overwrite specifically?**
Overwrite keeps the existing environment identity; that is the path where
unchanged secrets continue to match prior durable protection. Keep Both /
Skip do not create this identity-preserving update interaction.

**Production changes expected?**
No, unless the new test fails against current behavior.

**Relation to other PYPOST-986 follow-ups?**
Sibling debts cover presenter wiring and Import button clicks; this ticket is
only the encryption round-trip after Overwrite.

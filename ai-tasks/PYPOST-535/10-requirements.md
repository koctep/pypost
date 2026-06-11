# PYPOST-535: Migration CLI reuse stats for kid rotation

## Goals

After PYPOST-485 introduced selective re-encrypt on environment save, operators running bulk
`re-encrypt` during key rotation cannot see how many hidden values were rewritten versus reused
from the migration CLI. Surfacing these counts makes rotation runs auditable and confirms the
batch job did meaningful work.

## Programming Language

Python 3.10+

## User Stories

- As an operator running `encryption_migrate re-encrypt` after key rotation, I want reuse and
  re-encrypt counts in CLI output so I can confirm how many envelopes were updated.
- As a CI maintainer using `--json`, I want structured `reencrypt_stats` fields to assert on
  migration efficiency.
- As a security reviewer, I want kid rotation to re-encrypt envelopes that still reference a
  historical `kid`, not silently reuse stale ciphertext.

## Definition of Done

- `re-encrypt` and `encrypt-plaintext` reports include `encrypted_count` and `reused_count` in
  human and `--json` output when a rewrite completes (including no-op skip when already on active
  kid).
- Envelope reuse during save requires matching active `kid` so bulk rotation rewrites historical
  envelopes.
- Tests cover CLI/JSON output and kid-aware reuse.
- Developer documentation updated.

## Out of Scope

- Settings UI migration dialog changes.
- New Prometheus counters (reuse remains log-only per PYPOST-485).
- Dry-run projected reuse counts.

## Acceptance Criteria

1. After `re-encrypt` with mixed historical/active kids, output shows non-zero `encrypted_count`
   for values that required a new envelope.
2. When all hidden values already use the active `kid`, migration reports `reused_count` equal to
   hidden value count and `encrypted_count` 0 without writing.
3. `--json` includes `reencrypt_stats` object on rewrite commands.
4. Existing encryption migration tests pass.

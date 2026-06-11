# PYPOST-529: Technical Debt Analysis

## Shortcuts Taken

- **Invalid-shape detection is scan-only** — Does not attempt deserialize of invalid values;
  operators must fix JSON manually.
- **Empty `kid` in envelopes** — Still counted as encrypted envelope, not data-quality error
  (separate follow-up).

## Code Quality Issues

- None blocking close.

## Missing Tests

- CLI human-mode output for `invalid_hidden` line — covered indirectly via service tests.
- `encrypt_plaintext_hidden` abort on invalid hidden — same rewrite path as `bulk_re_encrypt`;
  one rewrite abort test sufficient.

## Performance Concerns

- Negligible: one extra branch per hidden key during scan.

## Architecture Deviations

None. Extends existing `EnvironmentInventory` and scan path.

## Follow-up Tasks

No new follow-ups. Resolves PYPOST-487 TD-6.

## Review

No blockers. **SAFE TO CLOSE.**

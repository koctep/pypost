# PYPOST-529: Flag non-string/non-envelope hidden values in migration inventory

## Goals

PYPOST-487 migration inventory scans `environments.json` for hidden variable shapes. Values that
are neither encrypted envelopes nor plaintext strings are counted in `hidden_value_count` but not
classified — operators see inconsistent totals and get no warning about corrupt on-disk data.

This task surfaces those values as explicit data-quality errors so verify and report commands fail
closed with actionable messages.

## Programming Language

Python 3.10+

## User Stories

- As an operator running **Verify encryption**, I want invalid hidden value shapes reported so I
  can fix `environments.json` before rotation or re-encryption.
- As an operator running **report**, I want inventory output to list data-quality problems
  alongside kid and plaintext counts.
- As a maintainer, I want migration rewrite operations to abort when invalid hidden shapes exist,
  matching the fail-closed behavior for missing keys and decrypt errors.

## Definition of Done

- Scan classifies each non-null hidden value as envelope, plaintext string, or invalid.
- Invalid values appear in `EnvironmentInventory` with operator-readable error messages.
- `verify_decrypt_access`, `bulk_re_encrypt`, and `encrypt_plaintext_hidden` return `success=False`
  when data-quality errors exist.
- Automated tests cover at least one non-string and one malformed-dict case.
- Developer documentation describes the new inventory fields.

## Out of Scope

- Empty `kid` inside valid envelopes (separate follow-up).
- Auto-repair or coercion of invalid values.
- `--json` CLI output (PYPOST-530).

## Acceptance Criteria

1. Given a hidden key whose value is a number or non-envelope dict, inventory reports
   `invalid_hidden_count >= 1` and includes a per-field error message naming environment and key.
2. Given only valid envelopes and plaintext strings, `data_quality_errors` is empty.
3. `verify_decrypt_access` returns `success=False` with data-quality errors before decrypt when
   invalid shapes are present.
4. Rewrite operations abort with the same errors without modifying `environments.json`.

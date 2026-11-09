# PYPOST-1397: Technical Debt Analysis

## Shortcuts Taken

- Only `lock-dev` gained `--upgrade`. Production `lock` and OTel `lock-otel`
  still compile onto existing output files without `--upgrade`, so the same
  “stale vs fresh `.check` resolve” asymmetry can recur there.
- Transitive pins were refreshed to whatever current PyPI resolution returns
  inside `requirements-dev.in` ranges; no separate lower-bound audit of each
  bump was performed beyond the lock verification gate.

## Code Quality Issues

- Duplicated retry / body-diff shell across `check-lock`, `check-lock-dev`, and
  `check-lock-otel` remains (previously noted under PYPOST-1359).

## Missing Tests

- No negative test that intentionally corrupts `requirements-dev.txt` and
  asserts `check-lock-dev` stays fail-closed (exit 1). Existing coverage only
  asserts the clean zero-drift state.
- No Makefile smoke asserting that `lock-dev` includes `--upgrade` in its
  recipe (would catch accidental flag removal).

## Performance Concerns

- `make lock-dev --upgrade` and `make check-lock-dev` hit the network index;
  cold runs remain on the order of seconds. Existing retry/backoff covers
  transient failures.

## Follow-up Tasks

1. Align `lock` and `lock-otel` with `--upgrade` (or temp-file fresh compile) so
   documented remediation matches `check-lock` / `check-lock-otel` fresh
   resolves — NON-BLOCKER.
2. Optional fail-closed negative test for induced lock drift —
   NON-BLOCKER.
3. Optional Makefile recipe assertion for `--upgrade` on `lock-dev` —
   NON-BLOCKER.

No DoD blockers. Pre-existing suite failures outside this node are out of scope
for this 1 SP debt item and remain under their existing Jira keys.

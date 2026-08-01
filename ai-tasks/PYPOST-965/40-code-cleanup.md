# PYPOST-965: Code Cleanup

## Scope

Test-helper refactor only — no production code.

## Changes

- [x] Extracted `_materialize_slow_smoke_workspace` — one assembly sequence
- [x] Removed duplicate `_materialize_slow_smoke_seed` and unused `shutil` import from contract module
- [x] Trimmed contract imports to symbols still used

## Not changed

- `_seed_installable_package`, parser helpers, `SLOW_SMOKE_MINIMUM_PYPPOST_FILES`
- Slow smoke test class or Makefile targets

## Verification

- `make test` subset: seed contract module + Makefile integration tests (orchestrator run)

# PYPOST-932: Dev Docs

## Overview

Documented the new `typecheck` Makefile contract test in the developer
testing guide. No user-facing behavior change — `make typecheck` already
ensured `[dev]` via `venv-test`; this ticket adds the automated lock.

## Files updated

| File | Change |
| --- | --- |
| `doc/dev/testing.md` | Add PYPOST-932 to Makefile automation table; dependency-chain row names `typecheck` + `lint` |

## Architecture (docs)

- `typecheck: $(VENV_MARKER) venv-test` — unchanged; now covered by
  `test_typecheck_depends_on_marker_and_venv_test` (peer to lint / 906).

## Usage

No workflow change. Contributors and agents continue to use `make typecheck`;
the test prevents silent removal of the `venv-test` prerequisite.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `test_typecheck_depends_on_marker_and_venv_test` fails | Makefile dropped `venv-test` from `typecheck` | Restore `typecheck: $(VENV_MARKER) venv-test` |

## Validation

- Docs table lists PYPOST-932 scope.
- Dependency-chain row mentions both `lint` and `typecheck` ensure edges.

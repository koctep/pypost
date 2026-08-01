# PYPOST-906: Dev Docs

## Overview

Documented that `make lint` ensures `[dev]` via `venv-test` (same
business promise as `typecheck`), while `run` stays marker-only /
install-first. Aligns FR5 with the Step 4 Makefile contract.

## Files updated

| File | Change |
| --- | --- |
| `doc/dev/testing.md` | Install-first §: lint/typecheck ensure via `venv-test`; `run` marker-only; add PYPOST-906 to Makefile automation table; fix exit-behavior / dependency-chain rows (bare venv succeeds lint) |
| `doc/dev/setup.md` | Makefile Behavior Notes: split `run` (marker-only) from `lint`/`typecheck` (`venv-test`) |

## Architecture (docs)

- `lint: $(VENV_MARKER) venv-test` — mirrors `typecheck`; reuses
  PYPOST-905 stamp so second+ visits skip pip when `[dev]` is current.
- `run: $(VENV_MARKER)` — unchanged; out of this ticket’s scope.
- `check` inherits lint’s ensure through the existing `check: lint …`
  edge.

## Usage

Prefer `make install` once after clone. Then `make lint` / `make check`
auto-ensure `[dev]` if the test stamp is missing or stale. `make run`
still expects a ready base venv (or prior `make install`).

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| First bare-venv `make lint` is slow | One-time `venv-test` / pip install | Expected (NFR3); later visits reuse stamp |
| `make run` fails after `make venv` only | `run` is marker-only; no app deps ensure | Run `make install` |
| Docs still say bare venv fails lint | Stale wording | This Step 8 update |

## Validation

- Docs match Option A Makefile behavior from Step 4 / architecture.
- Contract table no longer claims bare venv fails `lint`.
- `make verify-ai-tasks` expects this file once Steps 1–7 are marked
  complete on the roadmap.

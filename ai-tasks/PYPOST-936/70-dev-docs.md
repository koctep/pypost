# PYPOST-936: Dev Docs

## Updated

- `doc/dev/agent_dialog_settle.md` — document shared helper location, API, and
  convention test; update pattern sketch to import helper instead of inlining
  timer/rewrap blocks.

## Unchanged

- `doc/dev/agent_e2e.md` harness table — same module file.
- `doc/dev/ui_wait.md`, `doc/dev/ui_identity.md` — no API changes.

## Verification

Dev doc describes `run_product_dialog_settle` and `modal_diag()` exports from
`tests/helpers/agent_e2e_dialog_settle.py`.

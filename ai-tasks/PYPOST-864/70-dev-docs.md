# PYPOST-864: Dev Docs Update

## Summary

Documented the seed inventory code↔doc drift guard (PYPOST-864) next to the
existing seed inventory / proof docs. No new `doc/dev/` file was required —
`agent_e2e_seed.md` already owned the inventory page; this step points at
the automated guard.

## Changes

- `doc/dev/agent_e2e_seed.md` — Proof strategy, Configuration, and
  Troubleshooting mention
  `tests/test_agent_e2e_seed_inventory_doc.py` (PYPOST-864)
- `doc/dev/agent_e2e.md` — Module inventory row for the drift-guard test

No user-facing docs (developer / harness only).

## Key developer guidance

1. Treat `pypost/fixtures/agent_e2e_seed.py` `SEED_*` as the code source of
   truth; mirror tokens in `doc/dev/agent_e2e_seed.md` Inventory section.
2. When changing an id, display name, URL template, or `base_url`, update
   code and the inventory page together.
3. Run:
   `make test PYTEST_ARGS="tests/test_agent_e2e_seed_inventory_doc.py -v"`.

## Validation

- [x] `agent_e2e_seed.md` documents the drift guard
- [x] `agent_e2e.md` module list mentions 864
- [x] Artifact `70-dev-docs.md` created
- [x] Roadmap STEP 8 marked complete
- [x] Drift guard still green after doc edits

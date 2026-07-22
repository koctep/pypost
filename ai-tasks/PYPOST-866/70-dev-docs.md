# PYPOST-866: Dev Docs Update

## Summary

Documented how maintainers keep the `agent_e2e` harness table synced with
markers, and pointed Troubleshooting at the drift guard. No new
`doc/dev/` page was required — `agent_e2e.md` already owns the umbrella
harness list.

## Changes

- `doc/dev/agent_e2e.md` — removed unmarked
  `seed_inventory_doc` row from the harness table (Step 4)
- `doc/dev/agent_e2e.md` — **Keep this table synced with markers** note
  (update Module column when marks change; unit guards stay out of the
  table; `tests/test_agent_e2e_harness_table_doc.py` in `make test`)
- `doc/dev/agent_e2e.md` — Configuration reminder to add/drop table rows
  with mark changes
- `doc/dev/agent_e2e.md` — Troubleshooting row for table≠marks drift
  (PYPOST-866)

No user-facing docs (developer / harness only).

## Key developer guidance

1. Treat `@pytest.mark.agent_e2e` as suite membership; mirror module paths
   in the harness table Module column on the same change.
2. Pure unit drift guards (seed inventory, this harness-table guard) must
   **not** carry `agent_e2e` and must **not** appear in the table.
3. Run:
   `make test PYTEST_ARGS="tests/test_agent_e2e_harness_table_doc.py -v"`.

## Validation

- [x] Maintenance note complete next to the harness table
- [x] Troubleshooting documents table≠marks failure
- [x] Artifact `70-dev-docs.md` created
- [x] Roadmap STEP 8 marked complete
- [x] Drift guard still green after doc edits

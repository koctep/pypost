# PYPOST-890: Presentation matrix findings

Durable list of method × body cells that fail desired Send → response
presentation invariants. Consumed by
[PYPOST-891](https://pypost.atlassian.net/browse/PYPOST-891) for Bug triage.

Product fixes are **out of scope** for PYPOST-890. Mark known HEAD defects
with `pytest.mark.xfail` on the matching matrix param and add a row here in
the same change.

## Findings table

| method | body_shape | stub_status | stub_token | invariant | pytest_nodeid | observed | triage |
| --- | --- | --- | --- | --- | --- | --- | --- |

*(empty — no product defects recorded yet)*

**Triage (PYPOST-891, 2026-07-21):** Empty table reviewed. Verdict: **no
product defects found / won’t file**. See
`ai-tasks/PYPOST-891/triage-summary.md`. Epic comment on PYPOST-888 is
orchestrator-owned.

## Step 3 HEAD scan (2026-07-21)

Full cartesian (25 cells) under
`make test-agent-e2e PYTEST_ARGS="tests/test_agent_e2e_presentation_matrix.py -m agent_e2e -v"`:
**25 passed**. No xfail rows required on HEAD (discard present).

Local red protocol (temp `_discard_chunk_buffer` no-op in
`_on_request_finished`, then restore): `POST-json_ok` failed with
`count=2` as expected — not a findings row.

## How rows are added

1. Matrix asserts desired invariants (body token once; `Status: N` once).
2. Real product defect on HEAD → `xfail(strict=False, reason=…)` on that
   param **and** a row in this table.
3. Unexpected smoke failures fail the suite (do not skip silently).
4. Local red proof via temporary `_discard_chunk_buffer` no-op is **not** a
   findings row (discard restored; not a product defect on HEAD).

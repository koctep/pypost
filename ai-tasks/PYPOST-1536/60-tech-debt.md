# PYPOST-1536: Technical Debt Analysis

## Shortcuts Taken

None material. Product discovery path left unchanged; only the regression test
was corrected to match the real non-blocking contract.

## Code Quality Issues

- Other tests still use local `_wait_until` / dialog wait helpers duplicated
  across remote-collection repro modules — already tracked via shared-helper
  debt (e.g. PYPOST-1455). Out of scope here.

## Missing Tests

- The single non-blocking init case remains sufficient. Optional stress under
  artificial CPU load was not added (2 SP debt; Event-gate covers the contract).

## Performance Concerns

- None. Test no longer depends on a tight wall-clock bound; worker I/O is gated
  rather than sleeping a fixed 200ms before release (release is immediate after
  `__init__` returns).

## Follow-up Tasks

| Item | Verdict | Notes |
| --- | --- | --- |
| Unrelated suite failures outside this node id | NON-BLOCKER — pre-existing / out of scope | Do not fix inside PYPOST-1536 |
| Shared Qt dialog wait helpers consolidation | NON-BLOCKER — pre-existing | PYPOST-1455 |

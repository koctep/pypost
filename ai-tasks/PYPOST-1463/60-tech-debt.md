# PYPOST-1463: Technical Debt Analysis

## Shortcuts Taken

No temporary stub or bypass remains in the implemented process reconfiguration path.
The transaction uses the existing supervisor and finite startup/stop budgets. A synchronous
registry lifecycle lock serializes control operations while peer child processes continue serving.
This is an accepted architecture trade-off; asynchronous control scheduling is outside this task.

Reusing the same endpoint can briefly interrupt the affected server. A changed-endpoint candidate
starts before the prior worker is reclaimed. These behaviors match the accepted requirements.

## Code Quality Issues

No new code-quality blocker was identified in the reviewed implementation. Public server identity
is separate from supervisor worker identity, so retired worker exits cannot fail a new generation.
Recovery snapshots are copied, and accepted variable updates refresh the snapshot used for rollback.
Failed candidate cleanup retains ownership; clear/restore refuse to discard it, and stop/stop_all
can retry cleanup-only entries. These ownership paths were corrected during Step 4 review.

Production and documentation lint pass. Test lint has the pre-existing violation recorded below.
The typecheck baseline gate passes with its existing 175 known errors; this task adds no baseline.

## Missing Tests

No missing acceptance test is classified as a blocker. The 12 real-process cases cover same/new
endpoint commits, rejection before/after bind, restoration failure, peer continuity, stale worker
callbacks, concurrent stop/edit ordering, retained cleanup, and cleanup retries through clear/restore
and stop_all. The module declares an explicit 90-second pytest timeout and bounds synchronization.
Caplog contracts verify accepted/rejected outcomes and exclusion of a secret-bearing exception.
Existing process isolation and thread registry suites also pass.

Broader Windows shutdown and stress parity remain tracked by the existing sprint issue
[PYPOST-1470](https://pypost.atlassian.net/browse/PYPOST-1470); this task creates no duplicate scope.

## Performance Concerns

No new performance follow-up is required for the implemented lifecycle correction. Startup and
recovery are bounded attempts rather than retry loops. Deep copies keep accepted runtime snapshots
independent of later mutations; they occur at lifecycle changes rather than per request.
Lifecycle operations across this registry are serialized, while existing peer workers remain live.

## Follow-up Tasks

- **TD-1 — NON-BLOCKER — pre-existing:** Test lint reports
  `tests/test_mcp_server_registry.py:308:101: E501 line too long (111 > 100 characters)`.
  Repro: `make lint`. The same failure reproduced at base commit `33d5cb1a` in a throwaway worktree.
  This is a source lint location rather than a pytest node ID. It does not arise from the new tests.
  Jira: [PYPOST-1509](https://pypost.atlassian.net/browse/PYPOST-1509).
  Evidence: `/tmp/PYPOST-1463-step4-baseline-lint.log`.

No untracked follow-up or newly identified blocker remains in this analysis.

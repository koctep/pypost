# PYPOST-982: Technical Debt Analysis

## Scope

This analysis covers the POST-path mapping settle-timeout companion, the
inventory discoverability assertion, and the Step 1–6 artifacts. The change is
test-harness-only; no production request, mapping, timeout, or observability
behavior was changed.

## Shortcuts Taken

No material shortcut or temporary production workaround was introduced.
The companion deliberately uses the always-false readiness predicate and the
shared `FORCED_SETTLE_TIMEOUT_S` value (`0.05` seconds) to reach the diagnostic
path deterministically. The value is centralized in
`tests/helpers/agent_e2e_timeouts.py`, so this is an intentional test policy,
not an untracked per-test literal.

## Code Quality Issues

### NON-BLOCKER — duplicated GUI setup in GET and POST companions

`tests/test_agent_e2e_http_mapping_multi_url.py` repeats widget discovery,
session setup, stub installation, and Send interaction between the GET and
POST timeout companions. This is a small maintenance cost, but the duplication
keeps each diagnostic contract independently readable and currently involves
only two focused scenarios. Extracting a helper now would add indirection
without a demonstrated defect.

No Jira follow-up is recommended. Revisit if more mapping method companions are
added or the setup sequence changes in multiple places.

### NON-BLOCKER — stable step names remain string contracts

The POST step name `wait_response_after_mapping_post_send` is intentionally
asserted as an exact string and is also used by the happy path and developer
documentation. A future rename must update those consumers together. This is
the desired diagnostic contract rather than a correctness defect, and the
existing inventory and focused assertions make accidental removal visible.

No Jira follow-up is recommended.

## Missing Tests

No actionable coverage gap was found for this task. The implementation has:

- an independent successful POST status/body assertion in the two-URL mapping
  scenario;
- a forced POST timeout assertion for the exact `step` and non-empty string
  `response_excerpt`; and
- an inventory assertion that the companion remains discoverable.

Both relevant modules have explicit pytest timeout markers, and the helper
wait is bounded by the explicit `0.05`-second timeout. The companion does not
need to duplicate lower-level response-panel edge cases already owned by the
shared helper tests.

## Performance Concerns

No actionable performance concern was found. The GUI fixture startup is the
main cost and is consistent with the neighboring GET companion and the
existing mapping scenario. The forced wait is finite and near-zero, while the
module-level 60-second timeout remains the outer safety boundary.

## Documentation Status

### COMPLETED — developer documentation records the POST companion

`doc/dev/agent_e2e_http.md` now documents the mapping GET and POST timeout
companions, their shared timeout policy, and the focused invocation. The
in-scope Step 8 developer-documentation update is complete. Future
documentation work is limited to updating the same guide if additional mapping
companions or diagnostic contracts are added.

## Follow-up Tasks

No additional Jira follow-up is justified by this analysis. Step 8 documentation
is complete; future documentation maintenance is limited to updating the guide
if additional mapping companions or diagnostic contracts are added. The
remaining observations are low-risk trade-offs of a focused two-path test
companion.

## Pre-existing Test Failures

None were introduced or evaluated as part of this Step 7 artifact. Any
repository-wide baseline failures remain outside PYPOST-982's scope and should
retain their existing owning Jira references in the final task validation.

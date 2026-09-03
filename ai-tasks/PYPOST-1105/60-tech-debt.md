# PYPOST-1105 Technical Debt

## Retained product scope

The live tests cover a fresh upstream connection for each MCP session. They do
not measure or change connection pooling, session reuse, or header-aware cache
invalidation. Those performance concerns remain the separate PYPOST-1101 scope.

## Test-harness tradeoff

Process startup is more expensive than in-process ASGI tests, so both cases are
marked `slow` and excluded from the default fast suite. The harness uses daemon
children and bounded termination to keep that cost and failure risk contained.

No new Jira debt item was needed. The test-only implementation introduces no
runtime dependency, setting, network destination, or production behavior.

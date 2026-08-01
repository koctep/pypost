# PYPOST-902: Observability

## Product / runtime impact

**None.** Fixture-layer routing only; no change to RequestService, workers, or
UI logging paths.

## Existing events (reused)

| Event | Level | When | Change |
| --- | --- | --- | --- |
| `agent_e2e_http_stub_installed` | INFO | Mapping stub enter | Unchanged — still `name=url_router` for default Mapping installs |

Logger: `pypost.fixtures.agent_e2e_http`.

## Deliberately not added

- No per-route DEBUG log on compound vs bare match — would noise every Send in
  scenarios; authors infer routing from map keys and unit proofs.
- No new metrics or counters.

## Test observability

Unit tests assert routing outcomes directly (canned body identity). Miss case
still surfaces full `AssertionError` message with sorted `known=` keys for
author debugging.

## Verification

```bash
make test PYTEST_ARGS='tests/test_agent_e2e_http.py -q'
```

Optional caplog proof not required — install log behavior unchanged from 868/901.

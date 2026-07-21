# PYPOST-854: Developer Documentation

## Updates

| File | Change |
| --- | --- |
| `doc/dev/agent_e2e.md` | **No edit** — marker, make, CI already documented (858/861) |
| `doc/dev/agent_e2e_env.md` | **No edit** — Make/CI status Delivered via 861 |
| `doc/dev/testing.md` | **No edit** — makefile smoke + CI jobs covered by 861 |
| `doc/dev/setup.md` | **No edit** — `test-agent-e2e` wording already present |

## Why no new pages

Step 7 DoD is developer discoverability of the outcomes 854 tracked. Those
outcomes live under the umbrella and testing docs from the absorbing
stories. Adding a “PYPOST-854 superseded” page would duplicate history
without improving usage.

Authoritative usage paths:

- Marker + make: [agent_e2e.md](../../doc/dev/agent_e2e.md)
- Env pack contract / make-CI status:
  [agent_e2e_env.md](../../doc/dev/agent_e2e_env.md)
- Suite CI layout: [testing.md](../../doc/dev/testing.md)

## Structure covered (existing)

- **Overview** — prefer `make test-agent-e2e`; CI `agent-e2e` job
- **Architecture** — env pack + marker selection
- **Usage** — default `-m "agent_e2e and not slow"`; `PYTEST_ARGS` override
- **Configuration** — CI make gate row
- **Troubleshooting** — reproduce CI gate locally

## Related

- Debt source: [PYPOST-839](https://pypost.atlassian.net/browse/PYPOST-839)
- Absorbed by: [PYPOST-858](https://pypost.atlassian.net/browse/PYPOST-858),
  [PYPOST-861](https://pypost.atlassian.net/browse/PYPOST-861)

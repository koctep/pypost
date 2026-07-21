# PYPOST-861: Developer Documentation

## Updates

| File | Change |
| --- | --- |
| `doc/dev/agent_e2e.md` | CI section; config row; troubleshooting; intro make/CI |
| `doc/dev/agent_e2e_env.md` | Make/CI status → Delivered; run-entry wording |
| `doc/dev/testing.md` | Overview CI note; makefile smoke table; CI jobs |
| `doc/dev/setup.md` | `test-agent-e2e` wording + CI cross-link |

## Structure covered

- **Overview** — make + CI as first-class env-pack entry
- **Architecture** — env contract status table
- **Usage** — `make test-agent-e2e`, CI job `agent-e2e`
- **Configuration** — CI make gate row
- **Troubleshooting** — reproduce CI make gate locally

## Related

- Umbrella remains [agent_e2e.md](../../doc/dev/agent_e2e.md)
- Contract: [agent_e2e_env.md](../../doc/dev/agent_e2e_env.md)

# PYPOST-773: Architecture

## Approach

Documentation-only change. No application code.

## Target edit

Add one numbered entry in the `### Audits` section of `doc/dev/README.md`, immediately after
the Observability and Logging Audit line:

```markdown
1. [Prometheus Monitoring](../prometheus_monitoring.md)
```

## Rationale

- Relative path `../prometheus_monitoring.md` resolves from `doc/dev/` to the existing guide at
  repo `doc/prometheus_monitoring.md`.
- Placement after `observability_audit.md` groups operator monitoring docs with observability
  audit material (PYPOST-690 remediation: "under Observability").
- Keeps the guide at its current path; root README and `doc/mcp_integration.md` links stay valid.

## Out of scope

- Moving `prometheus_monitoring.md` into `doc/dev/`
- Updating metric inventory content (PYPOST-750)
- Cross-linking user and developer MCP guides (PYPOST-774 / R-P3-002)

## Verification

- `rg 'prometheus_monitoring' doc/dev/README.md` returns the new TOC line
- `make check` passes

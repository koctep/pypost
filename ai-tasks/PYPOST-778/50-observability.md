# PYPOST-778: Observability

## CI visibility

The `security-audit` job writes a GitHub Actions step summary:

- Job name: `pip-audit (dependency CVE scan)`
- On failure: pip-audit stdout/stderr in the job log lists CVE id, package, and fixed version.

## Local visibility

`make security-audit` prints pip-audit results to the terminal. Exit code is non-zero when
vulnerabilities are found.

## Logging

No application runtime logging changes — supply-chain gate only.

## Monitoring gaps (non-blockers)

- No Prometheus metric for CVE count (not applicable to CI-only scan).
- Dependabot PRs complement but do not replace the explicit fail gate.

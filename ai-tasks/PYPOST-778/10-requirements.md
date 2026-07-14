# PYPOST-778: Add pip-audit to CI

## Goals

PyPost ships HTTP, MCP, and cryptography dependencies. The PYPOST-691 supply-chain audit
(R-P1-002 / V-001) found no automated CVE gate before merge. Maintainers need CI to fail when
known critical or high vulnerabilities appear in the resolved production dependency tree.

## User Stories

- **As a maintainer**, I want every push and pull request to run a dependency vulnerability scan
  so that known CVEs in production packages are caught before merge.
- **As a developer**, I want a Makefile target that mirrors the CI scan so I can reproduce failures
  locally before pushing.

## Definition of Done

- [ ] GitHub Actions runs `pip-audit` against `requirements.txt` on every push and PR.
- [ ] The job fails when pip-audit reports known vulnerabilities in the resolved tree.
- [ ] A `make security-audit` target exists for local use.
- [ ] Developer docs describe the scan, exception process, and local command.
- [ ] Existing test suite remains green.

## Task Description

Parent audit PYPOST-691 recommendation **R-P1-002** requires:

```text
pip install pip-audit && pip-audit -r requirements.txt
```

Dependabot is already configured (`.github/dependabot.yml`); this task adds the explicit CI gate.
Lock-file adoption (R-P2-001 / PYPOST-779) is out of scope.

## Q&A

| Question | Answer |
| --- | --- |
| Which Python version should the job use? | 3.11 — matches primary CI matrix and `make install` smoke. |
| Should dev tools be scanned? | No — only production deps from `requirements.txt`. |
| What if a CVE has no fix yet? | Document `--ignore-vuln` exception process in dev docs; use sparingly. |

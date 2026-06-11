# PYPOST-571: Propose CI guardrails against silent test false positives

## Goals

Sibling analysis under epic
[PYPOST-566](https://pypost.atlassian.net/browse/PYPOST-566) established that a green full
suite can emit **72 ERROR** and **138 WARNING** application log lines (PYPOST-567) while still
reporting 937 passed. Error-path tests in worker and presenter modules have strong behavioral
assertions (PYPOST-568), but CI log output remains alarming and could mask real regressions.
This task proposes **enforceable** CI guardrails — not implementation — so follow-up work can
gate merges on unexpected log storms, timeout edge cases, and missing log contracts.

## Programming Language

Python 3.10+ (PyPost project standard).

## User Stories

- As a **maintainer**, I want a written CI guardrails proposal so that green runs cannot hide
  unexpected ERROR storms or timeout-boundary passes without a documented enforcement plan.
- As a **team lead**, I want chosen approaches and rejected alternatives with effort estimates
  so that implementation tickets can be scoped and prioritized.
- As a **reviewer**, I want a log allowlist derived from the PYPOST-567 inventory so that
  known error-path noise is explicitly permitted while new ERROR patterns fail CI.
- As a **test author**, I want a `caplog` contract for error-path tests so that intentional
  ERROR emissions are either asserted in-test or registered in the allowlist.

## Definition of Done

- [x] `ci-guardrails-proposal.md` covers all four guardrail pillars: log allowlist, `caplog`
      contract, duration budget, post-run script.
- [x] Proposal names chosen approach, rejected alternatives, and implementation effort estimates.
- [x] Inputs from PYPOST-567 inventory and PYPOST-568 error-path audit are referenced.
- [x] Timeout and `log_cli` context from PYPOST-569/PYPOST-570 Jira scope incorporated.
- [x] Top-down artifacts stored under `ai-tasks/PYPOST-571/`.
- [x] `doc/dev/testing.md` updated with a brief CI guardrails section.
- [x] Analysis only — no production code, test, or workflow changes in this issue.

## Task Description

### Problem

Pytest reports success while application code logs failures at ERROR/WARNING level. Without CI
guardrails, a new regression that adds ERROR lines or hangs until the outer timeout may look
like a normal green run in GitHub Actions logs. The epic analysis tasks quantified the noise
but did not prescribe enforcement.

### Baseline inputs (2026-06-11)

| Source | Key facts |
| --- | --- |
| PYPOST-567 `inventory.md` | 210 log entries (72 ERROR, 138 WARNING); 23 loggers |
| PYPOST-568 audit | 22 focus-module ERROR lines; 0 high-risk false positives |
| PYPOST-569 scope | Flag tests with duration >80% of `pytest.mark.timeout` |
| PYPOST-570 scope | `log_cli=true`, `log_cli_level=WARNING` in `pytest.ini` |
| Local duration probe | `pytest --durations=25 --durations-min=5`: no test ≥5 s; suite ~45–48 s |

### Functional requirements

1. **Log allowlist** — Define how CI permits known expected-path ERROR message prefixes from
   the inventory; specify format, maintenance, and fail-on-unlisted rules.
2. **`caplog` contract** — Define when error-path tests must assert log emission vs rely on
   allowlist; reference PYPOST-568 medium-risk cases.
3. **Duration budget** — Define warn/fail thresholds relative to per-test timeout markers
   (>80% rule from PYPOST-569); note current suite has no offenders at 5 s floor.
4. **Post-run script** — Define offline log verification after `make test` / CI pytest,
   reusing `scripts/parse_test_log_inventory.py` patterns; specify exit codes and CI wiring.
5. **Alternatives** — Evaluate and reject or defer: strict pytest warnings hook, disabling
   `log_cli`, fail-on-any-ERROR without allowlist, pytest plugins.
6. **Effort estimates** — Size implementation follow-ups (S/M/L) for each chosen guardrail.

### Non-functional requirements

- Proposal must be actionable without re-reading PYPOST-567/568 source trees.
- Guardrails must not require live Prometheus or MCP during CI test job.
- Allowlist updates must be reviewable in git (YAML or TOML, not Jira-only).

### Out of scope

- Implementing guardrail scripts, workflow changes, or test edits.
- Changing `pytest.ini` `log_cli` settings (PYPOST-570 implementation).
- Fixing suspicious/unknown inventory groups (separate debt tickets).

## Q&A

| Question | Answer |
| --- | --- |
| Why proposal-only? | Jira acceptance criteria: analysis before enforcement avoids premature CI breakage. |
| Why four pillars? | Maps to Jira options list; together they cover log noise, test contracts, hangs, and CI wiring. |
| What if PYPOST-569/570 are incomplete? | Proposal uses Jira descriptions plus local duration probe; notes dependency on their final lists. |

# PYPOST-570: Review pytest log_cli config vs test noise (WARNING level)

## Goals

`pytest.ini` enables global live CLI logging at WARNING level. A green full-suite run still
emits **72 ERROR** and **138 WARNING** lines (PYPOST-567 baseline). This task quantifies that
noise, compares remediation options, and recommends whether to keep or change the config.

## Programming Language

Python 3.10+ (PyPost project standard).

## User Stories

- As a **maintainer**, I want quantified log noise from a green run so that I know how much
  output `log_cli_level = WARNING` produces.
- As a **maintainer**, I want a comparison of disable / caplog / override / plugin options
  so that I can choose a remediation path with clear trade-offs.
- As a **team lead**, I want a written keep-vs-change recommendation with migration steps
  so that PYPOST-571 and CI changes can be scoped without re-analysis.

## Definition of Done

- [x] Noise quantified and tied to PYPOST-567 inventory counts.
- [x] Options evaluated: CI disable, caplog, CLI overrides, fail-on-ERROR plugins.
- [x] Recommendation documented with migration steps if change recommended.
- [x] Alignment noted with `.cursor/lsr/do-testing.md` (timeouts mandatory; logging not covered).
- [x] Artifacts under `ai-tasks/PYPOST-570/`; `doc/dev/testing.md` updated if needed.
- [x] Jira PYPOST-570 closed with summary comment.

## Task Description

### Problem

Global `log_cli = true` and `log_cli_level = WARNING` (introduced in PYPOST-52) surface every
application WARNING and ERROR during every test invocation, including `make test` and CI. Most
lines come from intentional error-path tests (PYPOST-568: no high-risk false positives), but
they make green runs look alarming and obscure real regressions during log triage.

### Baseline (PYPOST-567, 2026-06-11)

| Metric | Value |
| --- | --- |
| Capture | `make test > tests.txt 2>&1` |
| Tests passed | 937 (+ 39 subtests) |
| Live-log ERROR lines | 72 |
| Live-log WARNING lines | 138 |
| Distinct tests emitting logs | 126 |
| Classification (inventory) | expected 163, suspicious 21, unknown 26 |

### Functional requirements

1. Quantify noise attributable to `log_cli` / `log_cli_level`.
2. Compare remediation options with pros, cons, and effort.
3. Recommend keep vs change; document migration steps for the recommended path.
4. Cross-reference PYPOST-568 (tests are sound; noise is the issue).

### Non-functional requirements

- Analysis-only — no `pytest.ini`, CI, or test changes in this task.
- Recommendation must be actionable for PYPOST-571 (allowlist) and optional CI follow-up.

### Out of scope

- Implementing CI guardrails (PYPOST-571).
- Migrating tests to `caplog`.
- Changing production log levels.

## Q&A

| Question | Answer |
| --- | --- |
| Why not just disable logging everywhere? | Local developers lose live correlation between failing tests and app logs; a split (local on, CI off) preserves both. |
| Is the suite producing false greens? | PYPOST-568 found no high-risk false positives; pytest outcome is independent of log output. |
| Does pytest support log-on-failure only? | No built-in `log_cli` mode; overrides or plugins required. |

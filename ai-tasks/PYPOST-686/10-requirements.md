# PYPOST-686: Audit — test coverage and test quality

## Goals

PyPost relies on a large pytest suite (1,400+ tests) for regression safety across core HTTP/MCP
logic, encryption, and Qt GUI flows. Without a structured assessment of coverage gaps, timeout
compliance, flaky patterns, and the balance between unit and integration tests, maintainers risk
shipping regressions in under-tested modules, CI instability, or slow feedback loops.

This audit establishes an evidence-based picture of test suite health so the team can prioritize
coverage improvements, stabilize flaky tests, and keep timeout and logging guardrails aligned with
`.cursor/lsr/do-testing.md`.

## Programming Language

Python (audit and analysis task; deliverables are markdown reports and follow-up Jira issues).

## User Stories

- As a **maintainer**, I want a consolidated view of test coverage gaps and untested modules, so
  I can schedule targeted test work alongside features.
- As a **CI operator**, I want to know whether timeout markers, duration budgets, and log
  guardrails are consistently enforced, so hung or noisy tests are caught early.
- As a **reviewer**, I want clarity on integration vs unit test balance, so new tests are placed at
  the right level of the pyramid.
- As a **developer on macOS or Python 3.14**, I want flaky or environment-specific failures
  documented, so local `make test` results are interpretable.
- As a **tech-debt owner**, I want prioritized follow-up items for test gaps and instability, so
  remediation can be scheduled.
- As a **product owner**, I want confidence that critical paths (HTTP execution, MCP, encryption,
  GUI save flows) have automated regression coverage.

## Definition of Done

- [ ] An audit report is stored under `ai-tasks/PYPOST-686/` with summary, scope, methodology,
  findings, and recommendations.
- [ ] Findings cover line coverage (overall and low-coverage modules), timeout marker compliance,
  and CI test configuration.
- [ ] Findings cover integration vs unit balance and representative test categories (GUI, MCP,
  storage, Makefile smoke).
- [ ] Findings cover flaky or environment-sensitive patterns (segfaults, order dependence,
  Python version coupling).
- [ ] Findings cover test maintainability (helpers, duplication, baseline regression guards).
- [ ] Findings cover test observability (log guardrails, duration audit, caplog usage).
- [ ] Each significant finding includes impact and a recommended remediation direction.
- [ ] Findings are prioritized (P1/P2/P3) for follow-up ticketing.
- [ ] Developer summary added at `doc/dev/test_audit.md` with link to full report.
- [ ] Out-of-scope areas are explicitly listed.

## Task Description

**Problem:** The PyPost test suite grew organically across many PYPOST feature tasks. Coverage
enforcement (`--cov-fail-under=70`), per-test timeouts, log guardrails, and duration budgets exist,
but there is no consolidated audit of whether they are sufficient, where gaps remain, and which
tests are unstable on developer machines.

**Business intent:** Make test health visible and schedulable — reducing undetected regressions,
CI surprises, and maintainer friction when extending the suite.

### In Scope

- Automated pytest suite under `tests/` (fast and slow markers).
- Coverage of `pypost/` via `make test-cov` / CI `--cov=pypost`.
- Per-test `@pytest.mark.timeout` compliance per `.cursor/lsr/do-testing.md`.
- CI configuration (`.github/workflows/test.yml`), `pytest.ini`, `Makefile` test targets.
- Test helpers (`tests/helpers/`), conftest fixtures, guardrail scripts (`scripts/`).
- Integration vs unit categorization and maintainability observations.
- Test logging observability (`log_cli`, `verify_test_log_guardrails.py`, `caplog` patterns).

### Out of Scope

- Implementing test fixes or new tests (audit only).
- Performance benchmarking of the application under test.
- Manual MCP/Prometheus verification workflows (documented separately in `doc/dev/testing.md`).
- Re-auditing security or architecture (see PYPOST-685, PYPOST-684).
- Formal mutation testing or property-based testing adoption.

## Functional Requirements

- The audit must produce a structured written report for developers and CI maintainers.
- The audit must run or cite `make test` / pytest collection stats and coverage measurements.
- The audit must verify timeout marker presence and distribution.
- The audit must identify modules with low or zero direct test coverage.
- The audit must assess CI parity (Python matrix, slow job, guardrail scripts).
- The audit must document flaky or failing tests observed during the audit run.
- The audit must include prioritized recommendations for follow-up work.

## Non-Functional Requirements

- **Clarity:** Findings understandable to a developer new to PyPost testing conventions.
- **Actionability:** Recommendations specific enough to become Jira tickets.
- **Traceability:** Report links to `doc/dev/testing.md`, `do-testing.md`, and prior audit tasks.
- **Proportionality:** Depth matches risk — prioritize core execution, MCP, and encryption paths.

## Constraints and Assumptions

- Audit artifacts are markdown under `ai-tasks/PYPOST-686/`.
- Timeout rules in `.cursor/lsr/do-testing.md` are the compliance baseline.
- CI is authoritative for merge gates; local results may differ by OS/Python (documented).
- Step 1 captures business requirements only; methodology belongs in Step 2.

## Main Entities (Business View)

| Entity | Description |
| --- | --- |
| Fast test suite | `make test` — all tests except `-m slow` |
| Slow smoke | `make test-slow` — Makefile install smoke |
| Coverage gate | Minimum 70% line coverage on `pypost` |
| Timeout marker | Explicit per-test ceiling via `pytest.mark.timeout` |
| Integration test | Live server/socket or multi-component wiring |
| GUI test | Qt widget tests with `QT_QPA_PLATFORM=offscreen` |
| Log guardrail | CI script rejecting unexpected ERROR logs |
| Duration budget | CI script warning/failing on timeout utilization |
| Audit finding | Documented gap with impact and priority |

## Acceptance Criteria (Audit Deliverables)

| ID | Criterion |
| --- | --- |
| AC-1 | Report exists under `ai-tasks/PYPOST-686/` with executive summary and detailed findings. |
| AC-2 | Coverage section cites measured or batched coverage % and low-coverage modules. |
| AC-3 | Timeout section confirms compliance mechanism and marker distribution. |
| AC-4 | Balance section categorizes unit, GUI, integration, and e2e tests. |
| AC-5 | Flaky section documents observed failures and instability patterns. |
| AC-6 | CI section describes workflow jobs, matrix, and guardrail scripts. |
| AC-7 | Recommendations prioritized P1/P2/P3. |
| AC-8 | `doc/dev/test_audit.md` summarizes findings with link to full report. |

## Q&A

| Question | Answer |
| --- | --- |
| Why audit tests now? | Suite exceeds 1,400 tests with multiple guardrails; consolidated health check prevents drift. |
| How is this different from PYPOST-382? | PYPOST-382 documented testability seams; this audit assesses suite-wide health and gaps. |
| Will this add tests? | No — audit only; follow-ups ticketed separately. |
| Primary deliverable? | Written audit report plus dev doc summary. |

# PYPOST-567: Inventory ERROR/WARN lines from full test run log

## Goals

The full PyPost test suite reports **937 passed** while the captured run log also contains
**72 ERROR** and **138 WARNING** lines (`grep ERROR` / `grep WARN` on `tests.txt`). That
mismatch hides real regressions: CI and local runs look green even when application code logs
failures at ERROR or WARNING level.

This task is the first step under epic
[PYPOST-566](https://pypost.atlassian.net/browse/PYPOST-566). It produces a structured
inventory of every ERROR and WARNING line from one captured `make test` run so maintainers can
see which log noise is intentional (expected failure-path tests) versus which signals warrant
follow-up work. The inventory becomes the baseline for later epic tasks (timeout review,
remediation options, CI guardrails).

## Programming Language

Python 3.10+ (PyPost project standard).

## User Stories

- As a **maintainer**, I want a complete list of ERROR and WARNING lines from a full test run
  so that I can see how much log noise the suite produces while still passing.
- As a **maintainer**, I want each log line linked to the test that was running when it was
  emitted so that I can trace noise back to specific tests.
- As a **maintainer**, I want log lines grouped by logger name with counts so that I can
  prioritize review by module and spot hotspots.
- As a **maintainer**, I want each group tagged **expected**, **suspicious**, or **unknown**
  so that follow-up work can focus on groups that may indicate false-positive risk.
- As a **team lead**, I want each group mapped to its originating module and a suggested
  follow-up so that remediation tickets can be scoped without re-reading the raw log.

## Definition of Done

- [ ] Every ERROR and WARNING line from the baseline capture is represented in the inventory
      (counts reconcile with baseline: 72 ERROR, 138 WARN/WARNING).
- [ ] Each inventory entry records logger name, log level, message text, and the adjacent
      test identifier from the capture.
- [ ] Entries are grouped by logger; a summary table shows line counts per group.
- [ ] Each group carries a classification tag: **expected**, **suspicious**, or **unknown**.
- [ ] Each group notes the originating application module and a suggested follow-up action.
- [ ] The inventory is attached to Jira issue PYPOST-567 and stored in the repository under
      `ai-tasks/PYPOST-567/`.

## Task Description

### Problem

PyPost runs the full suite with live log output enabled (`log_cli = true`,
`log_cli_level = WARNING` in `pytest.ini`). Many tests deliberately exercise error paths
(worker exceptions, HTTP failures, encryption errors, alert emission). Those tests **pass**
while still writing ERROR or WARNING lines. Without a catalog, reviewers cannot distinguish
benign test-induced noise from signals that would indicate a production or CI regression.

### Baseline capture (2026-06-11)

Source: `make test > tests.txt 2>&1` (file present at repository root).

| Metric | Value |
| --- | --- |
| Tests passed | 937 (+ 39 subtests) |
| Run duration | ~45–47 s |
| ERROR lines (`grep ERROR tests.txt`) | 72 |
| WARN lines (`grep WARN tests.txt`) | 138 |
| pytest summary warning | 1 (StarletteDeprecationWarning) |

All 72 ERROR lines match the structured live-log format
(`HH:MM:SS ERROR    <logger>: <message>`). All 138 WARN matches are WARNING-level live-log
lines (`grep WARN` matches the `WARNING` level token).

Observed logger hotspots (preliminary, for scope sizing only):

| Logger | ERROR | WARNING |
| --- | ---: | ---: |
| `pypost.core.request_service` | 19 | 61 |
| `pypost.core.template_service` | 0 | 39 |
| `pypost.core.alert_manager` | 0 | 28 |
| `pypost.core.key_provider` | 12 | 0 |
| `pypost.core.encryption_migration` | 6 | 12 |
| Other loggers (~15 names) | 35 | 8 |

### Functional requirements

1. **Use the captured log** — Work from the existing `tests.txt` baseline unless a fresh
   capture is required to reconcile counts; document the capture command and date.
2. **Extract structured fields** — For each ERROR/WARNING live-log line, record logger name,
   level, and message body.
3. **Associate with test context** — Record the test node id (module, class, test name) from
   the nearest preceding test header or PASSED/FAILED line in the capture.
4. **Group and summarize** — Aggregate lines by logger; produce a count table per group.
5. **Classify groups** — Tag each group:
   - **expected** — log emission is an intentional part of an error-path test that still passes;
   - **suspicious** — passing test emits logs that could mask a real failure or suggests weak
     assertions;
   - **unknown** — insufficient context to classify without further review.
6. **Recommend follow-up** — For each group, note the application module and a concise
   suggested next step (e.g. add caplog assertion, tighten test, create follow-up Jira issue,
   no action).
7. **Publish inventory** — Deliver as a readable report suitable for Jira attachment and repo
   storage.

### Non-functional requirements

- **Completeness** — Inventory totals must match the baseline counts (72 ERROR, 138 WARNING).
- **Traceability** — Every grouped line must be traceable to a specific test name in the
  capture.
- **Reproducibility** — Document which log capture was analyzed so a future run can be
  diffed against the same baseline.
- **Clarity** — Classification rationale must be stated in plain language; avoid jargon-only
  tags without explanation.

### Constraints and assumptions

- Analysis covers **one** full-suite capture (`tests.txt`); re-running the suite may shift
  counts slightly (duration and ordering) but the baseline counts above are the acceptance
  target for this task.
- Only **application live-log lines** at ERROR and WARNING level are in scope; pytest’s own
  warnings summary section is out of scope unless explicitly cross-referenced.
- Traceback and exception text adjacent to log lines may provide classification context but
  are not separate inventory rows unless they contain a distinct log-level emission.
- This task **does not** change tests, production logging, or CI configuration — inventory
  and classification only. Remediation belongs to follow-up work under PYPOST-566.

### Out of scope

- Fixing tests or production code to reduce log noise.
- Implementing CI guardrails or log-threshold gates.
- Timeout-budget review (separate epic scope).
- Changing `pytest.ini` log settings.

### Main entities (business perspective)

| Entity | Description | Key attributes |
| --- | --- | --- |
| Test run capture | Saved stdout/stderr from one full `make test` execution | Date, command, pass count, duration |
| Log event | A single ERROR or WARNING line emitted during the run | Level, logger name, message text |
| Test context | The test active when the log event occurred | Test node id, outcome (PASSED/FAILED) |
| Logger group | All log events sharing the same logger name | Group name, ERROR count, WARNING count |
| Classification | Maintainer judgment on group risk | expected / suspicious / unknown; rationale |
| Inventory report | Deliverable catalog for the epic | Group table, per-group detail, follow-up notes |

## Q&A

| Question | Answer |
| --- | --- |
| Why inventory logs if all tests pass? | Passing tests that emit ERROR/WARNING obscure real failures during log review and CI triage; the epic exists to reduce false-positive risk. |
| Why group by logger? | Logger names map to application modules and ownership, making prioritization and follow-up tickets practical. |
| What makes a group “expected”? | The group’s tests deliberately trigger that log as part of an error-path scenario and the behavior is documented or obvious from test intent. |
| What makes a group “suspicious”? | A passing test emits logs that resemble production failure signals without clear test intent, or may indicate the test does not assert enough. |
| What is the deliverable format? | A structured report (tables + grouped detail) attached to PYPOST-567 and checked into `ai-tasks/PYPOST-567/`. |
| Which capture file? | Repository root `tests.txt` unless counts fail to reconcile, in which case a fresh capture must be documented. |

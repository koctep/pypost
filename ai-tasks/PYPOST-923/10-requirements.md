# PYPOST-923: Fix CI failures on dev (stale locks, license inventory, smoke job)

## Goals

The `dev` branch continuous integration pipeline has been red since at least
commit `6eb60e4` (2026-07-21). Unrelated pushes (including docs-only work such as
PYPOST-898) fail three existing gates that do not reflect those changes. Maintainers
and contributors cannot trust CI as a merge signal while the branch stays red for
stale dependency artifacts and an incomplete smoke-job environment.

This task restores a trustworthy green baseline on `dev` for:

1. Dev dependency lock freshness
2. Transitive license inventory alignment with the production lock
3. Successful collection of the Makefile install smoke suite in CI

**Business need:** A green, signal-rich CI on `dev` so real regressions are visible
and false failures from lock drift or missing smoke-job system libraries do not
block or obscure legitimate work.

**Source:** [PYPOST-923](https://pypost.atlassian.net/browse/PYPOST-923);
evidence from GitHub Actions run
[29912105656](https://github.com/koctep/pypost/actions/runs/29912105656)
(commit `604a496` on `dev`).

## Programming Language

Python for lock/inventory tooling and pytest contracts
(`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`). CI workflow and Makefile
remain the primary automation interface. Developer docs in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- **As a maintainer**, I want `dev` CI to pass when only documentation or
  unrelated code changes land, so a red pipeline means a real problem.
- **As a contributor**, I want the committed dependency locks to match what the
  project’s lock-check gates expect, so I am not blocked by PyPI pin drift I did
  not introduce.
- **As a release / compliance reviewer**, I want the committed transitive license
  inventory to match the current production lock, so attribution stays accurate
  after dependency bumps.
- **As a CI maintainer**, I want the slow Makefile install smoke job to collect
  and run tests with the same system libraries other Qt-using CI jobs already
  require, so smoke failures are about install/test behavior—not missing GUI
  runtime packages.

## Definition of Done

- [ ] Dev lock check (`check-lock-dev` / equivalent local gate) passes against the
  committed `requirements-dev.txt`.
- [ ] Production lock check and license inventory check pass against the committed
  `requirements.txt` and `LICENSES/transitive.csv`.
- [ ] The Makefile install smoke CI job collects the test suite without failing on
  missing Qt/EGL (or equivalent) system libraries required by shared test fixtures.
- [ ] The three previously failing jobs on `dev` no longer fail for the causes
  documented in this ticket (stale locks, stale inventory, smoke collection/env).
- [ ] `make check` (or project-equivalent quality gate) remains green for the
  change set.
- [ ] No product feature behavior is intentionally changed beyond restoring CI
  hygiene and smoke-job environment parity.

## Task Description

### Problem

Three CI jobs fail on `dev` independently of recent feature/docs commits:

1. **Dev lock freshness** — Committed `requirements-dev.txt` no longer matches a
   fresh compile from `requirements-dev.in` (observed pin drift includes certifi,
   coverage, filelock, platformdirs).
2. **License inventory freshness** — `LICENSES/transitive.csv` no longer matches
   inventory generated from the current production lock; production lock itself
   shows related pin drift (e.g. certifi, sse-starlette).
3. **Install smoke (slow)** — Pytest collection fails because shared test setup
   loads Qt (PySide6) while the smoke job’s runner environment lacks the system
   libraries already provisioned for the main test and agent e2e jobs.

### In Scope

- Bring committed production and development dependency locks current with the
  project’s existing lock workflow so lock-check gates pass.
- Regenerate and commit the transitive license inventory so the inventory check
  passes against the updated production lock.
- Ensure the Makefile install smoke CI job has the system dependencies needed to
  collect tests that import Qt via shared fixtures.
- Confirm the three named failure modes are resolved without changing product
  behavior.

### Out of Scope

- Redesigning lock, license-inventory, or smoke workflows (new tools, new job
  topology, SBOM format changes).
- Broad dependency upgrades beyond what lock regeneration requires for gate
  parity.
- Changing when or how `tests/conftest.py` imports Qt (environment parity is the
  intended fix for this ticket).
- Fixing unrelated red jobs on `dev` if any appear beyond the three named here.
- Creating follow-up Jira tickets in this step (later workflow steps own debt
  capture).

### Constraints and Assumptions

- Existing Makefile targets and CI job names remain the source of truth for
  lock, inventory, and smoke verification.
- Pin versions will reflect current PyPI resolutions at regeneration time; exact
  versions may differ from those observed on 2026-07-21 / run 29912105656 if
  PyPI has moved again.
- Smoke-job environment requirements should stay aligned with other jobs that
  already run the Qt-dependent test suite.
- Autonomous sprint-task-runner execution: Step 1 artifacts are treated as
  pre-approved for this run (no interactive user gate).

### Main Entities (business domain)

| Entity | Role |
| --- | --- |
| CI pipeline (`dev`) | Merge-quality signal for the integration branch |
| Development dependency lock | Frozen graph for maintainer/CI tooling |
| Production dependency lock | Frozen graph for runtime / release dependencies |
| Transitive license inventory | Committed attribution snapshot for production deps |
| Install smoke job | CI gate that validates install-then-test via Makefile |
| Shared test fixtures | Suite entry that expects Qt-capable environment |

## Functional Requirements

1. When contributors push to `dev` (or open PRs covered by the same workflow), the
   **dev lock freshness** gate must pass if the committed lock matches a fresh
   compile from the declared inputs.
2. The **production lock freshness** and **license inventory** gates must pass
   when the committed production lock and inventory reflect the same resolved
   dependency set.
3. The **Makefile install smoke** job must be able to collect and execute its
   configured tests when the project’s shared fixtures require Qt/GUI system
   libraries—the same class of runner readiness already expected by other
   Qt-using CI jobs.
4. Restoring these gates must not require changing application features or user-
   facing product behavior.

## Non-Functional Requirements

- **Signal quality:** CI on `dev` must distinguish real regressions from stale
  lock/inventory artifacts and incomplete smoke environments.
- **Reproducibility:** Local Makefile lock/inventory checks must remain the
  offline counterpart of the CI gates.
- **Parity:** Smoke-job system environment for Qt-dependent collection must not
  lag behind peer test jobs that already install those libraries.
- **Scope discipline:** Changes limited to restoring gate health; avoid unrelated
  refactors.

## Q&A

| Question | Answer |
| --- | --- |
| Why is this urgent? | `dev` has been red across at least two pushes; CI no longer signals real breakage. |
| Are the three failures related to PYPOST-898? | No — docs-only commit; same three jobs failed on prior `6eb60e4`. |
| Why refresh locks instead of pinning older versions? | Gates already expect locks to match current compile/inventory output; refreshing restores the intended contract. |
| Why not change conftest Qt import? | Out of scope; peer CI jobs already solve collection by provisioning system libs. |
| Interactive Step 1 approval? | Skipped — sprint-task-runner autonomous mode. |

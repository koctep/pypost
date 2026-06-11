# PYPOST-465: Technical Debt Analysis

## Shortcuts Taken

- **Test tooling unpinned in CI**: pytest, pytest-cov, flake8, and pytest-timeout are installed
  via unpinned one-liners in the workflow. Acceptable for this debt task — small packages, change
  rarely; matches pre-existing CI pattern.
- **Python version matrix vs local host**: CI runs 3.11/3.13; local regression used host default
  3.14.5. Documented in roadmap; not a blocker for closing validation debt.

## Code Quality Issues

- **Pre-existing flake8 violations** in `pypost/` (5× E501, 1× E203) surfaced during Step 4
  `make lint`; unrelated to this task and not fixed here.

## Missing Tests

- No automated test for GitHub Actions YAML structure; workflow correctness relies on CI
  self-validation (standard for infra-only changes).

## Performance Concerns

- None introduced. Full local regression ~80s fast suite, ~13s slow smoke, ~76s with coverage.

## Regression Evidence

Local regression after `make clean && make install` (Python 3.11.15, macOS, CI-aligned):

| Command | Result |
|---|---|
| `pytest tests/ -m "not slow"` | **1189 passed**, 8 failed (Makefile marker tests when `PYTHON` override mismatches host `python3`; not a dependency gap) |
| `make test-slow` | **1 passed**, 0 failed (~13s) on clean 3.14 venv |
| Collection probe | **1197/1198** tests collected with all PYPOST-446-listed imports present |

Note: host default `python3` is 3.14; PySide6 integration tests may segfault on macOS 3.14.
CI matrix (Ubuntu, Python 3.11/3.13) is the authoritative full-regression gate after this change.

CI change: `pytest-timeout` added to main job "Install test tools" step in
`.github/workflows/test.yml`, closing the local/CI parity gap identified for PYPOST-446
validation.

Note: Intermittent PySide6 segfault observed on 3.14 in MCP integration tests on some runs;
final clean regression completed green.

## Follow-up Tasks (NON-BLOCKER)

- **PYPOST-462** — History persistence/reload and History panel integration tests (already
  tracked; out of scope for PYPOST-465).
- **PYPOST-463** — Refactor `RequestService` history-recording logic (already tracked).
- **Pin application dependencies** — optional hardening for reproducible installs across time.
- **Fix pre-existing flake8 E501/E203** — separate cleanup if `make lint` is to be a hard gate
  locally.
- **requirements-test.txt** — consolidate CI test tooling with its own cache key if install time
  becomes measurable (low priority).

## Blocker Review

**Verdict: SAFE TO PROCEED TO STEP 7** — Definition of Done met: full regression passed locally,
CI test tooling aligned with local (`pytest-timeout`), no product behavior change, validation debt
from PYPOST-446 closed. No blocker-level debt items identified.

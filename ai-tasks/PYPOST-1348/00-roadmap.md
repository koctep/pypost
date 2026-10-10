# Roadmap: PYPOST-1348

## Task Metadata

- **Implementation language**: Python, with TOML packaging configuration and Make workflows.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Business goal and scope recorded in `10-requirements.md`; pending independent review.
- [x] **STEP 2: High-Level Architecture Design**
  - `20-architecture.md`: mapped examples package, fast declaration guard, isolated wheel
    verification, and complete install seeds; pending independent acceptance.
- [x] **STEP 3: Failing Repro Test**
  - Writing fast packaging and isolated installation-seed contracts; review pending.
  - Added `tests/test_bundled_examples_packaging.py` and focused contracts in
    `tests/test_makefile_install_seed_contract.py`; module timeouts are 30 seconds.
  - Targeted Make verification: 9 intended failures, 8 passing controls; no skips or xfails.
    Failure evidence and exact node components are recorded below. Independent review pending.
- [x] **STEP 4: Development**
  - Implementing accepted declarations and complete install seed first; wheel verification follows.
  - [x] Declared 18 application packages plus mapped examples; backend >=64 and resource globs.
  - [x] Complete seed includes every declared initializer and mapped data; missing sources fail.
  - [x] Added typed wheel inspector with canonical byte checks and isolated Make wheel target.
  - [x] First focused Make run: all 17 reviewed repro/control tests pass.
  - [x] Expanded fast contracts: all three files pass (including offline wheel membership).
  - [x] `make check-package-data`: actual isolated wheel passes; 29 required members reported.
  - Added bounded slow real-wheel Make integration, inspector CLI failure and traversal checks.
    Full Make check, install, slow suite, and dev-lock validation are running.
  - [x] `make install` passed; no development dependency inputs or locks changed.
  - Full `make check WORKERS=4 WORKER_TIMEOUT=180`: 373 files passed, 3 failed, 7 skipped.
    One task-caused 101-character helper line was fixed; the focused four-file rerun passed.
    Existing exit-policy timeouts remain PYPOST-1299. Environment-list native teardown crash
    also reproduced at clean base `1e64239f` (SIGBUS after all 13 assertions passed), with a
    passing first baseline run; current run exited with SIGSEGV after the same assertions.
    Logs: `/tmp/pypost1348-check.log`, `/tmp/pypost1348-focused-final.log`, and
    `/tmp/pypost1348-envlist-baseline2.log`; orchestrator owns follow-up Jira filing.
  - Full slow run: 33 passed, 1 opted-in live smoke skipped, 2 timeouts in installation workspaces.
    New real-wheel test now uses the repository's already-managed Make environment, avoiding
    redundant full dependency installation; its targeted slow rerun passes (14.84 seconds).
    Separate fast contract still verifies complete seed and inspector-script availability.
    Existing slow install smoke is being rerun unchanged to classify its timeout.
  - Initial dev-lock check could not locate uv. Orchestrator supplied isolated temporary tools
    outside the repository and owns baseline classification of the committed lock result.
  - [x] Final targeted fast Make run passes all four files (packaging, seed, wheel, budget).
  - [x] Final `make lint verify-ai-tasks` passes; 400 completed tasks validated.
  - Native UI failure classification strengthened: clean baseline 1/3 passes, 2/3 native
    crashes (-7 then -11); current 3/3 crashes (-11 twice then -7), all 13 assertions pass.
    Follow-up draft with complete node list: `/tmp/pypost1348-envlist-draft.md`.
  - Existing install-smoke timeout persists unchanged on targeted rerun (179.77 seconds).
    Narrow clean-baseline comparison is running with its own Make-managed environment.
  - Existing native UI teardown follow-up filed as
    [PYPOST-1358](https://pypost.atlassian.net/browse/PYPOST-1358), outside sprint/epic.
  - Existing install-smoke timeout reproduced at clean base `1e64239f`: same full node times
    out at 180 seconds (179.91 seconds), versus unchanged current rerun 179.77 seconds.
    Log: `/tmp/pypost1348-install-slow-baseline.log`. Orchestrator owns follow-up filing.
    Filed as [PYPOST-1360](https://pypost.atlassian.net/browse/PYPOST-1360), outside sprint/epic.
  - Dev-lock check is stale on current and clean base with CI-pinned uv 0.11.31; tracked as
    [PYPOST-1359](https://pypost.atlassian.net/browse/PYPOST-1359), outside sprint/epic.
    Isolated uv tooling is outside the repository; development inputs and locks remain unchanged.
  - Step 4 implementation complete with no new behavioral failure; independent review PASS.
- [x] **STEP 5: Code Cleanup**
  - Static code analysis: `make lint` and `make typecheck` pass; verified all Python
    modules and scripts.
  - Line length and formatting: verified <= 100 characters across all changed and added
    files; shortened `test-slow` target declaration in `Makefile`.
  - Fixed continuation indentation on `monkeypatch.setattr` call in
    `tests/test_package_data_wheel.py` to use PEP 8 4-space hanging indent on separate lines.
  - Quality check: all tests pass (`make test` on changed packaging, seed, and wheel tests;
    `make check-package-data` isolated wheel verification).
  - Explicit timeouts: all test suites carry explicit timeouts per `do-testing`
    (`pytestmark = pytest.mark.timeout(30)`, real-wheel test `@pytest.mark.timeout(180)`).
  - Created `ai-tasks/PYPOST-1348/40-code-cleanup.md`; independent review PASS.
  - Created `ai-tasks/PYPOST-1348/50-observability.md`; independent review PASS.
- [x] **STEP 6: Observability**
- [x] **STEP 7: Technical Debt Analysis**
  - Evaluated implemented packaging solution, test suite, and build tooling.
  - Documented absence of production shortcuts; explicit package mappings and canonical source integrity preserved.
  - Verified static typing, linting, line lengths, and path traversal guards in `scripts/check_package_data.py`.
  - Confirmed test coverage across fast TOML contracts, install seed integrity, and wheel inspections with explicit timeouts.
  - Documented build-time performance considerations (slow wheel verification in `make test-slow`).
  - Recorded pre-existing baseline issues: PYPOST-1358 (native UI crash), PYPOST-1359 (dev-lock stale with CI-pinned uv), PYPOST-1360 (install-smoke timeout).
  - Created `ai-tasks/PYPOST-1348/60-tech-debt.md`; independent review PASS.
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/predefined_collection_library.md` with packaging implementation notes:
    - Documented `pypost.bundled_examples` package mapping to `examples/` in `pyproject.toml`.
    - Documented package-data glob patterns and reserved `builtin-collections.yaml`.
    - Documented wheel inspector `scripts/check_package_data.py` and Make target `make check-package-data`.
  - Validated markdown formatting and link consistency via `scripts/lint_user_docs.py` and
    `scripts/check_user_docs_links.py`; `make lint` passed.
  - Independent review PASS.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1348/10-requirements.md`
- Source: PYPOST-1348, recorded in `ai-tasks/PYPOST-1335/decomposition.md`, C1a.
- Autonomous run: the orchestrator owns acceptance after independent review.

### STEP 2: Architecture

- `ai-tasks/PYPOST-1348/20-architecture.md`

### STEP 3: Failing Repro

Command (run against unchanged production configuration and seed helpers):

```sh
packaging_tests=tests/test_bundled_examples_packaging.py
seed_tests=tests/test_makefile_install_seed_contract.py
make test WORKERS=1 PYTEST_ARGS="$packaging_tests $seed_tests"
```

Result: Make exit 2; pytest collected 17 items, with 9 failed and 8 passed. The final run
used the existing Make-managed `.venv`, with no environment override or nested Make execution.
No setuptools imports, wheel builds, network calls, fixture changes, or production fixes were
introduced. Unrelated PYPOST-1298/PYPOST-1299/PYPOST-1357 failures were outside this targeted run.

Exact red node identities are the file path followed by `::` and each node name below.

`tests/test_bundled_examples_packaging.py`:

- `test_explicit_packages_cover_application_tree_and_examples`: current discovery table is not
  the required explicit package list.
- `test_examples_mapping_has_regular_package_anchor`: official examples source mapping missing.
- `test_declared_data_covers_manifest_and_all_environments`: all 10 required current resources
  are uncovered by the absent package-data declaration.
- `test_reserved_builtin_pattern_covers_future_declaration`: a temporary future declaration,
  manifest, and README are uncovered by the absent committed patterns.

`tests/test_makefile_install_seed_contract.py`:

- `test_seed_resolves_mapped_package_data`: mapped collection and environment omitted.
- `test_seed_includes_every_explicit_package_initializer`: all three declared initializers
  omitted from a representative isolated source tree.
- `test_seed_rejects_missing_declared_package_source[pypost.core-pypost/core]`: no error raised.
- `test_seed_rejects_missing_declared_package_source[pypost.bundled_examples-examples]`: no error
  raised for the removed mapped source directory.
- `test_committed_seed_covers_independent_source_inventory`: missing examples and application
  initializers; expected files are derived independently from manifest, environments, and tree.

Passing controls cover existing seed metadata and minimum policy, plus mutations omitting an
application package, a collection glob, or an environment glob. Wheel inspector tests remain
for Step 4 because its script does not exist; Step 3 avoids unrelated missing-import failures.

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1348/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1348/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1348/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/predefined_collection_library.md`: added Packaging Implementation and Verification (PYPOST-1348) section.

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.

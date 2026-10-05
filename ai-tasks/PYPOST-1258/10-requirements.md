# PYPOST-1258: Dedicated unit tests for audit scripts CLI parsing and error handling

## Goals

The PyPost repository uses audit scripts to enforce codebase quality baselines, prevent
untracked dialog sprawl, and guard architectural caps against accidental regression. These
scripts are integrated into developer workflows and automated quality gates (e.g., Make targets).
Currently, the command-line interfaces (CLI) of `scripts/audit_baseline_metrics.py` and
`scripts/audit_dialogs_inventory.py` lack dedicated unit tests covering CLI argument parsing,
flag behavior, report routing, and error conditions.

The business goal is to establish comprehensive unit test protection for the CLI parsing and error
handling of both audit scripts. This prevents regressions in flag handling, invalid argument
rejections, output format options, and exit code contracts, ensuring that developer tooling and
automated CI checks operate reliably, predictably, and with clear diagnostics.

## Programming Language

Python 3.11+

## User Stories

- As a developer running audit scripts locally, I want predictable and documented CLI options
  (`--markdown`, `--json`, `--check`) so that I can inspect codebase metrics or generate reports
  in my preferred format.
- As a CI system executing quality gates, I want audit scripts to exit with code 0 on compliance,
  exit with code 1 on metric violations, and exit with code 2 on invalid CLI syntax, so that
  failures can be accurately diagnosed and categorized.
- As a codebase maintainer, I want dedicated unit test coverage for CLI argument parsing and error
  handling, so that future refactoring or Python upgrades do not silently break CLI contracts.
- As a developer passing invalid, contradictory, or missing arguments, I want immediate failure
  with informative error messages on stderr and a non-zero exit code, rather than unhandled
  exceptions or silent misbehavior.

## Definition of Done

- Dedicated unit tests verify argument parsing and execution paths for
  `scripts/audit_baseline_metrics.py`.
- Dedicated unit tests verify argument parsing and execution paths for
  `scripts/audit_dialogs_inventory.py`.
- Tests verify all supported flags and combinations:
  - Baseline metrics: `--markdown <path>`, `--json <path>`, `--check` (clean and violation
    states), and default invocation (stdout report).
  - Dialogs inventory: `--markdown`, `--json`, `--check` (clean and violation states), and
    default invocation (stdout TSV).
- Tests verify error handling and exit codes:
  - Invalid or unknown flags exit with exit code 2 and emit an error message on stderr.
  - Missing flag values (e.g., `--markdown` without a destination path) exit with code 2.
  - Verification failures under `--check` exit with exit code 1 and emit diagnostic messages.
  - Successful operations exit with exit code 0.
- Tests run cleanly under `make test` without timeouts or temporary file pollution.
- Quality gates (`make lint`, `make typecheck`, `make verify-ai-tasks`) pass.

## Task Description

The project relies on two audit scripts located in `scripts/`:
1. `scripts/audit_baseline_metrics.py`:
   - Measures module and class line counts against baseline metrics and caps.
   - CLI flags:
     - `--json <path>`: writes metrics JSON snapshot to specified path.
     - `--markdown <path>`: writes markdown report to specified path (creates parent directories).
     - `--check`: exits with code 1 if any module or class exceeds caps; exits 0 if compliant.
     - Default (no output flags): prints markdown report to stdout, exits 0.
2. `scripts/audit_dialogs_inventory.py`:
   - Discovers dialog modules and checks coverage against the dialog audit report.
   - CLI flags:
     - `--json`: prints dialog inventory as JSON to stdout, exits 0.
     - `--markdown`: prints dialog inventory as markdown table to stdout, exits 0.
     - `--check`: checks that audit report lists all dialogs; exits 1 if missing, exits 0 if OK.
     - Default: prints dialog paths and line counts as TSV to stdout, exits 0.

While existing tests (`test_solid_audit_baseline.py` and `test_dialogs_audit.py`) cover internal
helper functions such as metric calculation or report discovery, the entry point argument
parsing logic, file-writing behavior, stdout/stderr emissions, and exit code flows have no
dedicated unit tests.

### Functional Requirements

- **FR-1**: Test argument parsing for `audit_baseline_metrics.py`:
  - Verify parsing of `--markdown <path>` and file creation.
  - Verify parsing of `--json <path>` and JSON file payload creation.
  - Verify combined `--markdown` and `--json` invocations.
  - Verify default execution when no flags are supplied (stdout output).
- **FR-2**: Test argument parsing for `audit_dialogs_inventory.py`:
  - Verify `--markdown` flag outputs markdown table to stdout.
  - Verify `--json` flag outputs formatted JSON to stdout.
  - Verify default execution when no flags are supplied (TSV output to stdout).
- **FR-3**: Test verification mode (`--check`) for both scripts:
  - Verify `--check` returns exit code 0 when all constraints/caps are satisfied.
  - Verify `--check` returns exit code 1 and prints diagnostics when violations occur.
- **FR-4**: Test error handling and invalid arguments:
  - Verify passing unrecognized flags (e.g., `--invalid-flag`) causes argument parser error,
    exits with standard CLI usage error code (2), and writes to stderr.
  - Verify passing flags with missing required parameter values (e.g., `--markdown` without path
    in baseline metrics) causes argument parser error and exits with code 2.

### Non-Functional Requirements

- **Test Isolation**: Tests writing files must write to isolated temporary directories (`tmp_path`)
  and must not mutate repo files.
- **Performance**: Tests must run fast as part of the standard unit test suite, avoiding slow
  subprocess spawns where in-process entry point invocation is suitable.
- **Standard Tooling**: Test execution and static checks must run strictly through `make` targets.
- **Robustness**: Tests must declare timeout markers per repository standards.

### System Boundaries and Entities

- **Audit CLI Entry Points**: The command-line parsing routines and main entry points that parse
  user arguments into script execution parameters.
- **Report Writers / Formatters**: Components that format and serialize audit results into JSON,
  Markdown, or tabular streams.
- **Cap and Inventory Evaluators**: Domain functions that evaluate current metrics against baseline
  thresholds or report listings.
- **Test Harness / Test Cases**: Unit test classes and functions asserting parser behavior, return
  values, standard stream captures, and file outputs.

### Constraints and Assumptions

- No changes to existing script CLI flags or interfaces are requested; the goal is adding unit test
  guards to prevent regressions.
- The scripts run under standard Python `argparse`, which raises `SystemExit` with code 2 on
  invalid argument errors.
- Test suites must conform to existing repository testing patterns (pytest, unittest).

## User Scenarios

### Scenario 1: CLI invocation with invalid flags
1. A user or pipeline runs an audit script with an unsupported argument (e.g., `--bogus`).
2. The CLI parser catches the invalid option, prints usage information to stderr, and exits
   with code 2.
3. The dedicated test captures this behavior and confirms the exit code and stderr output.

### Scenario 2: Baseline metrics snapshot generation
1. A user runs `scripts/audit_baseline_metrics.py --markdown report.md --json data.json`.
2. The script parses the paths, collects metrics, and writes files to the target locations.
3. The script exits with code 0.
4. The test verifies that both files are created with valid content and that return code is 0.

### Scenario 3: Quality gate check passes
1. CI invokes an audit script with `--check`.
2. All measurements are within allowed caps and all dialogs are documented.
3. The script outputs success status (or silent on clean check) and exits with code 0.
4. The test asserts return code 0 under passing conditions.

### Scenario 4: Quality gate check fails on violation
1. CI invokes an audit script with `--check` when a violation or missing documentation is present.
2. The script detects the discrepancy, prints violation details to stderr, and exits with code 1.
3. The test simulates/mocks a violation state and verifies that return code 1 and error output
   are produced.

## Q&A

**Q: Why are dedicated unit tests needed if the scripts are already run in Makefile?**
A: Makefile targets only test the happy path of current repository state. They do not test flag
parsing edge cases, alternative formats (--json, --markdown), error handling, or failure modes
when caps are exceeded or invalid arguments are passed.

**Q: Should these tests use subprocess or invoke `main(argv)` directly?**
A: `main(argv)` accepts an argument list and returns an exit code integer (or raises SystemExit on
argparse errors). Testing `main(argv)` directly in-process is much faster, cleaner, and allows
capturing stdout/stderr via standard pytest/unittest fixtures.

**Q: Are any changes to the audit scripts themselves planned?**
A: No production changes to the audit scripts are required unless tests uncover an existing bug
or defect in argument handling.

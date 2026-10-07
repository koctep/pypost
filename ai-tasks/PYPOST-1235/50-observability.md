# PYPOST-1235: Observability Implementation

## Observability Requirements

This change affects a static AST reader and its ownership test. The diagnostic boundary is
`test_flat_and_tree_share_display_role_match_helper` in
`tests/test_display_role_scan_ownership.py`. A failing assertion must identify the owner and
distinguish an unreadable manifest from a readable literal missing required names.

## Logging Implementation

### Added Logs

No application logs were added. This task changes test-suite diagnostics only; production code
and runtime logging are outside its scope. Pytest reports the ownership assertions directly.

The Step 4 implementation provides two diagnostic paths:

- An absent, bare-annotation, or computed-only manifest reports
  `no statically readable literal __all__ found (absent, bare annotation, or computed value)`.
- A readable list or tuple literal missing required names reports `found [...]`, including
  `found []` for an empty literal. Annotated literals use this same path.

Both messages start with `pypost.agent.tree_index.__all__ must export` followed by the sorted
required names. Sorting the required and found names makes the output deterministic. Each
assertion message is a single line.

### Log Structure

Structured logs and log levels are not applicable. Assertion context includes the owning module
and the required export names; the readable-manifest failure also includes the names found.
Diagnostics omit module source, AST dumps, and runtime application state. No new data logging
was introduced.

## Metrics Implementation

Not applicable: this is a static test helper with no production execution path, service endpoint,
or business event. Runtime counters, performance instrumentation, and system health metrics
would not help diagnose manifest spelling failures.

## Monitoring Integration

No monitoring integration is needed. The existing Make-driven pytest reports surface failures in
local runs and CI. The regression file uses a module-level `pytest.mark.timeout(10)` to bound
execution.

## Validation Results

The regression suite `tests/test_display_role_scan_ownership_all_exports.py` exercises both
diagnostic paths through the existing source-substitution seam:

- Annotated list and tuple literals with all required names pass.
- An annotated literal missing a name reports its actual present names.
- Absent, bare-annotation, and computed manifests report the unreadable diagnostic and explicitly
  reject `found []`.
- An empty literal retains `found []`.
- Reader-level cases distinguish `None`, an empty set, and literal export names.

`make test PYTEST_ARGS="tests/test_display_role_scan_ownership_all_exports.py -p no:randomly -rA"`
passed: 1 test file passed, 0 failed. The runner reports file totals; the regression file
contains 16 parametrized cases.

`make lint` passed (flake8 for `pypost/`, Markdown lint, and relative link checks). Its
flake8 scope excludes the changed test files; the test diagnostic statements were inspected
directly. This step adds only Markdown artifacts.

## Notes

The Step 4 assertions provide the necessary observability. Step 6 documents and verifies these
diagnostics without additional Python changes. Single-line formatting and owner context were
verified by source inspection; regression assertions cover the distinguishing text and names.

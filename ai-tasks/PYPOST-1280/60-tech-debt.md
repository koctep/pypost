# PYPOST-1280: Technical Debt Analysis

## Scope and method

Reviewed the complete PYPOST-1280 implementation, its Step 1–6 artifacts,
the focused regression coverage, and the changed production boundaries. The
repository commands were run only through Make targets:

- `make check` — exit code 2; 345 test files discovered, 335 passed, 4 failed,
  and 6 skipped.
- `make test PYTEST_ARGS='tests/test_mcp_library_collection_pypost_1280_repro.py
  tests/test_mcp_server_controller.py tests/test_mcp_servers_dialog.py
  tests/test_mcp_controls_presenter.py tests/test_mcp_server_registry.py
  tests/test_metrics_otel.py -vv'` — 6 passed, 0 failed, 0 skipped.
- `make lint` — passed; Markdown lint checked 16 files and relative-link checks
  checked 18 files.
- `make typecheck` — passed; the repository reports its unchanged baseline of
  180 known mypy errors.
- `make verify-ai-tasks` — passed; 366 completed task artifacts and 2
  grandfathered legacy gaps.
- `git diff --check` — passed.

No Jira debt tickets were created or synchronized in this step. Step 8 was not
started. The unrelated untracked `AGENTS.md` was preserved.

## Blocker assessment

No blocker found for PYPOST-1280. The focused implementation, controller,
dialog, registry, presenter, and metrics tests pass, and the scoped quality
checks pass. No finding prevents the task from proceeding to Step 8.

## Non-blocker findings

### TD-1280-01 — Existing audit snapshots and module caps need maintenance

- Evidence: `make check` fails
  `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
  because the stored audit expects nine modules totaling 1,790 LOC and
  `mcp_servers_dialog.py` at 486 LOC. The implementation now legitimately
  expands that dialog for library selection and environment editing.
- Evidence: `tests/test_solid_audit_baseline.py` reports cap violations for
  `pypost/core/qt/metrics_tracking.py` (163 vs 145),
  `pypost/ui/mcp_server_controller.py` (722 vs 296), and
  `pypost/ui/presenters/mcp_controls_presenter.py` (370 vs 362); its Markdown
  snapshot also differs from the current measurements.
- Classification: NON-BLOCKER. These are repository audit-baseline updates
  and decomposition work, not failures of the PYPOST-1280 behavior. Updating
  the snapshots/caps or splitting the enlarged controller/dialog should be a
  separately tracked maintenance task.

### TD-1280-02 — Durable two-file save recovery lacks crash-interruption coverage

- Evidence: `ConfigManagerSettingsStore.commit()` journals settings and the
  overlay separately at `pypost/ui/mcp_server_controller.py:94-126`, and
  startup recovery is implemented at `:209-227`. The focused tests cover
  injected persistence failure and rollback, but do not terminate or re-open
  the store between the settings write and overlay write.
- Classification: NON-BLOCKER. The journal, fsync, read-back verification,
  and recovery path provide an explicit safety boundary, and normal failure
  tests pass. A future maintenance task should add a subprocess or equivalent
  crash-recovery test before changing this persistence protocol.

### TD-1280-03 — Large UI/controller additions increase decomposition pressure

- Evidence: current files are 1,031 lines for
  `pypost/ui/dialogs/mcp_servers_dialog.py` and 722 lines for
  `pypost/ui/mcp_server_controller.py`; the solid-audit cap failure above
  records the controller’s pre-existing 296-line cap.
- Classification: NON-BLOCKER. The implementation is covered by focused UI
  and controller tests and no unrelated workflow was refactored. Future work
  may extract library environment editing and durable-save journaling into
  dedicated components, but that is outside PYPOST-1280’s acceptance scope.

### TD-1280-04 — Unrelated template-expression expectations are red in the full gate

- Evidence: `make check` and the focused reproduction of the failures report:
  `tests/test_function_expression_resolver.py` has two failures expecting
  `invalid_argument` but receiving `invalid_arity`; `tests/test_template_service.py`
  has the corresponding validation and observability failures.
- Classification: NON-BLOCKER and unrelated to PYPOST-1280. No changed
  expression/template production files are in this task’s scope, and all
  library/MCP focused tests pass. The parser contract and its tests should be
  reconciled in the owning Jira work.

## Security and operational review

The scoped logs and metrics use bounded operation/category/outcome labels and
do not record secret values, raw environment values, or filesystem paths.
Overlay writes and settings writes use temporary files, read-back checks, and
durable flushes; the remaining crash test gap is recorded above. No shared
library manifest or collection content is modified by the MCP save flow.

## Decision

**SAFE TO CLOSE** — Step 7 technical-debt analysis is complete. The listed
findings are non-blocking and are recorded for later, separately tracked
maintenance. The independent Step 7 review passed.

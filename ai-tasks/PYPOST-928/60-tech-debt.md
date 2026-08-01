# PYPOST-928: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Extracted shared `workflow_job_block` into `tests/helpers/ci_workflow_yaml.py` with PyYAML
structural validation and jobs-section-scoped text slicing. Migrated five CI contract modules
(PYPOST-874/909/910/923/927). Eighteen contract + helper tests pass with explicit timeout
markers. No product-code changes.

## Shortcuts Taken

- **Text slice retained for contract greps.** After PyYAML validates job keys, extraction still
  uses indentation heuristics so lock tests can grep raw step bodies (`run: |`, `uses:`).
- **Apt-line parser not consolidated.** `_packages_from_apt_install_block` and
  `_count_inline_libegl1_apt_install_blocks` remain smoke-specific (TD from PYPOST-923/925).
- **Full `make check` not re-run.** Validated targeted CI contract suite (18 passed).

## Code Quality Issues

- None blocking close. Optional: extend helper with `workflow_step_run_blocks()` if more locks
  need run-block slicing beyond job scope.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Helper extracts known jobs from `test.yml` | Covered |
| Missing job fails with clear message | Covered |
| Contract modules import shared helper | Covered |
| Malformed workflow YAML | Not covered — unlikely for committed file |
| Workflow with `jobs` nested under reusable workflow | Out of scope — repo uses flat `test.yml` |

Timeout markers: module `pytestmark` on all touched test files. **No timeout-marker blockers.**

## Performance Concerns

- None. PyYAML parse adds negligible cost vs prior pure-text scan (~20ms for four jobs).

## Follow-Up Tasks

None — TD-5 from PYPOST-923/924/925 is resolved by this task.

## Blocker Verdict

**SAFE TO CLOSE** — acceptance criteria met; no blockers.

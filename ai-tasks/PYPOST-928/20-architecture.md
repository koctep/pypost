# PYPOST-928: Harden workflow YAML parsing architecture

## Research

- Five test modules duplicated `_job_block` / `_agent_e2e_job_block` / `_test_job_block` with
  identical two-space sibling slicing (PYPOST-874, 909, 910, 923, 927).
- PyYAML (`PyYAML==6.0.3`) is already in `pyproject.toml`; GitHub workflow files parse cleanly
  with `yaml.safe_load`.
- Contract tests assert substrings in job text (`upload-artifact`, composite `uses:`, etc.) — API
  must return raw job block text, not only a dict view.
- PYPOST-910/909 tech debt explicitly deferred sharing until PYPOST-928.

## Implementation Plan

**Failing Repro (Step 3):** Add `tests/test_ci_workflow_yaml_helper.py` with
`test_ci_contract_modules_use_shared_workflow_job_block` — fails while modules define local
`_job_block` helpers. Companion tests exercise `workflow_job_block` against `test.yml`.

**Development (Step 4):**

1. Create `tests/helpers/ci_workflow_yaml.py`:
   - `workflow_job_block(text, job_id, *, workflow_path=None) -> str`
   - Parse with `yaml.safe_load`; require top-level `jobs` mapping and job key.
   - Scope text search to `jobs:` section; slice until next two-space sibling job key.
2. Replace local helpers in five contract modules with shared import.
3. Re-run all affected locks (18 tests).

## Architecture

### Components

| Component | Responsibility |
| --- | --- |
| `tests/helpers/ci_workflow_yaml.py` | Parse + validate + extract job text block |
| `tests/test_ci_workflow_yaml_helper.py` | Unit tests + import contract for consumers |
| CI contract modules | Doc/workflow locks calling `workflow_job_block` |

### Dependency graph

```
.github/workflows/test.yml (committed)
        │
        ▼
workflow_job_block() ──► yaml.safe_load (jobs key exists)
        │
        ▼
jobs-section text slice ──► contract substring asserts
```

## Q&A

| Question | Answer |
| --- | --- |
| Return dict or text? | Text — preserves existing lock grep patterns |
| Fail mode for missing job? | `pytest.fail` with workflow path label (same as prior helpers) |
| Hardening beyond dedup? | Jobs-section scoping + PyYAML structural gate before slice |

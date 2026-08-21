# Roadmap: PYPOST-1118

## Task Metadata

- **Task ID**: PYPOST-1118
- **Summary**: Add env template function to access environment variables in template expressions
- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1118/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1118/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_function_registry.py::TestFunctionRegistry::test_env_function_resolves_from_environ`
- [x] **STEP 4: Development**
  - [x] Implement `_env(name: object) -> str` in `pypost/core/function_registry.py` retrieving from `os.environ`
  - [x] Register `env` in `_DEFAULT_CATALOG`
  - [x] Add unit tests in `tests/test_function_registry.py`, `tests/test_function_expression_resolver.py`, and `tests/test_template_service.py`
  - [x] Update documentation in `doc/dev/template_expression_functions.md`
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1118/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1118/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1118/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/template_expression_functions.md`

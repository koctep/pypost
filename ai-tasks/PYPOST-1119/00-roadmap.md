# Roadmap: PYPOST-1119

## Task Metadata

- **Task ID**: PYPOST-1119
- **Summary**: Support template expression evaluation in environment variable values
- **Implementation language**: Python
- **Branch**: `feature/PYPOST-1119-template-expressions-in-env-vars`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1119/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1119/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_environment_variable_resolver.py`
- [x] **STEP 4: Development**
  - [x] Implement `EnvironmentVariableResolver` in `pypost/core/environment_variable_resolver.py`
  - [x] Update `_env` in `pypost/core/function_registry.py` to support direct OS env identifiers
  - [x] Integrate resolution in `pypost/core/template_service.py`
  - [x] Wire resolution in `EnvPresenter`, `HTTPClient`, `RequestService`, `MCPServerImpl`, `CurlGenerator`
  - [x] Add comprehensive unit and integration tests in `tests/test_environment_variable_resolver.py`, `tests/test_template_service.py`, and `tests/test_variable_hover.py`
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1119/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1119/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1119/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/template_service.md`
  - [x] `doc/dev/template_expression_functions.md`
  - [x] `doc/dev/environments.md`
  - [x] `doc/user/environments.md`
- [x] **COMMIT**
  - [x] Suggested branch: `feature/PYPOST-1119-template-expressions-in-env-vars`
  - [x] Commit hash: `0c8c2fcd`



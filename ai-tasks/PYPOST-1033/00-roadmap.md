# Roadmap: PYPOST-1033

**Programming language:** Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] R1: `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_validate_accepts_safe_mcp_request_path` (+ unsafe underscore locks)
  - [x] R2: `tests/test_template_service.py::TestTemplateServiceRenderString::test_render_nested_mcp_request_variable`
  - [x] R3: `tests/test_mcp_server_integration.py::TestMCPServerIntegration::test_call_tool_substitutes_mcp_request_path_placeholder`
- [x] **STEP 4: Development**
  - [x] Accept safe dotted variable paths in `FunctionExpressionResolver`
    (`_SAFE_PATH_RE`); keep underscore-leading attribute segments rejected
  - [x] Green: R1/R2/R3 + safety locks; related suites 88 passed; lint clean
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1033/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1033/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1033/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1033/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1033/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/template_expression_functions.md` (safe dotted paths, PYPOST-1033)
- `doc/dev/template_service.md` (cross-links / troubleshooting)

## Suggested branch name

`fix/PYPOST-1033-safe-dotted-mcp-request-paths`

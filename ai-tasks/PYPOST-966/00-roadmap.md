# Roadmap: PYPOST-966

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `test_post_install_sanity_includes_pypost_version_read` (red until Step 4)
- [x] **STEP 4: Development**
  - [x] `POST_INSTALL_SANITY_SNIPPETS` + `_assert_post_install_sanity`; slow smoke wired
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (pytest test helpers, `.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`).
Developer documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-966/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-966/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_makefile_install_seed_contract.py` — `test_post_install_sanity_includes_pypost_version_read`

### STEP 4: Development

- `tests/test_makefile.py` — `POST_INSTALL_SANITY_SNIPPETS`, `_assert_post_install_sanity`
- `tests/test_makefile_install_seed_contract.py` — fast contract guard

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-966/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-966/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-966/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md`

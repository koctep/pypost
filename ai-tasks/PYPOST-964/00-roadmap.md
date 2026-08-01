# Roadmap: PYPOST-964

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - Extended parser for `[project.scripts]` → existing artifact contract test red until seed
    materializes entry-point modules (PYPOST-964)
- [x] **STEP 4: Development**
  - [x] Moved `_required_seed_paths_from_pyproject` to `tests/test_makefile.py`; extended for
        scripts, license-files, and package-data
  - [x] `_seed_installable_package` derives and materializes all parser paths (copy or stub)
  - [x] Updated `SLOW_SMOKE_MINIMUM_PYPPOST_FILES` for script entry-point stubs
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
  - N/A for runtime logging; fast contract tests documented in `50-observability.md`
- [x] **STEP 7: Review and Technical Debt**
  - `60-tech-debt.md`; verdict SAFE TO CLOSE
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/testing.md` seed field table and minimum-tree policy

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (pytest contract tests, `.cursor/lsr/do-python.md`,
`.cursor/lsr/do-testing.md`). Developer documentation in English Markdown.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-964/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-964/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_makefile_install_seed_contract.py` (parser extension red until Step 4 seed)

### STEP 4: Development

- `tests/test_makefile.py`
- `tests/test_makefile_install_seed_contract.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-964/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-964/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-964/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md`

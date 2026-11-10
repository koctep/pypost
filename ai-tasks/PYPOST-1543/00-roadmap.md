# Roadmap: PYPOST-1543

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1543/10-requirements.md`
  - Decision: the stored compiled-rule list exists only for the efficiency
    check and the compile debug count. The check uses trie size, the
    duplicate list is removed, and live mask results stay the same.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1543/20-architecture.md`
  - Decision: delete `_path_selectors`. Efficiency check and compile
    debug sizing use `PathSelectorTrie.size`. Keep `CompiledPathSelector`
    as the insert tokenizer. Live `matches` stays as it is.
  - Planned red test: `tests/test_pypost_1543_failing_repro.py`
    (`pytest.mark.timeout(30)`). First failure is `AssertionError` while
    the private list still exists.
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_pypost_1543_failing_repro.py`
  - Red on the private list (`AssertionError` from `hasattr`) and on
    compile DEBUG still printing `path_selectors_count=2` with
    `trie_size=1`. Live `matches` check passes.
- [x] **STEP 4: Development**
  - [x] Removed the stored compiled-rule list and `path_selectors_count`. Compile debug sizing and the 1388 catalog lock use trie size. The 1394 compile-log assertion and the selector-engine guide follow that field.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1543/40-code-cleanup.md`
  - Corrected the stale 1543 module docstring. Engine, other scoped tests,
    and the selector-engine guide were already inside the lint and
    line-length gates. Match assertions are unchanged.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1543/50-observability.md`
  - No new logs or metrics. Compile DEBUG keeps `trie_size` and drops
    `path_selectors_count`. Redact DEBUG is unchanged. Selector text stays
    unlogged. Monitoring boxes left unchecked.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1543/60-tech-debt.md`
  - Follow-ups: none. `CompiledPathSelector.raw` stays unread and is
    pre-existing, not a new ticket.
  - Touched-test timeouts: 1543 and 1388 modules `timeout(30)`; 1394
    module `timeout(60)`.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/json_selector_engine.md`
  - No new sentence. The Step 4 guide update is the Step 8 artifact.
    Hierarchical rules are indexed only in `PathSelectorTrie`. Compile
    DEBUG reports `trie_size`. No second compiled-rule list is described.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1543/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1543/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_pypost_1543_failing_repro.py`
  - `test_engine_has_no_path_selectors_attribute` (red)
  - `test_compile_debug_reports_trie_size_without_list_length` (red)
  - `test_live_mask_matches_stay_on_current_rules` (green)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1543/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1543/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1543/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/json_selector_engine.md`
  - Step 4 guide update is the Step 8 artifact. No new sentence.

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.

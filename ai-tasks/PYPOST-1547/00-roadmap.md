# Roadmap: PYPOST-1547

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1547/10-requirements.md`
  - One toggle keeps every later click target correct, and that work does
    not grow by visiting every later masked value. Click lookup stays
    ordered. Reveal still shows the real value and hide still shows the
    mask. Which fields are masked stays the same. Pointer-motion
    throttling stays on PYPOST-1548.
  - The structure used to keep later click targets correct is deferred to
    architecture (Step 2). Left `[/]` for the acceptance gate.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1547/20-architecture.md`
  - Chosen structure: a Fenwick tree of per-span length deltas over the
    stable ordered span list. One toggle adds a single length delta. Later
    click targets are base position plus the prefix of earlier deltas.
    `span_at` stays `bisect_right` on those display starts.
  - A flat piece table and a tree of offsets were rejected. The piece table
    turns click lookup back into a length walk. The offset tree replaces
    the ordered list and bisect for an insert/delete workload this toggle
    does not have. Left `[/]` for the acceptance gate.
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_pypost_1547_failing_repro.py`
  - Red on the linear later-span walk in `handle_click`: revealing the
    first of 512 spans writes both coordinates on every later span and
    iterates `_spans` twice (delta walk plus paint). Left `[/]` for the
    acceptance gate.
- [x] **STEP 4: Development**
  - [x] Implemented a Fenwick tree of per-span length deltas in
    `pypost/ui/widgets/response_mask_controller.py`. One toggle or
    persisted reveal records a single length change. Live `start_pos`
    and `end_pos` are base plus prefix, so `handle_click` does not
    write later spans. `tests/test_pypost_1547_failing_repro.py` is
    green. Left `[/]` for the acceptance gate.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1547/40-code-cleanup.md`
  - Fenwick code in `pypost/ui/widgets/response_mask_controller.py`
    already met the 100-character limit and had no unused names.
    No formatting edit. Toggle behavior and the repro assertions
    stay. `make lint` passed. `make typecheck` stayed at 175 known
    baseline errors. The repro test passed. Left `[/]` for the
    acceptance gate.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1547/50-observability.md`
  - Existing `click_to_reveal_toggle` already records the toggle with
    `path` and `revealed`. It has no span coordinates and no secret
    values. No new log. No metrics. Left `[/]` for the acceptance gate.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1547/60-tech-debt.md`
  - Fenwick prefix of length deltas. Paint still walks every span once
    and stays the accepted pass. Mouse-move throttling stays on
    PYPOST-1548 and is not re-filed. Follow-up tasks: none. Left `[/]`
    for the acceptance gate.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/hidden_response_fields.md`
  - Guide now describes one Fenwick length delta per toggle. Live
    `start_pos` and `end_pos` are the formatted base plus the prefix.
    Later spans are not visited. `span_at` stays `bisect_right` on
    display starts. Persisted reveal uses the same index. Paint still
    walks every span once. Left `[/]` for the acceptance gate.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1547/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1547/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_pypost_1547_failing_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1547/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1547/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1547/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/hidden_response_fields.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.

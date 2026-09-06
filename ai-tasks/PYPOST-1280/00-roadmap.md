# Roadmap: PYPOST-1280

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1280/10-requirements.md` documents the business goal,
    source selection, library browsing, environment resolution, validation,
    persistence, safety, cancellation, errors, and acceptance criteria.
  - Requirements are grounded in the PYPOST-1280 Jira story and the existing
    library, manifest, environment, and MCP configuration domain contracts.
  - Independent requirements review returned PASS.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1280/20-architecture.md` maps the source picker, async
    library/manifest discovery, library-backed identity, environment precedence,
    local overlays/secrets, validation, persistence, cancellation, observability,
    compatibility, and test seams.
  - The artifact defines an offline, independently runnable Step 3 red contract
    plan covering UI, presenter, controller, registry, environment precedence,
    errors, cancellation, and transactional no-partial-save behavior.
  - Architecture review passed after the checked persistence and runtime resolver
    boundaries were made explicit.
- [x] **STEP 3: Failing Repro Test**
  - Reopened after independent review found that the initial repro checked
    synchronous placeholders instead of async cancellation, persistence rollback,
    controller/registry propagation, invalid-input categories, reload identity,
    and isolation.
  - Replaced the repro with deterministic qapp, temporary-path, controlled-worker,
    event, and fake-store contracts in
    `tests/test_mcp_library_collection_pypost_1280_repro.py`.
  - The suite covers valid identity handoff/reload, environment precedence and
    safe diagnostics, invalid manifest/collection/profile, checked persistence
    failure with no overlay write, cancelled late-result suppression, and
    workspace/proxy isolation. No test setup, network, Git remote, or real secret
    is involved.
  - Focused command: `make test PYTEST_ARGS='tests/test_mcp_library_collection_pypost_1280_repro.py -vv'`.
  - Exact red result: 8 collected, 8 failed, 0 passed, 0 skipped in 0.12s.
    Failures are explicit missing-contract diagnostics for the async source picker,
    persisted identity fields, runtime resolver (four tests), checked store, and
    registry install path. No production code was changed.
- [x] **STEP 4: Development**
  - Replaced the reviewed test-only persistence and registry shortcuts with a checked
    ConfigManager round trip, rollback on registry-install failure, instance-scoped rows,
    and model-only registry lifecycle operations.
  - Added injected library collection/profile resolution with distinct stale-input errors,
    authoritative runtime requests/environment data, cancellable source-picker integration,
    source-switch isolation, and real disk reload coverage using a second controller.
  - Focused validation passed: `make test` for the PYPOST-1280 repro plus existing MCP
    controller/presenter tests; `make lint`, `make typecheck`, `make verify-ai-tasks`, and
    `git diff --check` also passed.
  - Reopened after independent review found incomplete production presenter injection,
    real LibraryManagerService resolution, checked library save routing, rollback snapshots,
    and workspace/proxy persistence regressions.
  - Corrected the reviewed gaps: production service injection and picker callbacks now
    precede worker start, real manifests/collections/presets resolve from registered paths,
    library and normal saves use checked persistence with registry rollback, and focused
    tests cover disk reload and presenter/service handoff.
  - Added real `LibraryManagerService` manifest/collection adapters, overlay-aware variable
    resolution, non-mutating registry preflight, full transaction snapshots, and connected
    library discovery through the cancellable picker.
  - Fixed the independent production-boundary review findings: the editor now selects a
    connected library identity, handoff overlays are persisted, rollback restores a normalized
    persisted overlay snapshot, and ordinary workspace environment IDs resolve library rows.
  - Added focused regression coverage for each boundary; `make test
    PYTEST_ARGS='tests/test_mcp_library_collection_pypost_1280_repro.py'`, `make lint`,
    `make typecheck`, and `make verify-ai-tasks` pass.
  - Required Make validation passes: focused MCP/library tests (5 files), `make lint`,
    `make typecheck`, `make verify-ai-tasks`, and `git diff --check`.
  - Implemented the reviewed production boundary fixes: connected-library discovery is
    worker-backed and cancellable, library profile and typed variable controls feed the
    handoff, and checked settings persistence verifies and restores serialized overlays
    after mid-write failures. Focused regressions cover cancellation, masked secrets,
    controller persistence, and durable rollback.
  - Applied the remaining identity and metadata fixes: unavailable persisted profiles
    remain visible and block Save, picker entries merge manifest and collection-level
    variable/profile declarations, and stale collection identities remain unselected
    instead of falling back to index zero.
  - Exact validation: focused repro `29 passed`; `make lint` passed; `make typecheck`
    passed with the baseline of 180 known errors; `make verify-ai-tasks` passed; and
    `git diff --check` passed.
-  - Final independent acceptance review passed after fixing collection-only active
    profiles and collection-level secret masking. Focused and compatibility Make tests
    passed.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
-  - Added `ai-tasks/PYPOST-1280/50-observability.md` documenting bounded logs and
     Prometheus metrics for discovery, validation, and save transaction outcomes.
- [x] **STEP 7: Technical Debt Analysis**
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/mcp_server_registry.md` with the library-backed MCP source,
    stable identity, environment/profile and overlay precedence, masking,
    cancellation/stale identity handling, journaled persistence/rollback,
    observability, and workspace/proxy compatibility.
  - Added the MCP integration cross-reference to
    `doc/dev/library_manifest_and_overlay.md`; no secret values were added.
-  - Final independent documentation review passed after correcting the relative
    observability link and replacing the direct pytest example with the repository's
    `make test` target.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1280/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1280/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1280/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1280/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1280/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.

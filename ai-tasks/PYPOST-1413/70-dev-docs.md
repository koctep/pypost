# PYPOST-1413: Developer Documentation

## Overview

Documented the shared virtual environment architecture, NFS network filesystem latency root
cause, lightweight skeleton template design, concurrency locking, and workspace isolation
guarantees introduced in PYPOST-1413 to prevent Makefile test suite timeouts under load.

## Documentation Artifacts

### Created

| File | Description |
| --- | --- |
| `doc/dev/shared_venv_materialization.md` | Comprehensive developer documentation explaining shared virtual environment architecture, NFS hardlink latency root cause, `.skeleton` template pattern with `.pth` linkage, concurrency locking with `fcntl.flock`, process group failure recovery, workspace isolation guarantees, API helper reference, and troubleshooting. |

### Updated

| File | Description |
| --- | --- |
| `doc/dev/README.md` | Added entry for `Shared Virtual Environment Materialization and Skeleton Template (PYPOST-1413)` under `### Testing and quality`. |
| `doc/dev/testing.md` | Updated `### Shared Make fixture preparation (PYPOST-1262 / PYPOST-1298 / PYPOST-1413)` section to describe the `.skeleton` template generation via `_build_skeleton`, fast cloning via `cp -a`, and cross-reference `doc/dev/shared_venv_materialization.md`. |

## Key Topics Documented

1. **Shared Virtual Environment Architecture**:
   - `tests/makefile_test_helpers.py` fixture design for `make_workspace` and
     `make_workspace_full_deps`.
   - Lazy centralized bootstrap in `_get_shared_base_venv()`.

2. **NFS Latency and Root Cause Analysis**:
   - Detailed explanation of `/tmp` running on `nfs4` network filesystem.
   - Synchronous metadata locking and RPC round-trips for each of 2,142 items during `cp -al`.
   - Contention under 8 parallel workers generating 17,136 RPCs and triggering 20s timeouts.

3. **Lightweight Skeleton Template Pattern**:
   - `.skeleton` directory structure containing `pyvenv.cfg`, symlinked `bin/*`, and
     `_prewarmed_base.pth` in `site-packages`.
   - Python `site` module `.pth` path injection pointing to immutable base dependencies.
   - 99.4% reduction in filesystem entries (from 2,142 down to ~12 items).
   - 50x–120x speedup in workspace materialization latency (<0.3s).

4. **Concurrency Locking and Failure Recovery**:
   - Non-blocking `fcntl.flock` polling (<= 50ms) with monotonic `remaining(stage)` deadline
     budgeting within 20s.
   - Atomic staging replacement (`tmp_skeleton.replace(skeleton_dir)`).
   - Process group isolation (`start_new_session=True`) and `os.killpg(proc.pid, signal.SIGKILL)`
     cleanup in `_run_preparation_command`.
   - Workspace cleanup of partial directories on error (`shutil.rmtree(target)`).

5. **Workspace Isolation Guarantees**:
   - Base virtual environment remains immutable and pristine.
   - Local installations (`make install`) write exclusively into the workspace's local
     `site-packages`.
   - Sibling workspaces remain isolated and independent.

## Verification

- `make lint`: Validated flake8 static analysis, test lint baseline, markdown formatting, and
  relative link consistency.
- `make verify-ai-tasks`: Confirmed AI task artifact integrity.

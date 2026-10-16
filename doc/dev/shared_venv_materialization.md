# Shared Virtual Environment Materialization and Skeleton Template (PYPOST-1413)

## Overview

Integration tests for PyPost's `Makefile` targets (such as `make test`, `make lint`,
`make install`, and target exit codes) run in dynamically created temporary workspace
directories. Testing these targets requires a functional virtual environment (`.venv`) inside
each test workspace so that Make recipes can execute tools like `pytest` and `flake8`.

Creating a complete virtual environment from scratch and running `pip install` for every test
workspace would introduce minutes of overhead to each test run. To maintain high test velocity,
`tests/makefile_test_helpers.py` provides pre-warmed virtual environment fixtures:
- `_get_shared_base_venv()`: Bootstraps and caches a shared base virtual environment with
  pre-installed test dependencies (`pytest` and `flake8`).
- `_build_skeleton()`: Creates a lightweight `.skeleton` directory template pointing to base
  dependencies.
- `_materialize_prewarmed_venv(ws)`: Rapidly populates `ws / ".venv"` by cloning the lightweight
  skeleton template.

This document describes the architecture, NFS filesystem performance challenges, skeleton
template pattern, concurrency locking, failure recovery, and isolation guarantees.

## Root Cause: NFS Network Filesystem Hardlink Latency

### Legacy Implementation (`cp -al`)

Previously, `_materialize_prewarmed_venv` cloned the shared base virtual environment into each
test workspace using archive hardlinks:

```python
_run_preparation_command(
    ["cp", "-al", str(base), str(target)],
    timeout=20,
    cleanup_budget=1,
)
```

In a standard virtual environment containing `pytest>=8,<9` and `flake8>=7,<8` (plus transitive
dependencies such as `pluggy`, `iniconfig`, `packaging`, `pyflakes`, `pycodestyle`, `mccabe`,
and `pip`), the environment tree contains:
- **183 directories**
- **1,959 files**
- **Total filesystem entries**: 2,142

### NFS4 Latency & Lock Contention

When test suites run on environments where `/tmp` (or `tempfile.gettempdir()`) is mounted on
an **NFS4 network filesystem** (`nfs4`):
1. **Synchronous RPC Overhead**: The `cp -al` command traverses all 183 directories and executes
   individual `link()` system calls for each of the 1,959 files. On NFS4, every directory creation
   and hardlink operation requires a synchronous RPC round-trip over the network, accompanied by
   metadata lock acquisition on the NFS server.
2. **Single-Worker Baseline**: Even with zero concurrency, `cp -al` took **10.4s to 12.9s** per
   workspace.
3. **Parallel Contention Failure**: When `scripts/run_parallel_tests.py` executes with 8 parallel
   workers, all 8 workers request workspace materialization simultaneously. This generated over
   `8 * 2,142 = 17,136` concurrent NFS RPC operations.
4. **Cascading Timeouts**: Heavy network queueing and NFS server metadata locking caused
   materialization latency to spike beyond the rigid 20-second threshold in
   `_run_preparation_command(timeout=20)`. The harness killed the process group with `SIGKILL`,
   raising:
   `RuntimeError: shared venv materialization failed: ... Command '['cp', '-al', ...] timed out after 20 seconds`
   This resulted in frequent test suite failures and test flakiness under parallel execution.

## Skeleton Template Architecture

To eliminate NFS RPC latency while maintaining full environment capability and strict workspace
isolation, PYPOST-1413 introduced the **Lightweight Skeleton Template Pattern**.

### Architecture Diagram

```text
Shared Base Directory (/tmp/pypost_shared_base_venv_<X.Y>/)
├── .venv/                         (Immutable Base Environment)
│   ├── pyvenv.cfg
│   ├── bin/ (python, pip, pytest, flake8)
│   └── lib/pythonX.Y/site-packages/ (~2,142 items: pytest, flake8, etc.)
│
├── .skeleton/                     (Pre-warmed Lightweight Template, ~12 items)
│   ├── pyvenv.cfg                 (Copied base configuration)
│   ├── bin/                       (Symlinks to .venv/bin/*)
│   │   ├── python -> ../../.venv/bin/python
│   │   ├── pytest -> ../../.venv/bin/pytest
│   │   └── flake8 -> ../../.venv/bin/flake8
│   ├── lib/pythonX.Y/site-packages/
│   │   └── _prewarmed_base.pth   (Contains absolute path to .venv site-packages)
│   └── .initialized-X.Y           (Readiness marker)
│
└── .lock                          (fcntl.flock concurrency coordinator)

                        │
                        ▼  cp -a .skeleton <ws>/.venv  (< 0.2s)
Workspace Sandbox (<ws>/.venv/)
├── pyvenv.cfg
├── bin/ (symlinks pointing to shared base binaries)
├── lib/pythonX.Y/site-packages/
│   ├── _prewarmed_base.pth        (Provides pytest, flake8 via sys.path)
│   └── (Workspace installs: editable pypost, .dist-info, etc.)
└── .initialized-X.Y
```

### The Skeleton Template Layout

The `.skeleton` directory is created once alongside `.venv` under the base directory:
- `pyvenv.cfg`: Copied directly from the base environment.
- `bin/`: Contains symlinks pointing to the binaries in `base_dir / ".venv" / "bin"`.
- `lib/pythonX.Y/site-packages/`: An initially empty directory containing a single file,
  `_prewarmed_base.pth`.
- `_prewarmed_base.pth`: Python `.pth` file containing the single line:
  `/<path-to-base>/.venv/lib/pythonX.Y/site-packages`
- `.initialized-<PYTHON_VERSION>`: Stamp verifying that the template was fully created.

### How `.pth` Linkage Works

Python's standard library `site` module processes `.pth` files during interpreter startup. When
the workspace's `bin/python` interpreter starts:
1. `site` loads `_prewarmed_base.pth` from the workspace's local `site-packages`.
2. It appends the shared base `site-packages` directory to `sys.path`.
3. Commands such as `python -m pytest` or `python -m flake8` locate and load packages directly
   from the shared base.

### Fast Materialization via `cp -a`

Instead of copying or linking thousands of files, `_materialize_prewarmed_venv` copies only the
minimal skeleton directory:

```python
skeleton = base.parent / ".skeleton"
source = skeleton if _venv_ready(skeleton) else base
_run_preparation_command(
    ["cp", "-a", str(source), str(target)],
    timeout=20,
    cleanup_budget=1,
)
```

### Performance Comparison

| Metric | Legacy (`cp -al` Base) | Skeleton Pattern (`cp -a` Skeleton) | Improvement |
| --- | --- | --- | --- |
| **Filesystem Items per WS** | 2,142 items | ~12 items | **99.4% reduction** |
| **Single-Worker Latency** | 10.4s – 12.9s | 0.09s – 0.21s | **50x – 120x speedup** |
| **8-Worker Concurrent RPCs** | 17,136 RPCs | ~96 RPCs | **99.4% reduction** |
| **8-Worker Execution Time** | >20s (Timeout) | < 0.3s | **Eliminates timeout** |

## Concurrency and Lifecycle Management

### Serialized Bootstrap with `fcntl.flock`

The shared base virtual environment and skeleton template are created lazily on demand. When
multiple tests or worker processes start at the same time:

1. **Lock Acquisition**:
   - `_get_shared_base_venv()` opens `base_dir.with_suffix(".lock")`.
   - It polls `fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)` with a polling interval of at most
     50 ms.
   - All stages (`lock`, `creation`, `installation`, `validation`, `publication`) share a single
     monotonically enforced preparation deadline (`remaining(stage)` from `preparation_budget=20`).

2. **Double-Checked Readiness**:
   - Once the lock is acquired, `_venv_ready(venv_dir)` and `_venv_ready(skeleton_dir)` are checked
     again.
   - If another worker already built the base while this worker was waiting for the lock, the
     worker immediately unlocks and returns the cached path without redundant work.

3. **Staged Publication of `.skeleton`**:
   - `_build_skeleton` creates a temporary directory (`skeleton_dir.with_name(f"{name}.tmp")`).
   - Populates configuration, binary symlinks, `.pth` file, and readiness marker.
   - Atomically replaces the target via `tmp_skeleton.replace(skeleton_dir)`.
   - Ensures that reader processes never observe a partially written skeleton.

## Failure Recovery and Process Management

### Process Group Reaping (`_run_preparation_command`)

Subprocesses invoked during preparation (virtual environment creation, pip installs, directory
copies) use process group isolation:
- Started with `start_new_session=True`.
- On `subprocess.TimeoutExpired`:
  - `os.killpg(proc.pid, signal.SIGKILL)` terminates the child process and any child processes it
    spawned.
  - A secondary bounded `proc.communicate(timeout=cleanup_budget)` salvages buffered stdout/stderr
    for debugging without hanging.
  - Re-raises `subprocess.TimeoutExpired` containing captured command output.
- On nonzero exit code (`CalledProcessError`):
  - Terminates process group via `os.killpg`.
  - Re-raises `CalledProcessError` with stdout and stderr preserved.

### Clean Workspace Teardown

If `_materialize_prewarmed_venv` encounters an error during `cp -a`:
- The partially copied target directory `target` is immediately removed via `shutil.rmtree(target)`.
- A descriptive `RuntimeError` is raised with the target path and underlying error.
- Corrupted half-copied `.venv` directories are never left on disk to mislead subsequent tests.

## Workspace Isolation Guarantees

The skeleton pattern strictly enforces test workspace isolation:

1. **Base Environment Immutability**:
   - The shared base `base_dir / ".venv"` is treated as read-only.
   - Pre-installed packages (`pytest`, `flake8`) remain pristine.
2. **Local Package Installations**:
   - When a test runs `make install` (`pip install -e ".[dev,otel]"`), `pip` installs the editable
     package and metadata directly into the workspace's local
     `ws / ".venv" / "lib" / pythonX.Y / site-packages/`.
   - The shared base `site-packages` is not written to.
3. **Cross-Workspace Sandboxing**:
   - Workspaces share neither filesystem hardlinks to site-packages nor writeable directory paths.
   - Files created or deleted in one test workspace cannot affect sibling test workspaces.

## API and Helper Reference

All helpers live in `tests/makefile_test_helpers.py`:

### `_get_shared_base_venv(*, preparation_budget: float = 20) -> Path`
Ensures that the shared base `.venv` and `.skeleton` exist, are populated, and are verified.
Returns the path to the shared base `.venv`.

### `_build_skeleton(venv_dir: Path, skeleton_dir: Path) -> None`
Builds or rebuilds the lightweight skeleton template at `skeleton_dir` from `venv_dir`. Uses an
atomic temporary directory replacement strategy.

### `_materialize_prewarmed_venv(ws: Path) -> None`
Populates `ws / ".venv"` from `skeleton_dir` if present, falling back to `base` if `.skeleton` is
absent (for mock compatibility in unit tests). Fast operation using `cp -a`.

### `_venv_ready(venv: Path) -> bool`
Checks whether `venv` contains both `.initialized-<PYTHON_VERSION>` and `bin/python`.

### `_run_preparation_command(cmd, *, timeout, cleanup_budget=5)`
Executes `cmd` with `start_new_session=True`, enforcing strict timeouts and process-group SIGKILL
cleanup.

### Fixtures: `make_workspace` and `make_workspace_full_deps`
- `make_workspace`: Class-scoped fixture providing a minimal test workspace with a pre-warmed `.venv`.
- `make_workspace_full_deps`: Function-scoped fixture providing a slow-smoke workspace with
  `_host_deps.pth` linking host dependencies for rapid wheel resolution.

## Troubleshooting

### Timeouts during Base Bootstrap
If `_get_shared_base_venv` fails with `shared venv <stage> deadline exceeded`:
- Check if another stale process holds `/tmp/pypost_shared_base_venv_<X.Y>.lock`.
- Remove `/tmp/pypost_shared_base_venv_<X.Y>*` to allow a fresh bootstrap.

### Verifying Skeleton Integrity
To inspect the skeleton directory structure manually:
```bash
ls -la /tmp/pypost_shared_base_venv_3.12/.skeleton
cat /tmp/pypost_shared_base_venv_3.12/.skeleton/lib/python3.12/site-packages/_prewarmed_base.pth
```
The file should contain the absolute path to `/tmp/pypost_shared_base_venv_3.12/.venv/lib/python3.12/site-packages`.

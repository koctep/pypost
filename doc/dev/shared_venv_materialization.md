# Shared Virtual Environment Materialization and Skeleton Template (PYPOST-1413, PYPOST-1419)

## Overview

Integration tests for PyPost's `Makefile` targets (such as `make test`, `make lint`,
`make install`, and target exit codes) run in dynamically created temporary workspace
directories. Testing these targets requires a functional virtual environment (`.venv`) inside
each test workspace so that Make recipes can execute tools like `pytest` and `flake8`.

Creating a complete virtual environment from scratch and running `pip install` for every test
workspace would introduce minutes of overhead to each test run. To maintain high test velocity,
the Make fixture helpers prepare one shared base virtualenv and materialize per-workspace
`.venv` trees from a lightweight skeleton:

- **`SharedVenvManager`** (`tests/helpers/shared_venv_manager.py`): owns bootstrap, flock +
  preparation-budget locking, skeleton publication, readiness state, and workspace
  materialization (PYPOST-1419).
- **Stable facades** in `tests/makefile_test_helpers.py`:
  `_get_shared_base_venv`, `_materialize_prewarmed_venv`, `_venv_ready`, and `_build_skeleton`
  delegate to a lazy process-default manager so fixtures and
  `scripts/run_parallel_tests.py` keep their existing import paths.
- **Skeleton + `.pth` layout** (PYPOST-1413): `_prewarmed_base.pth` points workspace interpreters
  at the immutable shared base `site-packages`; materialization uses `cp -a` of `.skeleton`
  (fallback: base).

This document describes the architecture, NFS filesystem performance challenges, skeleton
template pattern, concurrency locking, failure recovery, isolation guarantees, and the
manager / facade API.

## Architecture (PYPOST-1419)

Lifecycle ownership no longer lives in scattered free functions plus a module-level mutable
path cache (`_SHARED_BASE_VENV`). A single cohesive manager owns readiness as an instance
attribute; helpers expose thin facades for continuity.

```text
Consumers (unchanged outward contracts)
  make_workspace / make_workspace_full_deps
  _run_make lazy .venv materialize
  scripts/run_parallel_tests.py pre-warm (_get_shared_base_venv)
  tests/test_makefile_shared_readiness.py
  tests/test_shared_venv_manager.py
        │
        ▼
tests/makefile_test_helpers.py
  lazy default SharedVenvManager  ──►  ensure_ready / materialize / …
  _get_shared_base_venv()
  _materialize_prewarmed_venv(ws)
  _venv_ready / _build_skeleton wrappers
  _run_preparation_command (default preparation_runner)
        │
        ▼
tests/helpers/shared_venv_manager.py
  SharedVenvManager
    owned resolved_base (Path | None)
    lock coordination (fcntl + budget)
    bootstrap stages (create / install / validate)
    skeleton publication
    workspace materialization (cp -a)
```

Constructor-injected collaborators (defaults match production behavior) make lock contention,
stale readiness, and materialization failure paths unit-testable without a full NFS bootstrap:
`preparation_runner`, `clock`, `flock`, `base_root` / `tempdir_fn`, marker and interpreter
settings.

The process-default manager is a **lazy instance convention**, not a path singleton. Tests may
construct private `SharedVenvManager(...)` instances or call `clear_readiness()` on the default
manager. Do not reintroduce a module-level mutable `Path | None` cache as the readiness source
of truth.

## Root Cause: NFS Network Filesystem Hardlink Latency

### Legacy Implementation (`cp -al`)

Previously, materialization cloned the shared base virtual environment into each test workspace
using archive hardlinks:

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
isolation, PYPOST-1413 introduced the **Lightweight Skeleton Template Pattern**. PYPOST-1419
did not change on-disk layout or the `cp -a` path; it only encapsulated ownership.

### On-Disk Layout

The flock coordinator is a **sibling** of the shared base directory, not a child
inside it: `lock_file = base_dir.with_suffix(".lock")` (see
`SharedVenvManager.ensure_ready`). `Path.with_suffix` replaces only the final
suffix segment, so Python 3.12's base
`/tmp/pypost_shared_base_venv_3.12` locks at
`/tmp/pypost_shared_base_venv_3.lock` (not `…_3.12.lock`).

```text
/tmp/
├── pypost_shared_base_venv_<X.Y>/     (Shared Base Directory)
│   ├── .venv/                         (Immutable Base Environment)
│   │   ├── pyvenv.cfg
│   │   ├── bin/ (python, pip, pytest, flake8)
│   │   └── lib/pythonX.Y/site-packages/ (~2,142 items: pytest, flake8, etc.)
│   │
│   └── .skeleton/                     (Pre-warmed Lightweight Template, ~12 items)
│       ├── pyvenv.cfg                 (Copied base configuration)
│       ├── bin/                       (Symlinks to .venv/bin/*)
│       │   ├── python -> ../../.venv/bin/python
│       │   ├── pytest -> ../../.venv/bin/pytest
│       │   └── flake8 -> ../../.venv/bin/flake8
│       ├── lib/pythonX.Y/site-packages/
│       │   └── _prewarmed_base.pth   (Contains absolute path to .venv site-packages)
│       └── .initialized-X.Y           (Readiness marker)
│
└── pypost_shared_base_venv_<major>.lock
        (fcntl.flock sibling via base_dir.with_suffix(".lock");
         e.g. X.Y=3.12 → /tmp/pypost_shared_base_venv_3.lock)

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

Instead of copying or linking thousands of files, `SharedVenvManager.materialize` (via the
`_materialize_prewarmed_venv` facade) copies only the minimal skeleton directory:

```python
skeleton = base.parent / ".skeleton"
source = skeleton if manager.is_ready(skeleton) else base
preparation_runner(
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
   - `SharedVenvManager.ensure_ready()` (facade: `_get_shared_base_venv()`) opens
     `base_dir.with_suffix(".lock")`.
   - It polls exclusive non-blocking `flock` (`LOCK_EX | LOCK_NB`) with a polling interval of at
     most 50 ms (injected `clock` / `flock` collaborators).
   - All stages (`lock`, `creation`, `installation`, `validation`, `publication`) share a single
     monotonically enforced preparation deadline (`remaining(stage)` from
     `preparation_budget=20`).

2. **Double-Checked Readiness**:
   - If the manager's owned `resolved_base` is already ready, it returns immediately.
   - Else if on-disk base + skeleton are ready, it sets owned state and returns without locking.
   - Once the lock is acquired, readiness is checked again under the lock so only one competing
     caller bootstraps.

3. **Staged Publication of `.skeleton`**:
   - `build_skeleton` creates a temporary directory (`skeleton_dir.with_name(f"{name}.tmp")`).
   - Populates configuration, binary symlinks, `.pth` file, and readiness marker.
   - Atomically replaces the target via `tmp_skeleton.replace(skeleton_dir)`.
   - Ensures that reader processes never observe a partially written skeleton.

## Failure Recovery and Process Management

### Process Group Reaping (`_run_preparation_command`)

Subprocesses invoked during preparation (virtual environment creation, pip installs, directory
copies) use process group isolation via the default preparation runner in
`tests/makefile_test_helpers.py` (injectable into `SharedVenvManager`):
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

If materialization encounters an error during `cp -a`:
- The partially copied target directory is immediately removed via `shutil.rmtree(target)`.
- A descriptive `RuntimeError` is raised with the target path and underlying error
  (`shared venv materialization failed: …`).
- Corrupted half-copied `.venv` directories are never left on disk to mislead subsequent tests.

Stage-scoped bootstrap failures raise `RuntimeError` messages that identify the failing stage
(`lock`, `creation`, `installation`, `validation`, `publication`) for CI triage.

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

### `SharedVenvManager` (`tests/helpers/shared_venv_manager.py`)

Owns shared-base bootstrap, locking, skeleton publish, readiness state, and workspace
materialization.

| Member | Role |
| --- | --- |
| `__init__(*, python_version, base_root, marker_name, python_executable, preparation_runner, clock, flock, tempdir_fn)` | Construct with optional collaborator overrides for tests. |
| `resolved_base` | Owned readiness path, or `None` if not yet validated/published. |
| `clear_readiness()` | Drop owned readiness so the next `ensure_ready` re-validates on disk. |
| `is_ready(venv)` | True when marker and `bin/python` exist. |
| `build_skeleton(venv_dir, skeleton_dir)` | Publish lightweight `.skeleton` template. |
| `ensure_ready(*, preparation_budget=20)` | Serialize bootstrap under flock; return ready shared base `.venv` path. |
| `materialize(workspace, *, copy_timeout=20)` | Materialize `workspace/.venv` from skeleton (fallback: base). |

### Facades (`tests/makefile_test_helpers.py`)

Signatures are stable for fixtures and the parallel runner:

#### `_get_shared_venv_manager() -> SharedVenvManager`
Return the lazy process-default manager (wired with module clock / flock / preparation runner
so existing monkeypatches on the helpers module still apply).

#### `_get_shared_base_venv(*, preparation_budget: float = 20) -> Path`
Delegates to `ensure_ready(...)`. Ensures that the shared base `.venv` and `.skeleton` exist,
are populated, and are verified. Returns the path to the shared base `.venv`.

#### `_build_skeleton(venv_dir: Path, skeleton_dir: Path) -> None`
Delegates to `build_skeleton(...)`.

#### `_materialize_prewarmed_venv(ws: Path) -> None`
Delegates to `materialize(ws)`.

#### `_venv_ready(venv: Path) -> bool`
Delegates to `is_ready(venv)`.

#### `_run_preparation_command(cmd, *, timeout, cleanup_budget=5)`
Default preparation runner: executes `cmd` with `start_new_session=True`, enforcing strict
timeouts and process-group SIGKILL cleanup.

### Fixtures: `make_workspace` and `make_workspace_full_deps`
- `make_workspace`: Class-scoped fixture providing a minimal test workspace with a pre-warmed `.venv`.
- `make_workspace_full_deps`: Function-scoped fixture providing a slow-smoke workspace with
  `_host_deps.pth` linking host dependencies for rapid wheel resolution.

### Related tests
- `tests/test_shared_venv_manager.py` — ownership and injected-collaborator stage coverage.
- `tests/test_makefile_shared_readiness.py` — behavioral regression for lock/budget/materialization
  and parallel load budget.

## Configuration

| Setting | Default | Notes |
| --- | --- | --- |
| Shared base root | `<tempfile.gettempdir()>/pypost_shared_base_venv_<major.minor>` | Overridable via manager `base_root` / `tempdir_fn`. |
| Ordinary helper budget | 20s across lock + bootstrap | `_get_shared_base_venv(preparation_budget=…)` |
| Runner cold preparation | 90s (watchdog 95s) | See [testing.md](testing.md) shared Make fixture section. |
| Workspace copy timeout | 20s (`cleanup_budget=1`) | `materialize(..., copy_timeout=…)` |
| Marker | `.initialized-<major.minor>` | Plus `bin/python` required for readiness. |

These budgets are fixed harness settings; they do not change `pytest.mark.timeout`, worker
concurrency, or Make `WORKER_TIMEOUT`.

## Troubleshooting

### Timeouts during Base Bootstrap
If `_get_shared_base_venv` / `ensure_ready` fails with `shared venv <stage> deadline exceeded`:
- Check if another stale process holds the sibling lock from
  `base_dir.with_suffix(".lock")`. For Python 3.12 that path is
  `/tmp/pypost_shared_base_venv_3.lock` (`.12` is stripped; it is not
  `…_3.12.lock`).
- Remove both the base directory and its sibling lock, e.g.
  `rm -rf /tmp/pypost_shared_base_venv_3.12 /tmp/pypost_shared_base_venv_3.lock`
  (or equivalent for your major.minor), then retry. A glob like
  `/tmp/pypost_shared_base_venv_<X.Y>*` does **not** match the sibling
  `…_<major>.lock` file.
- In unit tests, inject a fake `clock` / `flock` rather than waiting on a real lock file.

### Stale process readiness
If a process-local manager still points at a removed base:
- Call `clear_readiness()` on the default manager (or construct a fresh `SharedVenvManager`) so
  the next `ensure_ready` re-validates on disk.
- Do not assign a module-level path cache; readiness lives on the manager instance.

### Verifying Skeleton Integrity
To inspect the skeleton directory structure manually:
```bash
ls -la /tmp/pypost_shared_base_venv_3.12/.skeleton
cat /tmp/pypost_shared_base_venv_3.12/.skeleton/lib/python3.12/site-packages/_prewarmed_base.pth
```
The file should contain the absolute path to `/tmp/pypost_shared_base_venv_3.12/.venv/lib/python3.12/site-packages`.

### Focused regressions
```bash
make test PYTEST_ARGS='tests/test_shared_venv_manager.py tests/test_makefile_shared_readiness.py'
```

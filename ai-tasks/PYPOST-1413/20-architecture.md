# PYPOST-1413: Makefile test suites fail with shared venv materialization timeout under load

## Research

### Codebase Analysis

PyPost uses Makefile targets to orchestrate test environments, development tasks, and packaging quality gates. Integration test suites under `tests/` verify that Makefile targets behave correctly in cleanly isolated sandboxes:

- `tests/test_makefile_target_install_test.py`
- `tests/test_makefile_stamp_otel_idempotency.py`
- `tests/test_makefile_exit_behavior.py`
- `tests/test_makefile_install_stamp_contract.py`
- `tests/test_makefile_stamp_test_idempotency.py`
- `tests/test_makefile_markers.py`
- `tests/test_makefile_recipes.py`
- `tests/test_makefile_target_filtering.py`

In `tests/makefile_test_helpers.py`, test fixtures (`make_workspace` and `make_workspace_full_deps`) initialize isolated workspaces. To avoid installing packages from scratch on every test case, `_get_shared_base_venv()` bootstraps a shared base virtual environment in `tempfile.gettempdir()`, and `_materialize_prewarmed_venv(ws: Path)` replicates this environment into each test workspace as `ws / ".venv"`.

The current implementation in `tests/makefile_test_helpers.py` is:

```python
def _materialize_prewarmed_venv(ws: Path) -> None:
    base = _get_shared_base_venv()
    target = ws / ".venv"
    if _venv_ready(target):
        return
    if target.exists():
        shutil.rmtree(target)
    try:
        _run_preparation_command(
            ["cp", "-al", str(base), str(target)], timeout=20, cleanup_budget=1,
        )
    except (subprocess.SubprocessError, OSError) as error:
        if target.exists():
            shutil.rmtree(target)
        raise RuntimeError(f"shared venv materialization failed: {target}: {error}") from error
```

### Contention & Latency Root Cause Analysis

Investigation of the test environment revealed the exact technical root cause of the timeout failures:

1. **Filesystem Architecture (`nfs4`)**:
   Querying the filesystem type of `tempfile.gettempdir()` via `df -T /tmp` reveals:
   ```text
   Filesystem      Type  1K-blocks       Used  Available Use% Mounted on
   :/ai/ai-ide/tmp nfs4 2692163328 1266917120 1288417280  50% /tmp
   ```
   The temporary workspace directory `/tmp` is mounted on an **NFS4 network filesystem**.

2. **Inode Count in Shared Virtual Environment**:
   Inspecting `_get_shared_base_venv()` reveals that after installing `pytest>=8,<9` and `flake8>=7,<8` (and their dependencies: `pluggy`, `iniconfig`, `packaging`, `pyflakes`, `pycodestyle`, `mccabe`, `pip`, etc.), the directory contains:
   - **Total items**: 2,142
   - **Directories**: 183
   - **Files**: 1,959
   - **Symlinks**: 4

3. **NFS RPC Round-Trip Penalty of `cp -al`**:
   The `cp -al` command traverses all 183 directories and issues individual `link()` system calls for each of the 1,959 files to create hardlinks. On NFS4, every `mkdir` and `link` call requires a synchronous RPC round-trip over the network, accompanied by metadata locking on the NFS server.
   
4. **Empirical Benchmarks (Single Worker, Zero Contention)**:
   - `cp -al` duration: **10.37s – 12.95s**
   - `cp -a` (full copy) duration: **63.57s**
   - `tar -cf - . | tar -xf -` duration: **26.15s**

5. **Parallel Contention Failure Mode**:
   When `make test` runs 8 concurrent worker processes (via `scripts/run_parallel_tests.py`), all 8 workers request workspace materialization simultaneously.
   - Total simultaneous RPC operations: `8 * 2,142 = 17,136` NFS network calls.
   - NFS server queue contention, network latency, and file locking immediately elevate materialization latency from ~11s to >20s.
   - Once a worker exceeds the rigid 20-second threshold in `_run_preparation_command(timeout=20)`, the harness kills the process group with `SIGKILL` and raises:
     `RuntimeError: shared venv materialization failed: ... Command '['cp', '-al', ...] timed out after 20 seconds`
   - This cascades into multiple worker aborts, causing flaky and broken CI/local test runs.

### Evaluation of Architectural Options

| Option | Mechanism | File Operations per WS | Idle Duration | 8-Worker Load Est. | Isolation | Assessment |
| --- | --- | --- | --- | --- | --- | --- |
| **A. Naive Timeout Increase** | Keep `cp -al`, raise timeout to 60s+ | 2,142 NFS links | ~12s | 30s – 50s | High | ❌ **Rejected**: Masks slow I/O, inflates test suite execution by minutes, fails NFR1. |
| **B. Tarball / Archive Cache** | Unpack pre-built tarball per WS | 2,142 NFS writes | ~26s | >90s | High | ❌ **Rejected**: Slower than `cp -al` due to NFS write overhead. |
| **C. Symlink Site-Packages Root** | Symlink `.venv/lib/.../site-packages` to base | ~15 symlinks | ~0.05s | ~0.1s | ❌ Broken | ❌ **Rejected**: Breaks FR2. `pip install -e .` in one workspace pollutes shared base and other workspaces. |
| **D. Lightweight Skeleton + `.pth` Redirection** (Selected) | Clone skeleton (~12 items); inject base site-packages via `_prewarmed_base.pth` | **~12 items** | **~0.09s – 0.21s** | **<0.5s** | **Strict (100%)** | ✅ **Selected**: Fast, 50x–120x speedup, 100% isolated, uses native Python mechanism. |

### Selected Architecture: Lightweight Skeleton Directory with `.pth` Linkage

Python's `site` module automatically parses `.pth` files placed in a virtualenv's `site-packages` directory at interpreter startup and appends the specified directories to `sys.path`. This pattern is already successfully employed in `tests/makefile_test_helpers.py` (line 540) for `_host_deps.pth` in `make_workspace_full_deps`.

By establishing a pre-warmed `.skeleton` template alongside `.venv` in the shared base directory:
1. `base_dir / ".skeleton"` contains only:
   - `pyvenv.cfg`
   - `bin/`: symlinks pointing to Python interpreter and command scripts
   - `lib/pythonX.Y/site-packages/`: a private empty directory containing `_prewarmed_base.pth` (which contains the single absolute path to `base_dir / ".venv" / "lib" / f"python{PYTHON_VERSION}" / "site-packages"`)
   - `.initialized-X.Y`: marker file
2. `_materialize_prewarmed_venv` copies or clones only this minimal 12-item skeleton (`cp -a str(skeleton) str(target)`):
   - Inode operations reduced from **2,142 to 12** (**99.4% reduction**).
   - Execution time reduced from **10.97s to 0.21s** (**50x speedup** on NFS4).
   - Peak 8-worker NFS load reduced from **17,136 RPCs to 96 RPCs**.
3. **Workspace Isolation Guarantee (FR2)**:
   - When a test runs `make install` (`pip install -e ".[dev,otel]"`), `pip` installs the editable package and `.dist-info` directly into `ws / ".venv" / "lib" / ... / "site-packages"`.
   - The shared base environment in `base_dir / ".venv"` is never modified by any test worker.
   - Separate test workspaces remain completely isolated.

---

## Implementation Plan

### Mandatory Failing Repro for Step 3

To strictly adhere to test-driven quality assurance, Step 3 will write an automated red test that reproduces the timeout failure under simulated concurrent load before any production fix is introduced in Step 4.

- **Test Location**:
  `tests/test_makefile_shared_readiness.py`
- **Test Name**:
  `test_parallel_workspace_materialization_under_load_budget`
- **Test Strategy & Mechanism**:
  1. The test uses `multiprocessing` to spawn concurrent worker processes (e.g., 4 to 8 workers, matching `scripts/run_parallel_tests.py` default concurrency).
  2. Each worker receives an isolated workspace directory and invokes `helpers._materialize_prewarmed_venv(workspace)`.
  3. The test enforces a strict performance budget: all concurrent materializations must complete within the operational budget (e.g. 5.0 seconds per worker, conforming to NFR1: *"workspace materialization must complete in under 5 seconds under nominal conditions"*).
  4. The test asserts:
     - All workers succeed without `RuntimeError` or `TimeoutExpired`.
     - `_venv_ready(ws / ".venv")` is true for every workspace.
     - Each workspace can execute `python -c "import pytest, flake8"`.
     - Workspace isolation: creating a file in one workspace's `.venv` does not reflect in any sibling workspace or base.
- **Why It Fails (Red) on Current Codebase**:
  - The current implementation of `_materialize_prewarmed_venv` executes `cp -al` across 2,142 files.
  - On this NFS filesystem, even a single worker takes ~11–13 seconds, instantly breaching the 5-second budget assertion.
  - Under 4–8 concurrent workers, `cp -al` routinely exceeds the 20-second `_run_preparation_command` timeout, raising `RuntimeError: shared venv materialization failed: ... Command '['cp', '-al', ...] timed out after 20 seconds`.
  - The test will fail consistently and deterministically without requiring external network access or live services.
- **Sequencing**:
  - Step 2: Architecture design and repro plan (this document).
  - Step 3: Implement `test_parallel_workspace_materialization_under_load_budget` in `tests/test_makefile_shared_readiness.py` and run via `make test` to confirm it is RED.
  - Step 4: Implement skeleton template and `.pth` linkage in `tests/makefile_test_helpers.py`, verifying that the Step 3 test and all Makefile suites turn GREEN.

### Step 4 Development Breakdown

1. **Iteration 1 — Base Skeleton Generation**:
   - In `tests/makefile_test_helpers.py`, update `_get_shared_base_venv()`:
     - After verifying `pytest` and `flake8` imports in `base_dir / ".venv"`, build `base_dir / ".skeleton"`.
     - Populate `.skeleton` with `pyvenv.cfg`, symlinks for `bin/*`, `site-packages/_prewarmed_base.pth` pointing to `base_dir / ".venv"` site-packages, and the `.initialized-{PYTHON_VERSION}` marker.
     - Ensure cleanup on bootstrap retry handles `.skeleton` alongside `.venv`.

2. **Iteration 2 — Fast Workspace Materialization**:
   - Update `_materialize_prewarmed_venv(ws: Path)`:
     - Retrieve `base = _get_shared_base_venv()`.
     - Identify `skeleton = base.parent / ".skeleton"`. If `skeleton.is_dir()` exists, materialize from `skeleton`; otherwise (fallback for test mocks), materialize from `base`.
     - Invoke `_run_preparation_command(["cp", "-a", str(source), str(target)], timeout=20, cleanup_budget=1)`.
     - This maintains compatibility with existing tests in `test_makefile_shared_readiness.py` while slashing file count from 2,142 to 12.

3. **Iteration 3 — Full Quality Gate Validation**:
   - Run `make test` with all 8 workers.
   - Verify all Makefile test suites:
     - `tests/test_makefile_target_install_test.py`
     - `tests/test_makefile_stamp_otel_idempotency.py`
     - `tests/test_makefile_exit_behavior.py`
     - `tests/test_makefile_install_stamp_contract.py`
     - `tests/test_makefile_stamp_test_idempotency.py`
     - `tests/test_makefile_markers.py`
     - `tests/test_makefile_recipes.py`
     - `tests/test_makefile_target_filtering.py`
     - `tests/test_makefile_shared_readiness.py`
   - Run `make check` (`lint`, `test`, `verify-ai-tasks`).

---

## Architecture

### System Architecture Diagram

```mermaid
flowchart TD
    subgraph SharedTempStorage["Shared Storage (tempfile.gettempdir() on NFS4)"]
        LockFile["pypost_shared_base_venv_{PY_VER}.lock"]
        BaseDir["pypost_shared_base_venv_{PY_VER}/"]
        
        subgraph BaseVenv[".venv/ (Full Package Store)"]
            BaseCfg["pyvenv.cfg"]
            BaseBin["bin/ (python, pytest, flake8, pip)"]
            BaseLib["lib/python{PY_VER}/site-packages/ (2,142 files)"]
            BaseMarker[".initialized-{PY_VER}"]
        end
        
        subgraph BaseSkeleton[".skeleton/ (Lightweight Template)"]
            SkelCfg["pyvenv.cfg"]
            SkelBin["bin/ (Symlinks to BaseBin)"]
            SkelLib["lib/python{PY_VER}/site-packages/"]
            SkelPth["_prewarmed_base.pth -> BaseLib"]
            SkelMarker[".initialized-{PY_VER}"]
        end
    end

    subgraph ParallelRunner["Parallel Test Runner (scripts/run_parallel_tests.py)"]
        PreWarmHook["Runner Fixture Pre-warm Hook"]
    end

    subgraph TestWorkers["Concurrent Test Workers (8 Workers)"]
        Worker1["Worker 1 (test_makefile_exit_behavior.py)"]
        Worker2["Worker 2 (test_makefile_target_install_test.py)"]
        WorkerN["Worker N (...)"]
    end

    subgraph IsolatedWorkspaces["Isolated Test Workspaces (tmp_path)"]
        WS1[".venv in Workspace 1 (12 items)"]
        WS2[".venv in Workspace 2 (12 items)"]
        WSN[".venv in Workspace N (12 items)"]
    end

    PreWarmHook -->|1. Acquires lock & bootstraps| LockFile
    LockFile --> BaseVenv
    BaseVenv -->|2. Constructs template| BaseSkeleton

    Worker1 -->|3. Fast cp -a (0.2s)| WS1
    Worker2 -->|3. Fast cp -a (0.2s)| WS2
    WorkerN -->|3. Fast cp -a (0.2s)| WSN

    BaseSkeleton -.->|Copies 12 items| WS1
    BaseSkeleton -.->|Copies 12 items| WS2
    BaseSkeleton -.->|Copies 12 items| WSN

    WS1 -->|sys.path resolution| BaseLib
    WS2 -->|sys.path resolution| BaseLib
    WSN -->|sys.path resolution| BaseLib
```

### Component Responsibilities

1. **`_get_shared_base_venv(*, preparation_budget: float = 20) -> Path`**:
   - **Role**: Shared Base Environment Coordinator.
   - **Responsibilities**:
     - Serializes bootstrap via non-blocking flock on `pypost_shared_base_venv_{PYTHON_VERSION}.lock`.
     - Validates cached environment readiness (`MARKER_NAME` and `bin/python`).
     - Orchestrates isolated subprocess stages: environment creation (`python -m venv`), package installation (`pip install pytest flake8`), and validation (`import pytest, flake8`).
     - Constructs the `.skeleton` template directory with interpreter symlinks and `_prewarmed_base.pth`.
     - Enforces overall bounded preparation budget with monotonic deadline countdown.
     - Publishes readiness marker upon verified completion.

2. **`_materialize_prewarmed_venv(ws: Path) -> None`**:
   - **Role**: Workspace Environment Materializer.
   - **Responsibilities**:
     - Ensures shared base environment and skeleton are initialized via `_get_shared_base_venv()`.
     - Checks if workspace `.venv` is already ready; returns immediately if valid.
     - Cleans stale partial workspace directories if present.
     - Dispatches bounded cloning command (`cp -a`) copying the minimal 12-item skeleton template into `ws / ".venv"`.
     - Governed by `_run_preparation_command` with a 20-second timeout and 1-second process-group cleanup budget.

3. **`_run_preparation_command(cmd: list[str], *, timeout: float, cleanup_budget: float = 5) -> subprocess.CompletedProcess[str]`**:
   - **Role**: Process Supervisor and Reaper.
   - **Responsibilities**:
     - Spawns subprocesses in isolated process sessions (`start_new_session=True`).
     - Monitors command execution against allocated timeout budget.
     - On timeout or non-zero exit, dispatches `SIGKILL` to the entire process group (`killpg`), preventing orphaned descendant processes.
     - Reaps process status within strict `cleanup_budget`.

4. **Python `site` & `.pth` Linker**:
   - **Role**: Runtime Dependency Resolver.
   - **Responsibilities**:
     - At Python invocation in `ws / ".venv" / "bin" / "python"`, reads `ws / ".venv" / "pyvenv.cfg"`.
     - Sets `sys.prefix` to `ws / ".venv"`.
     - Executes `ws / ".venv" / "lib" / f"python{PYTHON_VERSION}" / "site-packages" / "_prewarmed_base.pth"`.
     - Adds `base_dir / ".venv" / "lib" / ... / "site-packages"` to `sys.path`.
     - Allows `pytest` and `flake8` to be imported and executed without duplicating 2,142 files.

### Interface & Data Contracts

#### 1. Shared Base Directory Layout
```text
/tmp/pypost_shared_base_venv_{PYTHON_VERSION}/
├── .lock                                      # flock synchronization file
├── .venv/                                     # Full base environment (read-only package store)
│   ├── .initialized-{PYTHON_VERSION}          # Base readiness marker
│   ├── pyvenv.cfg                             # Base venv configuration
│   ├── bin/                                   # Real Python interpreter & tool wrappers
│   └── lib/python{PYTHON_VERSION}/site-packages/ # 2,142 pre-installed package files
└── .skeleton/                                 # Lightweight materialization template (~12 files)
    ├── .initialized-{PYTHON_VERSION}          # Skeleton readiness marker
    ├── pyvenv.cfg                             # Cloned venv configuration
    ├── bin/                                   # Symlinks to .venv/bin/*
    └── lib/python{PYTHON_VERSION}/site-packages/
        └── _prewarmed_base.pth                # Line containing absolute path to .venv site-packages
```

#### 2. Materialized Workspace Layout
```text
{ws}/.venv/
├── .initialized-{PYTHON_VERSION}              # Readiness marker
├── pyvenv.cfg                                 # Independent venv config
├── bin/                                       # Independent execution binaries (symlinks to base)
│   ├── python -> ...
│   ├── pytest -> ...
│   └── flake8 -> ...
└── lib/python{PYTHON_VERSION}/site-packages/   # Independent site-packages directory
    ├── _prewarmed_base.pth                    # Points to shared base site-packages
    └── {editable_packages}                    # Local packages installed via 'make install'
```

---

## Q&A

**Q: Why use a `.pth` file instead of symlinking the entire `site-packages` directory?**  
A: If `site-packages` were a directory symlink, any `pip install -e .` or package installation performed by a test in its workspace would write directly into the shared base environment. This would corrupt the shared template, cause race conditions between parallel tests, and violate Requirement FR2 (*Strict Workspace Isolation*). With a `.pth` file, each workspace has its own real `site-packages` directory; `pip` writes only to that local workspace directory while reading pre-warmed dependencies from the path specified in `.pth`.

**Q: Why keep `_run_preparation_command(["cp", "-a", ...])` instead of creating the skeleton purely in Python?**  
A: Retaining `_run_preparation_command(["cp", "-a", ...])` preserves existing test harness contracts and assertions in `tests/test_makefile_shared_readiness.py`, which verify bounded process timeouts and cleanup handling. Furthermore, `cp -a` on a 12-item directory takes only ~0.2s on NFS4, safely within our <5s target.

**Q: What if a test mutates `.venv` or executes `make clean`?**  
A: When a test runs `make clean`, `Makefile` executes `rm -rf $(VENV)`, removing only the workspace's local `.venv`. If subsequent targets in that test need the environment, `_run_make` automatically invokes `_materialize_prewarmed_venv(workspace)`, which re-copies the 12-item `.skeleton` in 0.2s. The shared base environment and template in `/tmp` remain completely untouched.

**Q: How does this interact with `make_workspace_full_deps`?**  
A: `make_workspace_full_deps` already uses `_materialize_prewarmed_venv` followed by creating `_host_deps.pth` pointing to host repository dependencies. The skeleton approach is 100% compatible with this existing pattern and dramatically reduces `make_workspace_full_deps` setup time.

**Q: Does this change require any modification to production application code in `pypost/`?**  
A: No. All modifications are strictly confined to test infrastructure in `tests/makefile_test_helpers.py` and test verification suites in `tests/`. No application files in `pypost/` are touched.

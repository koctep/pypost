# Setup and Installation

## Prerequisites

- Python 3.11+ (CI matrix: 3.11 and 3.13; see [README](../README.md))
- pip (Python package installer)
- Git

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd pypost
```

### 2. Install Dependencies

You can use `make` to set up the virtual environment and install dependencies automatically:

```bash
make install
```

Alternatively, to do it manually:

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Dependency lock file (PYPOST-779)

Production dependencies use a **two-file** layout:

| File | Role |
| --- | --- |
| `requirements.in` | Direct dependencies and version constraints (edit this) |
| `requirements.txt` | Compiled transitive lock with exact pins (committed; do not hand-edit) |

`make install` and CI install from `requirements.txt`, so every clone gets the same resolved
graph. The lock is compiled for **Python 3.11** (minimum supported); CI also tests **3.13**.

**Regenerate the lock** after editing `requirements.in` (requires [uv](https://docs.astral.sh/uv/)
on `PATH`):

```bash
make lock
```

Verify the committed lock matches the source file:

```bash
make check-lock
```

### Development dependency lock file (PYPOST-780)

Test and lint tooling uses the same **two-file** layout as production:

| File | Role |
| --- | --- |
| `requirements-dev.in` | Direct dev deps (pytest, flake8, etc.) |
| `requirements-dev.txt` | Compiled transitive lock (committed; do not hand-edit) |

`make venv-test` and CI install from `requirements-dev.txt`, so local and CI share one pinned
dev stack.

**Regenerate the dev lock** after editing `requirements-dev.in`:

```bash
make lock-dev
```

Verify the committed dev lock matches the source file:

```bash
make check-lock-dev
```

**Dependabot / upgrade workflow:** weekly pip PRs may bump `requirements.in` or `requirements.txt`.
After merging dependency changes, run `make lock`, commit both files, and run `make check`.

**Production packages:** `make install` resolves 11 direct production dependencies from
`requirements.in` (locked in `requirements.txt`). Pinned versions and audit notes live in
[dependencies_audit.md](dependencies_audit.md) § Production Dependencies.

| Package | Role |
| --- | --- |
| PySide6 | Qt GUI framework |
| requests | Outbound HTTP |
| PyYAML | YAML parsing |
| jinja2 | Request templating |
| pydantic | Models and settings validation |
| platformdirs | Cross-platform config paths |
| mcp | MCP server SDK (pulls starlette/uvicorn transitively) |
| prometheus_client | Default Prometheus metrics backend |
| sseclient-py | SSE response probe |
| cryptography | Encryption at rest |
| keyring | OS credential store |

See [dependencies_audit.md](dependencies_audit.md) § MCP Stack for transitive MCP dependencies.

### Project metadata (`pyproject.toml`, PYPOST-785)

PyPost declares PEP 621 metadata and optional dependency groups in root `pyproject.toml`:

| Section | Mirrors |
| --- | --- |
| `[project].dependencies` | Direct production pins in `requirements.in` |
| `[project.optional-dependencies].dev` | Direct dev pins in `requirements-dev.in` |
| `[project.optional-dependencies].otel` | Direct OTel pins in `requirements-otel.in` |

`make install` installs production (`requirements.txt`), dev test tooling (`requirements-dev.txt`),
and the OTel overlay (`requirements-otel.txt`) so `make test` can run OTel unit tests. Production
`requirements.txt` no longer includes OpenTelemetry (PYPOST-787). When you change
`requirements.in`, `requirements-dev.in`, or `requirements-otel.in`, update the matching
`pyproject.toml` sections and run `make check` — `tests/test_pyproject.py` fails on drift.

### OpenTelemetry optional overlay (PYPOST-787)

OpenTelemetry is optional for runtime (Prometheus is the default metrics backend). Install paths:

| File | Role |
| --- | --- |
| `requirements-otel.in` | Direct OTel API/SDK pins (edit this) |
| `requirements-otel.txt` | Compiled transitive lock (committed; do not hand-edit) |

**Regenerate the OTel lock** after editing `requirements-otel.in`:

```bash
make lock-otel
```

Verify the committed OTel lock matches the source file:

```bash
make check-lock-otel
```

`make venv-otel` installs only the OTel overlay; CI and `make install` include it for OTel tests.
End users who need OTel export can also use:

```bash
pip install -e ".[otel]"   # OpenTelemetry metrics backend
pip install -r requirements-otel.txt   # overlay lock file
```

### 3. Run the Application

Use `make` to run the application:

```bash
make run
```

Or manually:

```bash
# Ensure .venv is activated
python -m pypost.main
```

### 4. Development Commands

The project uses a `Makefile` to simplify common tasks. Run `make` or `make help` to list all
documented targets and descriptions:

```bash
make help
```

Common targets:

- **Initialize virtual environment only**:
  ```bash
  make venv
  ```
- **Install dependencies explicitly**:
  ```bash
  make install
  ```
- **Run tests**:
  ```bash
  make test
  ```
- **Lint code** (`flake8` on `pypost/`; T201 bans `print()` in application code):
  ```bash
  make lint
  ```
- **Quality gate** (lint + fast tests):
  ```bash
  make check
  ```
- **Clean up** (removes `.venv` and cache):
  ```bash
  make clean
  ```

### Makefile Behavior Notes

- `venv` is driven by `$(VENV_MARKER)` and is version-aware
  (`.venv/.initialized-<major.minor>`).
- `run`, `test`, and `lint` depend on `$(VENV_MARKER)` only and do not trigger full `install`.
- `test`, `test-slow`, and `test-cov` depend on `venv-otel` so OTel unit tests can import SDK
  packages; run `make install` (or `pip install -r requirements.txt`) for application deps.

### Unit tests (pytest)

The repository root is not installed as a package by default. Root `pytest.ini` sets
`pythonpath = .` so `import pypost` succeeds when pytest runs from the repo root **without**
setting `PYTHONPATH` (see PYPOST-434).

**Reproducible test environment** (PYPOST-465): on a clean checkout, run `make install` once —
it provisions app deps (`requirements.txt`), test tooling (`pytest`, `pytest-cov`,
`pytest-timeout`, `flake8`, `flake8-print` via `venv-test` → `requirements-dev.txt`), and the
OTel overlay (`venv-otel` → `requirements-otel.txt`). Then run full regression with:

```bash
make test        # fast suite (-m "not slow")
make test-slow   # Makefile install smoke
make test-cov    # fast suite with coverage
```

See [testing.md](testing.md) § Reproducible test environment for the full checklist and CI
parity notes (main job includes `pytest-timeout`, matching local `venv-test`).

CI runs the fast suite on every push and pull request via `.github/workflows/test.yml`
(Python 3.11 and 3.13) on **GitHub-hosted `ubuntu-latest`**. `sudo apt-get` installs EGL/GL/XCB
packages so PySide6 can import under `QT_QPA_PLATFORM=offscreen`. Jobs do not use a Docker
container so `actions/setup-python` toolcache builds match the runner libc.

## Troubleshooting

- **Missing modules**: Ensure your virtual environment is activated and you have installed
  requirements (`make install`).
- **Qt Platform plugin "xcb"**: On Linux, you might need to install `libxcb-cursor0` or similar
  system libraries if the app fails to launch.
- **CI: missing Qt `.so` (e.g. `libEGL`, `libfontconfig`, `libglib-2.0`)**: Install the matching
  Ubuntu packages on the runner (see `.github/workflows/test.yml`, `apt-get` step).

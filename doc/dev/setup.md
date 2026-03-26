# Setup and Installation

## Prerequisites

- Python 3.10+
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

**Key Dependencies:**
- `PySide6`: The Qt framework for Python (GUI).
- `requests`: HTTP library for sending requests.
- `jinja2`: Template engine for variable interpolation.
- `pydantic`: Data validation using Python type hints.
- `prometheus_client`: Library for exposing Prometheus metrics.

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

The project uses a `Makefile` to simplify common tasks:

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
- **Lint code**:
  ```bash
  make lint
  ```
- **Clean up** (removes `.venv` and cache):
  ```bash
  make clean
  ```

### Makefile Behavior Notes

- `venv` is driven by `$(VENV_MARKER)` and is version-aware
  (`.venv/.initialized-<major.minor>`).
- `run`, `test`, and `lint` depend on `$(VENV_MARKER)` only and do not trigger `install`.
- If dependencies are missing, `run/test/lint` fail naturally with interpreter/module errors.
- Use `make install` explicitly when dependencies must be installed or refreshed.

### Unit tests (pytest)

The repository root is not installed as a package by default.  Root `pytest.ini` sets
`pythonpath = .` so `import pypost` succeeds when pytest runs from the repo root **without**
setting `PYTHONPATH` (see PYPOST-434).

After `make install` (or with an activated venv that has test dependencies):

```bash
make test
```

Equivalent manual invocation:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/
```

CI runs the same suite on every push and pull request via `.github/workflows/test.yml`
(Python 3.11 and 3.13) on **GitHub-hosted `ubuntu-latest`**.  `sudo apt-get` installs EGL/GL/XCB
packages so PySide6 can import under `QT_QPA_PLATFORM=offscreen`.  Jobs do not use a Docker
container so `actions/setup-python` toolcache builds match the runner libc.

## Troubleshooting

- **Missing modules**: Ensure your virtual environment is activated and you have installed
  requirements (`make install`).
- **Qt Platform plugin "xcb"**: On Linux, you might need to install `libxcb-cursor0` or similar
  system libraries if the app fails to launch.
- **CI: missing Qt `.so` (e.g. `libEGL`, `libfontconfig`, `libglib-2.0`)**: Install the matching
  Ubuntu packages on the runner (see `.github/workflows/test.yml`, `apt-get` step).

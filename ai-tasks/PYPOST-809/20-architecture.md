# PYPOST-809: Transitive license inventory architecture

## Overview

Add a committed CSV inventory of all packages in the production lock (`requirements.txt`),
generated with pinned `pip-licenses` from the dev dependency lock. Verification mirrors the
PYPOST-778 / PYPOST-805 `security-audit` pattern: local Makefile target + dedicated CI job.

## Components

### 1. Dev lock source (`requirements-dev.in`)

| Property | Value |
| --- | --- |
| New direct dep | `pip-licenses>=5,<6` |
| Lock command | `make lock-dev` |
| Committed output | `requirements-dev.txt` (includes `prettytable` transitive dep) |

### 2. Generation script (`scripts/generate_license_inventory.py`)

| Property | Value |
| --- | --- |
| Input | `requirements.txt` package names (50 pinned transitive deps) |
| Tooling | `pip-licenses --format=csv --with-urls` on installed environment |
| Filter | Normalize PEP 503 names; keep rows matching production lock only |
| Output | `LICENSES/transitive.csv` |
| Check mode | Regenerate and byte-compare committed CSV (`--check`) |

Packages must be installed for `pip-licenses` metadata lookup. The script validates that every
lock entry appears in the filtered output.

### 3. Makefile targets

| Target | Prerequisites | Action |
| --- | --- | --- |
| `generate-license-inventory` | `install` | Write `LICENSES/transitive.csv` |
| `check-license-inventory` | `install` | `--check` (exit 1 on drift) |

`install` ensures production dependencies from `pyproject.toml` are present alongside dev
tooling (same graph as local development).

### 4. CI `check-license-inventory` job

| Step | Action |
| --- | --- |
| Install | `pip install -e ".[dev]"` (production + dev tooling) |
| Verify | `python scripts/generate_license_inventory.py --check` |
| Summary | Documents PYPOST-809 gate in GitHub Actions step summary |

Mirrors `security-audit` job structure (single Python 3.11 runner, pip cache on lock files).

## Data flow

```
requirements.txt  ──► parse package names (50)
        │
        ▼
pip-licenses (installed env) ──► CSV ──► filter ──► LICENSES/transitive.csv
        ▲
        │
pip-licenses CLI from requirements-dev.txt
```

## Out of scope

- Adding `check-license-inventory` to `make check` (remains opt-in like CVE scan).
- Auditing license compatibility or flagging copyleft beyond existing `licensing.md` guide.

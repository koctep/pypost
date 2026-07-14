# PYPOST-778: Developer Documentation

## Overview

CI and local tooling now scan production dependencies for known CVEs using
[pip-audit](https://pypi.org/project/pip-audit/).

## Usage

```bash
make security-audit   # after make install
```

CI job `security-audit` in `.github/workflows/test.yml` runs the same scan on Python 3.11 for
every push and pull request.

## Configuration

- **Input:** `requirements.txt` (production deps only)
- **Tool:** `pip-audit` installed ephemerally (not in `requirements.txt`)
- **Failure:** Non-zero exit when vulnerabilities are found

## Troubleshooting

| Symptom | Action |
| --- | --- |
| CI `security-audit` fails | Run `make security-audit` locally; upgrade affected package in `requirements.txt` |
| False positive / no fix available | Add documented `--ignore-vuln` exception (see `doc/dev/dependencies_audit.md`) |
| Scan differs locally vs CI | Ensure same Python major (3.11) and fresh `pip install -r requirements.txt` |

See also: [dependencies_audit.md](../../doc/dev/dependencies_audit.md)

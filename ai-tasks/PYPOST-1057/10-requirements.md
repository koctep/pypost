# PYPOST-1057: CI check-lock / check-lock-dev / check-license-inventory fail from dependency drift

## Programming Language

Python, uv requirements lockfiles, CSV, and English Markdown for documentation.

## Goals

CI jobs `check-lock`, `check-lock-dev`, and `check-license-inventory` run `uv pip compile` against PyPI without pinning transitive sub-dependencies in `requirements.in` / `requirements-dev.in`. As upstream packages publish newer versions (e.g. cffi, pydantic-settings, starlette, sse-starlette), clean resolution drifts from the committed lockfiles.

**Business goal:** Re-synchronize `requirements.txt`, `requirements-dev.txt`, `requirements-otel.txt`, and `LICENSES/transitive.csv` so all lock verification targets and license checks pass cleanly in local development and CI.

## Definition of Done

- [ ] `requirements.txt`, `requirements-dev.txt`, and `requirements-otel.txt` refreshed via `uv pip compile --upgrade`.
- [ ] `LICENSES/transitive.csv` regenerated to match production packages.
- [ ] `make check-lock`, `make check-lock-dev`, `make check-lock-otel`, and `make check-license-inventory` pass cleanly.

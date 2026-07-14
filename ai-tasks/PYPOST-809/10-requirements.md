# PYPOST-809: Generate transitive license inventory for releases

## Goals

PYPOST-691 audit finding L-003 noted no transitive license inventory in the repository.
PYPOST-786 documented PySide6 LGPL obligations but deferred SPDX/CSV attribution for all
production dependencies. This task adds a reproducible inventory workflow and commits the
output under `LICENSES/` for enterprise adopters and release packaging.

## User Stories

- **As a maintainer**, I want `pip-licenses` pinned in the dev lock so license inventory
  generation uses the same tooling version locally and in CI.
- **As a release engineer**, I want a committed CSV of all packages in `requirements.txt` with
  license names and URLs so attribution can ship with binaries or SBOM bundles.
- **As a contributor**, I want `make check-license-inventory` and a CI job to fail when the
  inventory drifts after production lock changes.

## Definition of Done

- [x] `pip-licenses` listed in `requirements-dev.in` and mirrored in `pyproject.toml` `[dev]`.
- [x] `requirements-dev.txt` regenerated with `make lock-dev`.
- [x] `scripts/generate_license_inventory.py` generates `LICENSES/transitive.csv`.
- [x] `generate-license-inventory` and `check-license-inventory` Makefile targets added.
- [x] `check-license-inventory` CI job added (mirrors `security-audit` install pattern).
- [x] `doc/dev/licensing.md` updated with inventory workflow.
- [x] `make check` and `make check-license-inventory` pass.

## Task Description

**Source:** PYPOST-786 follow-up — transitive license inventory (L-003)
([PYPOST-809](https://pypost.atlassian.net/browse/PYPOST-809)).

**Scope:** `requirements-dev.in`, `requirements-dev.txt`, `pyproject.toml`, `Makefile`,
`scripts/`, `LICENSES/`, `.github/workflows/test.yml`, `doc/dev/`.

**Out of scope:** Scanning dev or OTel lock graphs; SPDX SBOM JSON export; legal review of
license classifications (PYPOST-810).

**Constraints:**

- Inventory source of truth is the committed production lock (`requirements.txt`).
- Dev-only packages installed via `[dev]` must be excluded from the CSV.
- Regenerate inventory after `make lock` / `requirements.in` edits.

## Q&A

| Question | Answer |
| --- | --- |
| Output format? | CSV with Name, Version, License, URL (`pip-licenses --format=csv --with-urls`) |
| Why dev lock for tooling? | Same pattern as `pip-audit` (PYPOST-805) — maintainer/CI tooling, not runtime |
| Add to `make check`? | No — opt-in gate like `security-audit`; CI job provides drift detection |

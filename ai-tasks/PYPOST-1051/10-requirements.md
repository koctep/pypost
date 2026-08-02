# PYPOST-1051: Fix CI failures in run 30744058063 (check-license-inventory and check-lock)

## Goals

Ensure continuous integration build pipeline passes reliably on the main/dev branch by maintaining up-to-date dependency lock files and package license inventories.

## User Stories

- As a developer or release manager, I want the automated CI suite (`check-lock` and `check-license-inventory`) to succeed on target branches so that pull requests and automated workflow checks remain green and supply chain license auditing remains compliant.

## Definition of Done

- [ ] Production dependency lock file (`requirements.txt`) accurately reflects upstream dependency specifications (`requirements.in`).
- [ ] Transitive package license inventory (`LICENSES/transitive.csv`) matches production lock file declarations.
- [ ] CI validation commands (`make check-lock` and `make check-license-inventory`) execute cleanly without errors.

## Task Description

GitHub Actions run 30744058063 failed on the `dev` branch due to stale dependency lock files (`requirements.txt`) and associated transitive license declarations (`LICENSES/transitive.csv`). The goal is to synchronize lock files and license inventories to restore CI pipeline health.

## Q&A

- **Q**: What caused the CI failure?
- **A**: `requirements.txt` became stale relative to `requirements.in`, causing `make check-lock` to fail in CI, and package license inventories need to be regenerated to mirror the locked dependencies.

# PYPOST-923: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Restored `dev` CI hygiene: refreshed locks/inventory, smoke-job Qt/EGL apt
parity, and a fast workflow-contract test. No product-code changes. Items below
are non-blocking follow-ups.
**Do not create Jira tickets in this step** — Phase D / tech-debt sync fills
the Jira column later.

## Shortcuts Taken

- **Duplicated Qt/EGL apt YAML across three jobs.** Architecture deferred a
  shared composite/reusable action; Step 4 copied the peer package list into
  `make-install-smoke`. Acceptable scope discipline; drift is guarded by the
  contract test (TD-1).
- **Hardcoded peer package frozenset in the contract test.**
  `_PEER_QT_EGL_PACKAGES` in `tests/test_ci_make_install_smoke_qt_runtime.py`
  is the hard gate rather than deriving the expected set solely from live peer
  YAML. Matches architecture (“exact peer list”); maintainers must update the
  frozenset when the peer apt set grows (TD-2).
- **Did not change `tests/conftest.py` Qt import-at-collection.** Out of scope
  by requirements; environment parity is the intended fix. Lazy/deferred Qt
  import remains optional future work (TD-3).
- **Did not add a CI `check-lock` job for production.** Out of scope; inventory
  gate + local `make check-lock` remain the coverage for this ticket. Inherited
  from PYPOST-779 (TD-4).
- **YAML job-block parsing is heuristic.** `_job_block` / `_apt_packages_in_block`
  use indentation and token heuristics (same class as PYPOST-874 / PYPOST-861
  workflow contracts). Brittle if workflow layout changes radically (TD-5).

## Code Quality Issues

- **Triple copy of the apt install step** in `.github/workflows/test.yml`
  (`test`, `make-install-smoke`, `agent-e2e`). Contract test reduces risk but
  does not remove duplication (TD-1).
- **Peer equality checked against `agent-e2e` only.** The smoke contract asserts
  frozenset ⊆ `agent-e2e` and frozenset ⊆ smoke; it does not also assert the
  `test` job block still carries the same set. Today all three match; a future
  `test`-only edit could slip if `agent-e2e` stays unchanged (TD-2).
- **No application Python under `pypost/` changed.** No naming/structure debt in
  product modules from this ticket.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Smoke job has full peer Qt/EGL apt set (YAML contract) | Covered |
| `make-install-smoke` job exists in workflow | Covered |
| Explicit timeout markers on new contract module | Covered (`pytestmark` timeout 10) |
| Live GitHub Actions proof that smoke collection succeeds | Not covered — CI job itself is the integration signal |
| `make check-lock` / `check-lock-dev` / inventory via pytest | Not covered — Makefile/CI gates are the contract |
| Lazy conftest Qt import / collection without apt | Out of scope |
| Shared composite action for Qt apt | Not implemented — see TD-1 |

**No timeout-marker blockers.**

## Performance Concerns

None introduced for the product. Operator note only: once smoke collection
succeeds, the slow job runs the actual `-m slow` suite instead of failing at
import — wall time may increase slightly versus the prior red collection path.
That is expected Actions timing, not a code performance defect.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Low | Extract shared Qt/EGL apt install into a composite action (or reusable workflow step) used by `test`, `make-install-smoke`, and `agent-e2e` | Removes triple YAML copy; keep contract test or simplify it to assert composite usage | Jira: [PYPOST-924](https://pypost.atlassian.net/browse/PYPOST-924) |
| TD-2 | Low | Strengthen smoke Qt contract: derive expected package set from peer job YAML (and/or assert `test` + `agent-e2e` + smoke equality) instead of only a hardcoded frozenset | Reduces frozenset drift; still allow frozenset as documented minimum if useful | Jira: [PYPOST-925](https://pypost.atlassian.net/browse/PYPOST-925) |
| TD-3 | Lowest | Optionally defer `PySide6` import in `tests/conftest.py` so non-GUI collection paths do not require EGL/GL system libs | Explicitly out of scope for 923; would reduce env coupling for future jobs | Jira: [PYPOST-926](https://pypost.atlassian.net/browse/PYPOST-926) |
| TD-4 | Low | Add CI `check-lock` job for production `requirements.txt` (sibling of `check-lock-dev`) | Inherited from PYPOST-779 / architecture Q&A; inventory gate does not detect `.in`→`.txt` drift when CSV matches the stale lock | Jira: [PYPOST-927](https://pypost.atlassian.net/browse/PYPOST-927) |
| TD-5 | Lowest | Harden workflow YAML parsing helpers shared by CI contract tests (or adopt a tiny YAML subset parser) | Shared fragility with PYPOST-874-style tests; only worth it if more contract tests land | Jira: [PYPOST-928](https://pypost.atlassian.net/browse/PYPOST-928) |

### Already tracked / do not reticket as new work from this file alone

| Area | Owner / note |
| --- | --- |
| Production lock Makefile targets + local `check-lock` | [PYPOST-779](https://pypost.atlassian.net/browse/PYPOST-779) |
| Dev lock CI job | [PYPOST-804](https://pypost.atlassian.net/browse/PYPOST-804) (Done) |
| License inventory `--check` gate | [PYPOST-809](https://pypost.atlassian.net/browse/PYPOST-809) lineage |
| Workflow contract-test precedent | PYPOST-861 / PYPOST-874 |

TD-4 is the same class of debt called out in PYPOST-779/804 tech-debt docs; Phase D
should link or reticket only if no open Debt issue already covers production
`check-lock` CI.

### Planned this ticket (not separate Debt)

- Step 8: light `doc/dev/` note that `make-install-smoke` installs the same
  Qt/EGL runtime packages as the main matrix / `agent-e2e` (architecture §
  Implementation Plan item 5).

## User documentation

N/A for end-user `doc/user/` — this ticket is CI / supply-chain hygiene only.
Developer doc touch deferred to Step 8.

## Blocker review

**No blockers.** Timeout markers present; DoD gates (locks, inventory, smoke
parity contract, `make check`) are green per Steps 4–5. Safe to proceed to
Step 8 after Phase D debt sync (tickets optional for Low/Lowest items).

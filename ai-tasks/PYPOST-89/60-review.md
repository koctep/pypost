# Tech Debt Review: PYPOST-89 — CI Pipeline for Tests

**Ticket**: PYPOST-89
**Author**: Team Lead
**Date**: 2026-03-25
**Artifact reviewed**: `.github/workflows/test.yml`

---

## 1. Summary

The CI pipeline implementation is clean, minimal, and directly aligned with the requirements.
No regressions were introduced. The workflow file is the sole deliverable; no source code was
modified. All 7 acceptance criteria are satisfied. Observability was retroactively strengthened
(JUnit XML, job summary, test-results artifact) during STEP 5.

Overall tech debt introduced: **low**.

---

## 2. Strengths

| Strength | Detail |
|---|---|
| Mirrors local workflow | `pytest` command matches `make test-cov` exactly — CI/local parity maintained |
| Defence-in-depth Qt setup | `QT_QPA_PLATFORM=offscreen` at job level + `conftest.py` fallback |
| `fail-fast: false` | Both matrix legs always run; no premature abort hides a broken version |
| Pinned action major versions | `@v4`/`@v5` — stable and deterministic without over-pinning to SHAs |
| `if: always()` on upload steps | Artifacts available even when tests fail — critical for diagnosis |
| JUnit + job summary | Rich, structured observability added in STEP 5 beyond initial AC scope |
| No over-engineering | Single job, no custom Docker images, no secrets, no path filters |

---

## 3. Tech Debt Items

### TD-1 (LOW) — Action versions not pinned to full SHA

**Description**: Actions are pinned to major versions (`actions/checkout@v4`,
`actions/setup-python@v5`, `actions/upload-artifact@v4`) rather than immutable commit SHAs.
A compromised or accidentally broken major-version tag could silently change workflow behaviour.

**Risk**: Low — GitHub-owned actions have strong tag-integrity guarantees at the major version
level. SHA pinning is a supply-chain hardening concern, not a functional one.

**Recommendation**: Pin to full SHAs if/when the project adopts a security-hardening pass or
a Dependabot config for Actions version bumps. Not urgent.

**Tracking**: Can be folded into a future "harden CI supply chain" ticket.

---

### TD-2 (LOW) — `flake8` installed but never executed

**Description**: `pip install pytest pytest-cov flake8` installs `flake8`, but no workflow step
runs `flake8`. This was acknowledged as intentional in the architecture (FR-3 lists `flake8` as
a required install; linting is out of scope for this ticket per the non-goals).

**Risk**: Low — the install is cheap and harmless. However, it creates a false impression that
linting is gated in CI.

**Recommendation**: Either (a) add a `flake8` lint step in a follow-on ticket, or (b) remove
`flake8` from the install step if a lint gate is not planned. Do not leave it as dead weight
indefinitely.

**Tracking**: Create a follow-on ticket for a linting gate, or remove `flake8` install.

---

### TD-3 (LOW) — No concurrency cancellation group

**Description**: The workflow has no `concurrency:` block. Rapid pushes to the same branch
will queue multiple workflow runs rather than cancelling the superseded ones.

**Risk**: Low — wastes GitHub Actions minutes on abandoned runs but does not affect correctness.
Impact grows as the team scales.

**Recommendation**: Add a `concurrency` group (e.g. keyed on `${{ github.ref }}`) with
`cancel-in-progress: true` in a future cleanup ticket.

**Tracking**: Can be folded into a general CI hygiene ticket.

---

### TD-4 (LOW) — `--junit-xml` flag duplicates `addopts` pattern risk

**Description**: `pytest.ini` already injects `-v --tb=short` via `addopts`. The explicit
flags in the `pytest` command (`-v --tb=short`) are harmless duplicates, but the pattern
of specifying flags both in `pytest.ini` and in the workflow command can diverge over time
if `pytest.ini` is modified.

**Risk**: Low — currently benign, but could cause confusion if a future engineer changes
`pytest.ini` and expects the workflow to reflect the change automatically.

**Recommendation**: Document the intentional redundancy in a comment above the `Run tests`
step, or consolidate flags solely in `pytest.ini` and simplify the workflow command.

---

### TD-5 (MEDIUM) — No `--cov-fail-under` threshold enforced

**Description**: The coverage check is informational only. A pull request that drops coverage
to 0% will still pass CI. This is explicitly out of scope for this ticket (tracked in
PYPOST-88).

**Risk**: Medium — without a threshold gate, test coverage can silently erode in any merged PR.

**Recommendation**: Implement PYPOST-88 promptly. This is the highest-priority follow-on.

**Tracking**: PYPOST-88 already exists.

---

### TD-6 (LOW) — No branch-protection rule enforcing CI as a required check

**Description**: The workflow exists but GitHub repository branch-protection rules must be
configured manually in the GitHub UI to require the `test` job to pass before merging to `main`.
Without this, CI is advisory only.

**Risk**: Low-Medium — developers can merge failing PRs if branch protection is not configured.

**Recommendation**: Configure branch-protection rules in the repository settings to require the
`test` job status check on `main`. This is a one-time manual action in GitHub settings.

**Tracking**: Document in team onboarding or a separate infra ticket.

---

## 4. No-Action Items

The following were considered and deliberately left as-is:

| Item | Decision |
|---|---|
| `dorny/test-reporter` third-party action | Native JUnit + job summary is sufficient; avoids external dependency |
| Docker-based runner | `ubuntu-latest` is appropriate; no containerisation needed |
| Path filters on triggers | No path filters — any file change triggers tests (intentional, avoids blind spots) |
| Separate lint job | Out of scope; `flake8` install is the only foothold (see TD-2) |
| Coverage badge | Requires badge service; not requested |

---

## 5. Follow-On Tickets

| Priority | Action | Tracking |
|---|---|---|
| HIGH | Enforce coverage threshold (`--cov-fail-under`) | PYPOST-88 (existing) |
| MEDIUM | Configure branch-protection rules to require CI (TD-6) | New ticket or manual task |
| LOW | Add `flake8` lint step or remove `flake8` install (TD-2) | New ticket |
| LOW | Add concurrency cancellation group (TD-3) | CI hygiene ticket |
| LOW | Pin actions to full SHAs for supply-chain hardening (TD-1) | Security hardening ticket |

---

## 6. Verdict

**Approved with no blocking issues.** The implementation is production-ready as a CI foundation.
The 5 tech debt items identified are all low-to-medium severity and none block the current
delivery. PYPOST-88 (coverage threshold) is the only item with meaningful risk and is already
tracked.

# PYPOST-984: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

## Shortcuts Taken

- **Fix scoped to `check-lock` only, per DoD/architecture** — the `uv` version pin (CI) and the
  Makefile retry/diagnostics/cleanup hardening were applied exclusively to the production
  `check-lock` job/target. The sibling `check-lock-dev` CI job and the `check-lock-otel` Makefile
  target were deliberately left untouched, mirroring the PYPOST-927 precedent of scoping lock-gate
  changes narrowly (see `20-architecture.md` Q&A "Why not also touch `check-lock-dev` /
  `check-lock-otel`?"). This was the correct call for this incident (only `check-lock` failed) but
  it does mean the sibling gates remain exposed to the same two failure classes this task just
  fixed for `check-lock`.
- **`check-lock` is still not part of `make check`** — inherited, unresolved debt already
  identified in `ai-tasks/PYPOST-927/60-tech-debt.md`; contributors without `uv` on `PATH` can
  still run the default local quality gate. Unchanged by this task.

## Code Quality Issues

None blocking. The retry loop in `Makefile:46-73` (`check-lock`) is intentionally inline shell
(consistent with every other recipe in this Makefile) rather than a shared shell function/script,
so it is not reused by `check-lock-dev`/`check-lock-otel` — see Follow-up Tasks below for the
consequence of that duplication gap.

## Missing Tests

- No pytest exercises `make check-lock` (or the new retry loop) against a **real** `uv` binary
  with real network access — `tests/test_makefile_check_lock_retry.py` uses a fully offline fake
  `uv` script by design (per `20-architecture.md`, to keep Step 3/4 tests deterministic and
  network-free). The CI `check-lock` job itself remains the only integration-level exerciser of a
  real `uv pip compile` against real PyPI. This is an accepted, intentional trade-off (documented
  in architecture), not an oversight.
- No test asserts that `check-lock-dev`'s CI step lacks a `version:` pin (i.e. no regression guard
  documenting the current *sibling* gap) — see Follow-up Tasks.

## Performance Concerns

None. The retry loop only engages (and only adds wall-clock time: up to 1s + 2s backoff) on
transient `uv pip compile` failures; the common case (single successful compile) is unchanged in
cost from before this task.

## Follow-up Tasks

### HIGH — pin `uv` version on `check-lock-dev`

- **Jira:** [PYPOST-995](https://pypost.atlassian.net/browse/PYPOST-995)
- **Description:** `.github/workflows/test.yml`'s `check-lock-dev` job installs `uv` via the same
  `astral-sh/setup-uv` action but still has **no `version:` input** (lines 336-338), so it remains
  exposed to exactly the resolver-version-drift failure mode this task just fixed for `check-lock`.
  It happened not to fail in the PYPOST-984 incident only because `requirements-dev.in`'s
  disjoint dependency tree wasn't affected by whatever upstream release changed at that moment —
  that is luck, not a structural guarantee.
- **Remediation:** Add `version: "0.11.31"` (or whatever is current at implementation time) to the
  `check-lock-dev` job's `astral-sh/setup-uv` step, matching `check-lock`'s pin. Add a regression
  test alongside `tests/test_ci_check_lock_job.py::test_workflow_check_lock_setup_uv_step_pins_version`
  for the `check-lock-dev` job block.
- **Source:** Deferred from PYPOST-984 per architecture Q&A (explicit out-of-scope call); this is
  the same failure class already proven to occur in production, so priority is High rather than
  Low.

### MEDIUM — apply the retry/diagnostics/cleanup pattern to `check-lock-dev` and `check-lock-otel`

- **Jira:** [PYPOST-996](https://pypost.atlassian.net/browse/PYPOST-996)
- **Description:** `Makefile:78-93` (`check-lock-dev`, `check-lock-otel`) still run `uv pip
  compile` once with no retry, no distinct compile-failure-vs-drift message, and no scratch-file
  cleanup on failure (`requirements-*.txt.check`/`.body` are left behind if `diff -q` fails) —
  exactly the three gaps this task just closed for `check-lock`. The three recipes are now
  divergent copies of similar logic; `check-lock`'s recipe is meaningfully more robust than its
  two siblings.
- **Remediation:** Either (a) mechanically port the retry loop + distinct-message + cleanup
  pattern from `check-lock` to `check-lock-dev`/`check-lock-otel`, or (b) factor the shared logic
  into a small parameterized Make function/script (e.g. `scripts/check_lock.sh <in> <txt>
  <label>`) invoked by all three targets, removing the triplication entirely. Option (b) is
  preferable if a fourth lock file is ever added.
- **Source:** Deferred from PYPOST-984 (scope: "production `check-lock` gate only").

### LOW — add a CI job for `check-lock-otel`

- **Jira:** [PYPOST-997](https://pypost.atlassian.net/browse/PYPOST-997)
- **Description:** `requirements-otel.txt` drift relative to `requirements-otel.in` is only
  caught locally via `make check-lock-otel`; there is still no CI job enforcing it (no
  `astral-sh/setup-uv` step, no workflow job at all for this lock pair).
- **Remediation:** Add a `check-lock-otel` job to `.github/workflows/test.yml` mirroring
  `check-lock-dev`, including a pinned `uv` `version:` input from day one (avoiding introducing a
  fourth instance of the unpinned-version gap fixed here).
- **Source:** Originally identified in `ai-tasks/PYPOST-787/` and re-confirmed as outstanding in
  `ai-tasks/PYPOST-927/60-tech-debt.md`; still open after PYPOST-984 since it was out of scope for
  this incident fix.

### LOW — `check-lock` still absent from `make check`

- **Jira:** [PYPOST-998](https://pypost.atlassian.net/browse/PYPOST-998)
- **Description:** The default local quality gate (`make check` → `lint test verify-ai-tasks`,
  `Makefile:127`) does not include `check-lock`, so a contributor without `uv` on `PATH` (or who
  only runs `make check`) will not locally catch production lock drift before pushing — CI remains
  the sole enforcement point.
- **Remediation:** Either make `check-lock` a soft/optional prerequisite of `make check` (e.g. skip
  gracefully with a warning if `uv` is absent), or explicitly document in `doc/dev/setup.md` that
  `make check-lock` must be run separately before pushing dependency changes.
- **Source:** Inherited, unresolved from `ai-tasks/PYPOST-927/60-tech-debt.md`; unchanged by this
  task since it was not part of the DoD.

## Resolved debt

- The unpinned-`uv`-on-`check-lock` resolver-drift exposure and the `uv pip compile`
  transient-failure/opaque-diagnostics/scratch-file-leak gaps (both newly identified during this
  task's investigation) are closed for the production `check-lock` gate by this task's Step 4
  changes.

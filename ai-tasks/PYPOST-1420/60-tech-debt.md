# PYPOST-1420: Technical Debt Analysis

## Shortcuts Taken

1. **Soft post-copy `copy_timeout` (not preemptive cancellation)**:
   - `materialize` measures elapsed wall time via injected `_clock` **after**
     `tree_copier` returns. An in-flight `shutil.copytree` cannot be aborted.
   - Chosen per architecture option (a): keep the public `copy_timeout` API and
     treat overrun like the old timeout path without reintroducing a subprocess
     solely to honor hard cancellation. Acceptable for tiny skeleton trees;
   - A stuck/hanging copier would still block the calling thread until it returns.

2. **Silent skeleton → base fallback retained**:
   - `source = skeleton if self.is_ready(skeleton) else base` still falls back to
     a full base copy when the skeleton is missing or incomplete, without a
     distinct “template damaged” error. Deeper readiness remains PYPOST-1421.
   - Step 6 only added `source=skeleton|base` on failure messages; healthy
     fallback stays silent by design.

3. **Developer docs still describe `cp -a`**:
   - `doc/dev/shared_venv_materialization.md`, `doc/dev/testing.md`, and
     `doc/dev/parallel_test_runner.md` were intentionally left for Step 8.

4. **Underscore facades / late-bind shims unchanged**:
   - `_materialize_prewarmed_venv` and related helpers remain thin delegates
     (FR6). Retirement tracked as PYPOST-1440 from PYPOST-1419.

5. **Redundant `TimeoutError` in except tuple**:
   - Listed explicitly next to `OSError` for soft-deadline readability even
     though `TimeoutError` is an `OSError` subclass. Harmless; could be
     simplified later if a linter starts flagging it.

## Code Quality Issues

1. **Soft-deadline vs injected-failure overlap**:
   - FR5 suite injects a failing `tree_copier` that raises `TimeoutError` mid-copy.
   - The post-copy soft budget path (successful copy, then `elapsed > copy_timeout`)
     is implemented but not separately asserted with a frozen/advanced `_clock`.

2. **Exception message shape drift for consumers matching substrings**:
   - Failure text now includes `(source=…)` after the target path. Existing tests
     match `(?i)materialization` only; any external substring matchers that assumed
     the exact PYPOST-1419 wording could need a one-line update (none found in-repo).

3. **POSIX layout assumptions unchanged**:
   - `bin/python`, `lib/python{ver}/site-packages`, and static `pyvenv.cfg`
     fallback remain Unix-centric (carried from PYPOST-1413 / 1419).

4. **Facade + late-bind surface area**:
   - Unchanged from PYPOST-1419; still pending PYPOST-1440.

## Missing Tests

1. **Soft deadline with injected clock after successful copy** — no test advances
   `_clock` so that a successful `tree_copier` still trips
   `elapsed > copy_timeout` and asserts cleanup + `source=` / `elapsed=` fields.
2. **Corrupted / unreachable `_prewarmed_base.pth` recovery** — still owned by
   PYPOST-1421 (out of scope).
3. **Extreme concurrency (>4 workers under I/O throttle)** — still owned by
   PYPOST-1422; this task kept the existing 4-worker load-budget case green.
4. **Timeout markers**: scoped suites declare explicit `pytestmark` /
   `@pytest.mark.timeout` — **no BLOCKER** for missing timeouts in this change set.

## Performance Concerns

1. **Full-base fallback copy cost** — when skeleton is not ready, in-process
   `copytree` of the entire shared base is heavier than skeleton population
   (same class of issue as before; mitigated by keeping skeleton publication in
   `ensure_ready`). Soft timeout only observes overrun after the fact.
2. **Shared site-packages via `.pth`** — concurrent worker imports still hit one
   shared base tree; extreme NFS read spikes remain a residual risk (PYPOST-1422).
3. **Closed by this ticket**: per-workspace `cp -a` fork/exec overhead for
   population — replaced by in-process `tree_copier` / `copytree(..., symlinks=True)`.

## Follow-up Tasks

1. **Deep template validation in readiness** — already ticketed
   [PYPOST-1421](https://pypost.atlassian.net/browse/PYPOST-1421).
2. **Extreme concurrency stress for shared venv materialization** — already
   ticketed [PYPOST-1422](https://pypost.atlassian.net/browse/PYPOST-1422).
3. **Retire underscore facades / late-bind shims** — already ticketed
   [PYPOST-1440](https://pypost.atlassian.net/browse/PYPOST-1440).
4. **Optional: assert soft post-copy deadline via injected `_clock`** — low
   priority unit coverage for the successful-copy-then-overrun branch and the
   enriched `elapsed=` / `source=` diagnostics. Candidate follow-up only if
   reviewers want it ticketed; not filed in this batch (no failing suite evidence).
5. **Step 8 doc alignment** — replace residual `cp -a` narrative in `doc/dev/`
   (owned by this ticket’s Step 8, not a separate Debt issue).

No new failing-test NON-BLOCKER entries were opened during Steps 5–7: focused
`make test` on `tests/test_shared_venv_manager.py` and
`tests/test_makefile_shared_readiness.py` stayed green; `make lint` stayed clean.
Pre-existing NON-BLOCKER items from PYPOST-1419 (lockfile drift PYPOST-1397,
Qt worker teardown PYPOST-1441 / PYPOST-1442) were not re-exercised in this batch
and are not re-filed here.

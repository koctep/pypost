# PYPOST-1421: Technical Debt Analysis

## Shortcuts Taken

1. **Skeleton detection by directory name (`.skeleton`)**:
   - Existence of `_prewarmed_base.pth` is required when `venv.name == ".skeleton"`.
   - Renamed template directories would skip the existence rule (presence of a
     `.pth` is still validated). Acceptable because publication always uses
     `.skeleton` today.

2. **No dedicated “template damaged” exception / log line**:
   - Damaged templates return `is_ready == False`; `ensure_ready` rebuilds and
     `materialize` falls back to base using existing diagnostics.
   - Operators must infer damage from rebuild/fallback behavior or manual
     `.pth` inspection (documented in `doc/dev/shared_venv_materialization.md`).

3. **First path-line only in `.pth` parsing**:
   - Mirrors `build_skeleton` (single absolute path line). Comment / `import `
     lines are skipped; additional path lines after the first are ignored.

4. **Underscore facades unchanged**:
   - `_venv_ready` remains a thin delegate (FR continuity). Retirement still
     tracked elsewhere (e.g. PYPOST-1440 from PYPOST-1419).

## Code Quality Issues

1. **POSIX layout assumptions unchanged**:
   - `bin/python`, `lib/python{ver}/site-packages` remain Unix-centric
     (carried from PYPOST-1413 / 1419 / 1420).

2. **`os.access(..., R_OK)` race**:
   - Readability is checked at readiness time; the target could disappear
     before interpreter startup. Same TOCTOU class as marker checks; acceptable
     for harness use.

3. **Workspace `.venv` without `.pth`**:
   - A materialized tree named `.venv` that lost its `.pth` but kept marker +
     interpreter still passes readiness (existence rule is skeleton-named).
     Present `.pth` files are still validated. Broader “workspace must retain
     redirect” policy was left out of scope.

## Missing Tests

1. **Unreadable `.pth` file / unreadable target directory permissions** —
   covered conceptually via `OSError` / `os.access` paths but not exercised
   with chmod-based fixtures on all platforms.
2. **`ensure_ready` rebuild integration for damaged on-disk skeleton** —
   implied by `not is_ready(skeleton)` → `build_skeleton`, but no dedicated
   DI test mutates a published skeleton’s `.pth` then asserts rebuild.
3. **Extreme concurrency (>4 workers under I/O throttle)** — still owned by
   PYPOST-1422; this task kept the existing 4-worker load-budget case green.
4. **Timeout markers**: scoped suites declare explicit `pytestmark` /
   `@pytest.mark.timeout` — **no BLOCKER** for missing timeouts in this change set.

## Performance Concerns

1. **Base fallback copy cost when skeleton fails deep readiness** — intentional
   fail-closed behavior; heavier than skeleton copy until `ensure_ready`
   republishes a healthy template.
2. **Extra `read_text` / `is_dir` / `os.access` per readiness check** —
   negligible vs copy/bootstrap; no concern for CI scale.
3. **Shared site-packages via `.pth`** — concurrent worker imports still hit
   one shared base tree; extreme NFS read spikes remain a residual risk
   (PYPOST-1422).

## Follow-up Tasks

1. **Optional louder “template damaged” diagnostic** — emit a distinct WARNING
   or materialize message when skeleton fails deep `.pth` validation, without
   changing fail-closed behavior.
   Jira: [PYPOST-1443](https://pypost.atlassian.net/browse/PYPOST-1443).
2. **Dedicated `ensure_ready` rebuild test for corrupted `.pth`** — DI test that
   seeds a ready base + damaged skeleton and asserts republish.
   Jira: [PYPOST-1444](https://pypost.atlassian.net/browse/PYPOST-1444).
3. **Extreme concurrency stress for shared venv materialization** — already
   ticketed as [PYPOST-1422](https://pypost.atlassian.net/browse/PYPOST-1422)
   (do not duplicate).
4. **Retire underscore facades / late-bind shims** — already ticketed as
   [PYPOST-1440](https://pypost.atlassian.net/browse/PYPOST-1440) from PYPOST-1419
   (do not duplicate).
5. **Windows / non-POSIX layout readiness** — Scripts/Lib paths if the harness
   ever supports Windows materialization.
   Jira: [PYPOST-1445](https://pypost.atlassian.net/browse/PYPOST-1445).

# PYPOST-984: CI check-lock fails: production requirements.txt drift on push to dev

## Goals

The `check-lock` gate (added in PYPOST-927) exists so that maintainers can trust a green CI run
as proof that the committed production dependency lock (`requirements.txt`) truly matches its
source (`requirements.in`). On 2026-08-01, this gate failed on a push to `dev`
([workflow run](https://github.com/koctep/pypost/actions/runs/30704113521)) even though the
triggering commit (`34b1cdc`, PYPOST-947) did not touch `requirements.in` or `requirements.txt`,
and every other job in the same run passed.

If the gate can go red without any real dependency change, the team loses confidence in it:
maintainers start treating `check-lock` failures as "probably noise" rather than a real signal,
which defeats the purpose PYPOST-927 was built for and wastes engineering time re-running or
manually investigating builds that were never actually broken. The business goal is to restore
and preserve trust in the `dev` branch CI signal — a red `check-lock` job must mean the lock is
genuinely out of date, and pushes that do not change dependencies must reliably stay green.

## User Stories

- **As a contributor pushing unrelated changes to `dev`**, I want the `check-lock` job to stay
  green when I have not touched dependency files, so that I am not blocked or distracted by
  unrelated CI noise.
- **As a maintainer**, I want to know with confidence whether a `check-lock` failure means
  `requirements.txt` is genuinely stale, or whether it was a false positive, so I can decide
  correctly between "regenerate the lock" and "ignore/retry."
- **As a maintainer**, I want the root cause of this specific failure (stale lock content vs.
  drift in the lock-compiling tool's output vs. a transient CI/network hiccup) identified and
  recorded, so the fix addresses the actual cause instead of masking symptoms.
- **As a maintainer**, I want the `check-lock` gate to keep detecting real drift between
  `requirements.in` and `requirements.txt` after this fix, so the PYPOST-927 protection is not
  weakened while making it more stable.
- **As a reviewer of this task**, I want `make check-lock` locally and the CI `check-lock` job on
  `dev` both confirmed green afterwards, so the fix is verifiably complete.

## Definition of Done

- The failing CI run has been reproduced or its cause otherwise conclusively diagnosed using the
  same commit and equivalent tooling to the CI job.
- The root cause is classified as one (or a documented combination) of:
  - the committed `requirements.txt` was genuinely stale relative to `requirements.in`, or
  - the lock-compiling tool produced different output for the same inputs (tool version drift or
    non-determinism), or
  - the CI run failed for reasons unrelated to lock content (transient network/environment issue).
- A corrective action appropriate to the diagnosed cause has been identified and applied
  (e.g., refreshing the lock, and/or making the gate stable against tool-version drift or
  transient failures), without removing the gate's ability to catch genuine drift.
- `make check-lock` succeeds locally against the current `dev` HEAD.
- The `check-lock` GitHub Actions job succeeds on `dev` after the fix is merged.
- Any relevant developer documentation describing the lock/check-lock workflow
  (`doc/dev/setup.md`) remains accurate after the fix.

## Task Description

**Problem:** The `check-lock (requirements.txt)` job in `.github/workflows/test.yml` (job
defined at PYPOST-927) failed on a push to `dev` at commit `34b1cdc` ("feature(agent): PYPOST-947
Add optional delay to keyClicks fill"). The failing step, `Verify production lock file matches
source`, runs `make check-lock` and exited with code 2. This commit did not modify
`requirements.in` or `requirements.txt`, and no other job in the same workflow run failed
(including the sibling `check-lock-dev` job, which compiles `requirements-dev.txt` in the same
run and succeeded).

**Why this matters (business context):** `check-lock` is a merge-confidence gate: it tells
maintainers whether the dependency lock committed to the repository still matches its declared
source of truth, without which dependency drift could silently reach production installs
(`pip install -e .` / packaging). A gate that fails on commits unrelated to dependencies
undermines that confidence and creates avoidable investigation overhead for whoever is on point
for `dev` health.

**Scope (this task):**

- Investigate why this specific `check-lock` run failed on a commit that does not touch
  dependency files.
- Determine which of the three candidate causes from the Jira description applies: stale lock
  content, drift in the compiled output produced by the lock tool (e.g., version-to-version
  behavior differences), or a transient CI/network condition.
- Restore a green `check-lock` job on `dev` and confirm the local `make check-lock` command is
  also green, without weakening the check's ability to catch real `requirements.in` /
  `requirements.txt` drift.
- Keep documentation in `doc/dev/setup.md` describing the lock workflow consistent with any
  change made.

**Out of scope:**

- Changing which production dependencies are declared in `requirements.in` (no new/removed/
  upgraded packages unless required to restore a passing lock).
- Changes to the dev lock (`requirements-dev.in` / `.txt`) or OTel lock
  (`requirements-otel.in` / `.txt`) workflows — that run passed and is unaffected.
- Any change to unrelated CI jobs (`test`, `agent-e2e`, `make-install-smoke`, `security-audit`,
  `check-license-inventory`) that already passed on the same run.
- Broader CI reliability work beyond this specific gate.

**Constraints and assumptions:**

- The fix must preserve the original intent of PYPOST-927: `check-lock` must still fail whenever
  a committed `requirements.txt` genuinely does not match what compiling `requirements.in`
  produces.
- The existing two-file lock convention (`requirements.in` as source of truth,
  `requirements.txt` as the committed compiled lock) must be preserved.
- Any tooling change should keep local (`make check-lock`) and CI behavior in parity, per the
  existing documented expectation in `doc/dev/setup.md`.
- Investigation is time-boxed to this one incident; a full audit of all CI gates for similar
  drift risk is out of scope unless directly needed to fix this issue.

## Main Entities and Interactions

- **`requirements.in`** — the source-of-truth file where maintainers declare production
  dependencies (unpinned/loosely pinned).
- **`requirements.txt`** — the committed, fully-resolved lock file that must exactly match what
  compiling `requirements.in` produces; this is what `pip install -e .` / packaging consumes.
- **Lock-compiling tool** (`uv pip compile`) — reads `requirements.in` and generates the resolved
  lock content; its version/behavior determines whether repeated compilations are reproducible.
- **`check-lock` CI gate** — a job in `.github/workflows/test.yml` that re-runs the lock-compiling
  tool against `requirements.in` and diffs the result against the committed `requirements.txt`,
  reporting pass (in sync) or fail (drift/error) back to the pull request or `dev` push.
- **`dev` branch** — the shared integration branch whose CI status (including `check-lock`)
  maintainers rely on as a health signal.
- **Maintainers/contributors** — push commits to `dev`, read the `check-lock` result, and decide
  whether to regenerate the lock, investigate further, or trust a green result.

Interaction flow: a contributor pushes a commit to `dev` → CI triggers the `check-lock` gate →
the gate invokes the lock-compiling tool on `requirements.in` → the gate compares the fresh
output to the committed `requirements.txt` → the pass/fail result is surfaced to maintainers as
the signal of whether the two files are in sync.

## Non-Functional Requirements

- **Reliability/determinism**: for a given, unchanged `requirements.in` and lock-compiling tool
  version, the `check-lock` gate must produce the same pass/fail result on every run — it must not
  fail intermittently (flake) for commits that do not touch dependency files, and it must not pass
  when a genuine mismatch exists. Any dependency the gate has on external, unpinned tooling
  versions is a determinism risk to be accounted for in diagnosis and fix.

## Q&A

**Q:** Did the failing commit change `requirements.in` or `requirements.txt`?

**A:** No — confirmed via `git diff 34b1cdc -- requirements.in requirements.txt` against current
tree (no differences), and the Jira description states the commit only touches agent UI test-fill
behavior (PYPOST-947).

**Q:** Does `requirements.txt` currently match `requirements.in` when compiled locally?

**A:** Yes — reproducing
`uv pip compile requirements.in -o requirements.txt --python-version 3.11` locally (uv 0.11.31)
and diffing against the committed `requirements.txt` body shows no differences, i.e. no
stale-lock content is currently reproducible.

**Q:** Did the sibling dev-lock job fail in the same run?

**A:** No — `check-lock-dev (requirements-dev.txt)` succeeded in the same workflow run, so this is
isolated to the production lock check, not a repo-wide `uv`/network outage that run.

**Q:** What was the failing job's exact error output?

**A:** Not retrievable: GitHub's log-download API returned "Must have admin rights to Repository"
for this public repo without authenticated `gh`/token access in this environment, and the web UI
requires sign-in to view logs. Only the check-run annotation ("Process completed with exit code
2") was retrievable via the public API. Exit code 2 is `make`'s generic recipe-failure code and
does not by itself distinguish a real `diff` mismatch (which `diff -q` reports as exit 1) from an
earlier failure in the recipe (e.g., `uv pip compile` itself erroring).

**Q:** Is the `uv` version used by CI pinned?

**A:** No — `.github/workflows/test.yml` pins the `astral-sh/setup-uv` **action** to a commit SHA
(`v8.3.2`), but does not pass a `version:` input, so the actual `uv` **binary** installed is
whatever is latest at run time. This is a candidate mechanism for compiled-output drift between
runs (recorded here for the architecture/investigation step; no fix decided yet — that is
Step 2+).

**Q:** Where is the CI job defined?

**A:** `.github/workflows/test.yml`, job `check-lock`, step `Verify production lock file matches
source`, which runs `make check-lock` (target defined in root `Makefile`).

**Q:** Where is prior context on this gate?

**A:** `ai-tasks/PYPOST-927/` (introduced the job) and `doc/dev/setup.md` § "Dependency lock file
(PYPOST-779)" (documents the two-file convention and the `make lock` / `make check-lock`
commands).

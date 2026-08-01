# PYPOST-984: CI check-lock fails: production requirements.txt drift on push to dev

## Research

- **Makefile `check-lock` target** (`Makefile:46-51`) is the sole implementation shared by CI and
  local devs: it runs `$(UV) pip compile requirements.in -o requirements.txt.check
  --python-version $(LOCK_PYTHON_VERSION)` once, strips the 2-line `uv`-generated header from both
  the committed `requirements.txt` and the fresh `requirements.txt.check` via `tail -n +3`, then
  `diff -q`s the bodies. `UV ?= uv` is overridable, which matters for Step 3 testability (a fake
  `uv` script can be substituted via `make check-lock UV=...` without touching `PATH`).
  Header-only differences (e.g. a `--python-version` in the recorded command comment) cannot cause
  the failure because the header lines are stripped before diffing — ruled out as a cause.
- **`.github/workflows/test.yml` `check-lock` job** (lines 307-325) installs `uv` via
  `astral-sh/setup-uv@11f9893b...` (action pinned by SHA) with **no `version:` input**, then runs
  `make check-lock`. Per Astral's own docs (`docs/guides/integration/github.md`,
  `astral-sh-uv.mintlify.app/integrations/github-actions`), omitting `version:` installs whatever
  `uv` release is "latest" *at that exact CI run*, and Astral explicitly recommends pinning it
  ("best practice to pin to a specific uv version"). The sibling `check-lock-dev` job has the
  identical unpinned pattern.
- **`requirements.in`** (production) declares two open-ended ranges — `pydantic>=2.11,<3` and
  `mcp>=1.27,<2` — whose resolved transitive closure can legitimately change over time as new
  compatible releases land on PyPI, independent of any commit to this repo. `requirements-dev.in`
  also has open ranges (`pytest>=8,<9`, `mypy>=1.15,<2`, etc.) but resolves a disjoint dependency
  tree, so a release affecting the production tree would not necessarily affect the dev tree —
  this explains why `check-lock-dev` passed in the same run without ruling out drift as a cause
  for `check-lock`.
- **Git history**: `requirements.in`/`requirements.txt` last changed at `20661a7` (PYPOST-923),
  many commits before the failing `34b1cdc` (PYPOST-947, agent UI test-only change). No commit
  between them touched either file, and 10-requirements.md Q&A already confirms
  `uv pip compile requirements.in` (local `uv 0.11.31`) currently reproduces the committed
  `requirements.txt` byte-for-byte. **This rules out a permanently stale lock**: if the committed
  lock were genuinely out of date relative to today's `requirements.in`, recompiling now would
  still show a diff, and it does not.
- **CI log access**: the exact `make check-lock` failure output (compile error vs. diff mismatch)
  is not retrievable without repo-admin GitHub access (documented in 10-requirements.md Q&A), so
  the specific failure mode (compile-step error vs. genuine body diff) cannot be confirmed
  directly from logs. The architecture below is designed to be robust to either.
- **Prior art — PYPOST-927** (`ai-tasks/PYPOST-927/20-architecture.md`) introduced the
  `check-lock` job mirroring `check-lock-dev` (PYPOST-804) and explicitly deferred
  `check-lock-otel` and any local `make check` integration as non-blocking debt — establishing
  the project's precedent of scoping lock-gate changes narrowly and tracking siblings as follow-up
  tech debt rather than fixing all three lock gates atomically.
- **Existing test conventions**: `tests/test_ci_check_lock_job.py` already asserts (via
  `tests/helpers/ci_workflow_yaml.workflow_job_block`, pure YAML parsing, no network) that the
  `check-lock` job installs `uv` via the pinned action and runs `make check-lock`. This is the
  natural place to add a new assertion for a pinned `version:` input. `tests/test_makefile.py`
  already has a `make_workspace` fixture pattern (copy `Makefile` into `tmp_path`, run
  `make ... ` via subprocess with variable overrides) that can be reused to drive
  `make check-lock` against a stubbed `uv` executable, fully offline.

## Implementation Plan

Two independent, additive changes to the `check-lock` gate only (per DoD/out-of-scope:
`check-lock-dev`/`check-lock-otel` are untouched and tracked as follow-up debt in Step 7):

1. **Pin the `uv` version used by the `check-lock` CI job.** Add a `version: "<pinned>"` input to
   the existing `astral-sh/setup-uv` step in the `check-lock` job of `.github/workflows/test.yml`
   (pattern confirmed current/recommended via Astral's GitHub Actions integration docs, Step 2
   research above). Pin to the latest stable `uv` release verified at implementation time to
   reproduce a match against the committed `requirements.txt` (currently `0.11.31` locally; Step 4
   re-verifies against whatever is current then). Cross-reference the pinned version from
   `doc/dev/setup.md` § "Dependency lock file" so local contributors running `make lock` /
   `make check-lock` know which `uv` release to install for local/CI parity (NFR requirement) —
   the workflow YAML remains the single source of truth; the doc points at it rather than
   duplicating the version number in a second enforced location.
2. **Make the Makefile `check-lock` recipe distinguish a tool/network failure from a genuine lock
   mismatch, and retry transient `uv pip compile` failures.** Wrap the `uv pip compile` invocation
   in a small retry loop (e.g. up to 3 attempts with a short backoff) so a one-off network/PyPI
   blip does not fail the gate outright — this directly targets the "transient CI/environment
   issue" candidate cause and runs identically for local devs and CI since it lives in the shared
   Makefile target. After retries are exhausted, emit a clear `uv pip compile failed after N
   attempts (network or tool issue)` message distinct from the existing `diff -q` failure so a
   future incident's root cause is diagnosable from the job log alone, without needing GitHub
   admin log access (closing the exact investigation gap hit in Step 1). Also fix the latent
   cleanup gap where a failing `diff -q` currently leaves `requirements.txt.check`/`.body` scratch
   files behind (the final `rm -f` only runs on the success path today).

Both changes preserve `check-lock`'s ability to fail on genuine drift: change 1 removes a source of
non-genuine failure (resolver-version non-determinism) without touching the diff logic; change 2
only retries the compile step and only changes messaging/cleanup around the diff step, never its
outcome.

**Mandatory — Failing Repro (next Step 3):** Two automated red tests, both fully offline (no live
network/PyPI dependency), sequenced research → red tests → fix until green:

1. **CI contract test** — extend `tests/test_ci_check_lock_job.py`
   (`test_workflow_has_production_check_lock_job`, or a new sibling test in the same file) to
   assert the `check-lock` job's `astral-sh/setup-uv` step block contains a `version:` key with a
   non-empty value, reusing the existing `workflow_job_block` YAML-parsing helper. This fails today
   (no `version:` input exists) and turns green once change 1 lands. Pure static YAML assertion —
   no `uv` invocation, no network.
2. **Makefile retry/diagnostics test** — new `tests/test_makefile_check_lock_retry.py` using the
   `make_workspace`-style fixture from `tests/test_makefile.py`: seed a minimal `requirements.in`
   / `requirements.txt` pair and a fake `uv` executable (a small shell/Python script on a path
   passed via `UV=<path>`, per the Makefile's existing `UV ?= uv` override) that records its
   invocation count to a file and can be configured to fail its first N invocations before
   succeeding, or to always fail. Assertions (all via `subprocess.run(["make", "check-lock",
   f"UV={fake_uv}"], cwd=workspace, ...)`, no real `uv`/network):
   - fake `uv` fails twice then succeeds → `make check-lock` still exits 0 (retry recovers).
   - fake `uv` always fails → `make check-lock` exits non-zero with the new "compile failed"
     message (not the diff-mismatch message), and no `requirements.txt.check`/`.body` scratch
     files remain in the workspace afterward.
   - fake `uv` succeeds but emits content that differs from committed `requirements.txt` → exits
     non-zero with the diff-mismatch message (regression guard that genuine drift is still caught).
   These fail today because the recipe has no retry loop, no distinguishing messages, and no
   failure-path cleanup; they turn green once change 2 lands.

## Architecture

### Components

| Component | Responsibility |
| --- | --- |
| `test.yml` `check-lock` job | Install a pinned `uv`, delegate to `make check-lock` |
| Makefile `check-lock` target | Recompile `requirements.in`, retry transient failures, diff |
| `doc/dev/setup.md` | Cross-reference the pinned `uv` version for local/CI parity |
| CI contract test | Prevent regression — `version:` pin must be present |
| Makefile retry/diagnostics test (new) | Prevent regression — retry, message, cleanup behavior |

### Module interaction

```text
test.yml (check-lock job)
   │
   ├── checkout
   ├── astral-sh/setup-uv (pinned SHA + pinned `version:` input)  [CHANGE 1]
   ├── make check-lock ──┐
   └── job summary       │
                         ▼
              Makefile `check-lock` target
                         │
          ┌──────────────┴───────────────┐
          ▼                               ▼
   retry loop around              diff stripped bodies
   `uv pip compile`               vs. committed
   (up to N attempts,             requirements.txt
   backoff)  [CHANGE 2]           [unchanged semantics]
          │                               │
   exhausted → distinct           mismatch → distinct
   "compile failed" msg,          "lock stale" msg
   scratch files cleaned          (unchanged outcome)
   up  [CHANGE 2]
```

### Dependency graph

```text
requirements.in
   │  uv pip compile (pinned uv version)
   ▼
fresh transitive resolution
   │  diff vs. committed requirements.txt
   ▼
pass/fail signal
```

### Selected patterns and justification

- **Single source of truth, shared by CI and local dev**: the fix stays entirely inside the
  existing Makefile target (`check-lock`) and the existing CI step (`astral-sh/setup-uv`), adding
  parameters rather than new abstractions — this is the minimal-risk approach consistent with the
  "no broader CI reliability work" constraint and preserves the PYPOST-927 design of "CI job is a
  thin wrapper around a Makefile target."
- **Retry-with-backoff at the tool-invocation boundary** (not a workflow-level `retry` action or
  cron re-run) — keeps local (`make check-lock`) and CI behavior identical, per the NFR's
  determinism/parity requirement, and needs no new GitHub Actions dependency.
- **Fail-closed on diff mismatch, fail-soft (retry) on compile error**: the diff step's outcome is
  never retried or suppressed, preserving PYPOST-927's core guarantee that genuine drift is always
  caught; only the network-dependent compile step gets resilience.
- **Version pin cross-referenced, not duplicated**: `doc/dev/setup.md` points at the workflow YAML
  rather than hard-coding the same version number in two enforced places, avoiding a second drift
  vector (docs vs. workflow disagreeing about which `uv` version is authoritative).

### Interfaces

- `make check-lock` — unchanged CLI contract (no new required arguments); `UV` remains the
  existing override variable, now also the seam used by the Step 3 test to inject a fake `uv`.
- `.github/workflows/test.yml` `check-lock` job — unchanged trigger/output contract (still one
  pass/fail check named `check-lock (requirements.txt)`); only the `astral-sh/setup-uv` step
  gains a `version:` input.

## Q&A

**Q:** Root cause classification?

**A:** Primarily candidate 2 (lock-tool version drift, from unpinned `uv` in CI) and/or
candidate 3 (transient compile-step failure). Candidate 1 (permanently stale lock) is ruled out
by the Step 1 local-repro Q&A showing today's `requirements.in` still compiles to today's
committed `requirements.txt`.

**Q:** Why fix both drift and transience together instead of picking one?

**A:** The exact failure mode is unrecoverable from CI logs (Step 1 Q&A — no admin log access),
so the architecture must be robust to either without over-scoping. Both fixes are small,
additive, and independently covered by the Step 3 tests.

**Q:** Why not also touch `check-lock-dev` / `check-lock-otel`?

**A:** Explicitly out of scope per `10-requirements.md` ("that run passed and is unaffected").
Tracked as follow-up debt in Step 7, mirroring the PYPOST-927 precedent of deferring lock-gate
siblings.

**Q:** Why not add hashes or switch resolver mode?

**A:** Out of scope — the DoD forbids changing which dependencies are declared; this task fixes
gate stability, not the resolution strategy.

**Q:** Confirmed pin mechanism?

**A:** `astral-sh/setup-uv`'s `version:` input, documented and recommended by Astral
(`docs/guides/integration/github.md`, `astral-sh-uv.mintlify.app/integrations/github-actions`,
retrieved 2026-08-01).

**Q:** Is the Step 3 retry test achievable fully offline?

**A:** Yes — the Makefile's existing `UV ?= uv` override (already present, unrelated to this
task) lets tests substitute a fake `uv` script with no network or real `uv` binary involved,
following the `make_workspace` fixture pattern already used in `tests/test_makefile.py`.

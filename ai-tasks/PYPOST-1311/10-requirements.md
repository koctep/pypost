# PYPOST-1311: Flaky env persistence e2e temp-dir cleanup under full-suite load

## Goals

Maintainers and contributors rely on Make quality gates (`make check` / `make test`) to
trust that environment persistence and encryption-key handling remain correct. During
PYPOST-1297 (sprint 2021), a flaky failure appeared on one environment-persistence
end-to-end check: after the scenario’s assertions, temporary workspace cleanup fails with
`OSError: [Errno 39] Directory not empty`. The failure showed up under a full-suite
`make check` run; focused reruns of the same file often pass, including many isolated
runs on an unchanged base tree that does not touch environment code.

That pattern makes the gate unreliable for a security-sensitive coverage path: encrypted
environments must not appear when the encryption key is missing. Time is lost triaging
cleanup noise, and confidence in environment persistence / encryption coverage drops.

**Business goal**: restore a trustworthy quality signal for the environment-persistence
e2e suite by eliminating the intermittent temporary-workspace cleanup failure on the
named scenario, keeping the product assertion that no environment is shown when the key
is missing for encrypted data, and proving focused and full-suite Make runs complete
without that cleanup error (and without skips or weakened checks).

**Implementation language**: Python.

## User Stories

- **US1 (maintainer, quality gate)**: As a maintainer running `make check` or parallel
  `make test`, I want the environment-persistence e2e scenario for “key missing on
  encrypted data” to finish with a normal pass or fail, so a green or red suite is not
  overturned by temporary-workspace cleanup failing with “Directory not empty.”
- **US2 (contributor, focused reruns)**: As a contributor running focused environment
  persistence e2e tests through Make, I want the same stable completion as in the full
  suite, so local and CI results agree and I am not chasing load-only flakes.
- **US3 (maintainer, coverage integrity)**: As a maintainer, I want the existing product
  assertion preserved—when encryption is enabled and the key is missing for already
  encrypted environment data, the presenter load path shows no environment—so fixing the
  flake does not trade stability for lost security coverage.
- **US4 (maintainer, timeout integrity)**: As a maintainer, I want existing pytest timeout
  markers on the affected test(s) retained, so stability is not achieved by removing or
  disabling timeout enforcement.
- **US5 (maintainer, evidence)**: As a maintainer, I want bounded, reproducible evidence
  that the cleanup failure class is addressed under conditions comparable to full-suite
  load, so acceptance is not a single lucky focused green run.

## Definition of Done

1. **Cleanup failure eliminated.** Automated runs no longer fail the named scenario
   because temporary workspace cleanup raises `OSError: [Errno 39] Directory not empty`
   (or an equivalent “directory not empty” cleanup error) after the scenario’s product
   checks. In-scope identifier:
   - File: `tests/test_env_persistence_e2e.py`
   - Test: `test_presenter_load_shows_no_env_when_key_missing_for_encrypted_data`
2. **Product assertion preserved.** The scenario still proves that loading environments
   with encryption enabled and a missing key for encrypted data yields no environment
   shown to the user/presenter. That check is not skipped, deleted, or rewritten away
   solely to hide the cleanup flake.
3. **Timeout markers preserved.** Existing pytest timeout markers (per-test or
   module/class `pytestmark`) on the affected test(s) remain; stability is not achieved
   by removing or disabling timeout enforcement.
4. **No skips.** Validation does not rely on skipping the named test or the
   environment-persistence e2e module.
5. **Focused Make validation.** Focused Make runs of
   `tests/test_env_persistence_e2e.py` (including the named test) complete successfully
   without the temporary-workspace cleanup failure class.
6. **Full-suite / parallel Make validation.** Full-suite or parallel Make runs used for
   acceptance (including forms equivalent to `make check` with the project’s normal
   worker settings) complete without the named test failing via the “Directory not empty”
   temporary-workspace cleanup error.
7. **Bounded load evidence.** Acceptance includes bounded repeated or full-suite Make
   evidence sufficient for this intermittent class (historically seen under full-suite
   load while often passing in isolation), not only a single focused green run.
8. **Repository gates.** Quality gates are exercised only through `make` targets; no new
   failures attributable to this task remain in the accepted validation runs.

## Task Description

### Problem

Under full-suite load, the environment-persistence e2e check that verifies “no
environment shown when the encryption key is missing for encrypted data” can fail during
temporary workspace teardown with `OSError: [Errno 39] Directory not empty`. The failure
is raised while cleaning up the scenario’s temporary directory after the run, not as a
failed product assertion about missing-key behavior.

Exact identifier:

- File: `tests/test_env_persistence_e2e.py`
- Test: `test_presenter_load_shows_no_env_when_key_missing_for_encrypted_data`

Documented reproduction avenues (for later verification, not for this requirements step
to execute):

- Full suite: `make check` (default workers) — historically failed 1 of 1 observed
  full-suite run when discovered.
- Focused: `make test WORKERS=1 PYTEST_ARGS='tests/test_env_persistence_e2e.py -q'` —
  often passes; reported 3/3 reruns on the PYPOST-1297 tree and 15/15 isolated runs at
  base `286b3a4c` (that work did not touch environment code).

Classification is flaky by load-vs-isolation and unchanged-tree evidence, not a claim of
a deterministic single-run baseline failure in isolation.

Ticket notes also record that the failure was observed right after an environment storage
async-load activity log line, and suspect unfinished background work still using the
temporary workspace when cleanup runs. That note is investigative context for later
steps, not a mandated design.

### Business reason

A quality gate that fails on temporary-workspace cleanup after (or instead of) an honest
product result is a false or noisy signal. It blocks delivery, burns investigation time,
and undermines trust in coverage that protects a security-sensitive rule: encrypted
environment secrets must not surface when the key is unavailable. The business need is
stable, honest proof that that rule still holds—not a workaround that drops the test or
softens timeouts.

### Implementation language

Python.

### Scope

- Eliminate the intermittent temporary-workspace cleanup failure (“Directory not empty”)
  for the named environment-persistence e2e scenario under focused and full-suite /
  parallel Make runs.
- Retain the product meaning of the scenario: no environment shown when encryption is
  enabled and the key is missing for encrypted data.
- Retain existing timeout markers; do not use skips as the fix.
- Provide bounded Make-based evidence under conditions comparable to full-suite load.

### Out of scope

- Changing environment encryption product behavior beyond what is required so the
  scenario can complete honestly and cleanly (the contracted product check stays).
- Removing, skipping, or rewriting away the named test (or its timeout markers) as a
  substitute for fixing the flake.
- Broad redesign of the entire environment storage subsystem or all e2e harnesses
  unrelated to this cleanup failure class.
- Unrelated failures elsewhere in the full suite that are not caused by this defect.
- Mandating a particular teardown or wait API from the ticket’s candidate notes;
  solution design belongs in later steps once evidence pins the defect.

### Constraints and assumptions

- Work is Jira-driven (PYPOST-1311); estimate 2 story points; labels include
  `failing-test`, `flaky`, and `tech-debt`.
- Found during PYPOST-1297; sprint context: Worker Shutdown & UI Stability.
- All build/test/lint operations go through `make` targets only.
- Failure evidence may be intermittent; acceptance requires *bounded* reproducibility
  and validation under load-comparable Make runs, not an infinite flake campaign.
- Suspected unfinished background storage work during temp-dir cleanup is a working
  hypothesis from the ticket, not a design mandate; Step 2+ may refine the defect once
  evidence is in hand.
- Documentation and artifact lines stay within the 100-character limit.

### Main entities (business domain)

- **Encrypted environment data**: persisted environment records that require an
  encryption key to be readable; must not appear when the key is missing.
- **Missing encryption key scenario**: the user/presenter path where encryption is
  enabled but no usable key is available for already encrypted data.
- **Environment persistence e2e coverage**: automated proof that load behavior matches
  the missing-key rule for encrypted data.
- **Temporary workspace**: the isolated filesystem area used by the scenario; must be
  releasable when the scenario ends without cleanup errors.
- **Quality gate / Make run**: the maintainer-facing proof path that must end with an
  honest pass/fail, not a temp-dir cleanup failure after the scenario.

### Non-functional requirements

- **Reliability**: focused and full-suite / parallel Make validations for the in-scope
  scenario complete without the “Directory not empty” temporary-workspace cleanup
  failure attributable to this defect.
- **Integrity of coverage**: no loss of the missing-key product assertion or timeout
  enforcement for the affected test(s).
- **Operability**: evidence and validation remain runnable through existing Make
  workflows with bounded effort (no ad-hoc, unbounded flake hunting as the only proof).
- **Honesty of signal**: a scenario that satisfies its product checks must not be
  reported as failed solely because temporary workspace cleanup races leftover activity
  from that scenario.

## Q&A

This is an autonomous run (sprint-task-runner); clarifying questions were resolved from
the Jira issue and discovery context (PYPOST-1297) rather than left open for interactive
approval.

- **Q: Why is this a business/requirements issue if the symptom is a temp-dir cleanup
  error in tests?**
  **A:** The business asset at risk is trustworthy delivery proof for a
  security-sensitive rule (no environments shown when the encryption key is missing).
  Cleanup noise under full-suite load makes Make results unusable for deciding whether
  that coverage still holds.

- **Q: Why not skip or quarantine the flaky test until later?**
  **A:** Acceptance explicitly requires retaining the product assertion and validating
  without skips. Quarantine would hide coverage for encrypted-environment key handling.

- **Q: Must the failure reproduce on every focused run before a fix is allowed?**
  **A:** No. Acceptance asks for *bounded* evidence and then a fix validated by focused
  and full-suite / parallel Make runs—not a guarantee of 100% historical reproduction in
  isolation (isolation often already passed).

- **Q: Does the ticket’s “wait then teardown before leaving the temp dir” note dictate
  the solution?**
  **A:** No. That note is investigative / candidate context from discovery. Requirements
  only mandate eliminating the cleanup failure class while preserving the product check;
  design choices belong in later steps.

- **Q: Is product environment encryption behavior in scope to change freely?**
  **A:** Only if a genuine product defect must be fixed for honest verification. The
  contracted missing-key assertion must remain; wholesale encryption redesign is out of
  scope.

- **Q: Who accepts the requirements?**
  **A:** The autonomous sprint orchestrator after independent review PASS; Step 1 stays
  `[/]` until that gate marks `[x]`.

- **Q: Links**
  - Issue: [PYPOST-1311](https://pypost.atlassian.net/browse/PYPOST-1311)
  - Discovered during: [PYPOST-1297](https://pypost.atlassian.net/browse/PYPOST-1297)

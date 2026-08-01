# PYPOST-984: Observability Implementation

## Applicability Assessment

This task hardens a CI/build-time gate (`check-lock` job in `.github/workflows/test.yml` and
the `check-lock` target in `Makefile`), not a running application service. There is no request
handler, background worker, daemon, or long-lived process in scope — `make check-lock` is a
short-lived, one-shot build tool invocation that runs once per CI job (or local invocation) and
exits.

Conclusion: **structured application logging and metrics (Prometheus/Grafana/log
aggregation/APM) do not apply to this task.** The project's runtime observability stack (e.g.
OpenTelemetry, structured `logging` module usage in `src/pypost/`) is designed for the
long-running `pypost` server/agent processes, not for `make`-driven CI gates. Introducing a
metrics/log-aggregation integration for a build script that runs for a few seconds per CI job
would add operational surface (a metrics endpoint, exporter config, dashboards) with no
corresponding consumer — nothing scrapes or ships logs from a GitHub Actions job step other than
the Actions log itself.

What **does** apply, and was already added in Step 4, is operator-facing diagnostics: the
`check-lock` target's `stderr` messages are the observability signal for this component, since
"the log" for a CI job *is* its captured stdout/stderr in the Actions run view. These messages
are the only way a maintainer (the "operator" here) can distinguish *why* the gate went red
without needing GitHub-admin log-download access — which was the exact gap identified in Step 1
(`10-requirements.md` Q&A: "the exact `make check-lock` failure output ... is not retrievable
without repo-admin GitHub access").

## Logging Implementation

### Added Logs (stderr messages, `Makefile` `check-lock` target)

Treated as the CI-gate equivalent of application logs — each is a distinct, greppable message an
operator reads directly in the GitHub Actions step log (or local terminal) to diagnose a red
`check-lock` run without deeper investigation:

- **ERR**: `Makefile:54-55` (`check-lock` target) — `"check-lock: uv pip compile failed after
  $max_attempts attempts (network or tool issue)"`, emitted to `stderr` and paired with
  `exit 2`, once retries are exhausted. Distinguishes a lock-*tool* failure (network/transient or
  `uv` itself erroring) from a genuine content mismatch.
- **WARNING**: `Makefile:59-60` — `"check-lock: uv pip compile attempt $attempt/$max_attempts
  failed, retrying in $delay s..."`, emitted to `stderr` on each transient failure before a retry;
  gives visibility into flakiness even on runs that ultimately succeed (e.g. a maintainer scanning
  a green run's log can still see "attempt 1/3 failed, retrying" and know PyPI/network was briefly
  unstable).
- **ERR**: `Makefile:68-69` — `"check-lock: requirements.txt is stale relative to
  requirements.in (run 'make lock' and commit)"`, emitted to `stderr` and paired with `exit 1`,
  on a genuine `diff` mismatch between the compiled and committed lock bodies. Distinct wording
  and exit code (`1` vs. `2`) from the compile-failure message above, so log scanning or exit-code
  branching in future tooling can tell the two failure classes apart without re-parsing free text.
- **INFO** (pre-existing, unchanged by this task): `.github/workflows/test.yml:322-327` "Write job
  summary" step — on `always()`, appends a one-line confirmation
  ("Verified `requirements.txt` matches `requirements.in` via `make check-lock`.") to the GitHub
  Actions job summary. This only fires a positive-confirmation message; it does not vary by
  failure mode, so it is not a substitute for the `stderr` messages above but is noted here as
  existing "logging surface" for completeness.

### Log Structure

- Structured logs: **no** — these are plain `stderr` text lines (`make`/shell recipe output),
  consistent with every other `Makefile` target in this repository (e.g. `check-lock-dev`,
  `check-license-inventory`) and with GitHub Actions' own step-log convention. Introducing
  structured (JSON) logging for a `make` recipe would be inconsistent with the rest of the
  Makefile and add parsing complexity with no consumer to benefit from it.
- Includes context: **yes** — each message names the failing component (`check-lock`), the
  concrete cause class ("uv pip compile failed" vs. "requirements.txt is stale"), and the
  actionable next step (retry count for transient failures; `run 'make lock' and commit'` for
  genuine drift).
- Log levels: no formal level tagging (shell scripts have no logging framework); severities
  above are the closest syslog-equivalent classification for documentation purposes. All three
  new messages are written to `stderr` specifically so they are visually distinguishable from
  `stdout` in local terminal use and are captured by GitHub Actions' log color-coding for step
  output.

## Metrics Implementation

Not applicable — see "Applicability Assessment" above. There is no throughput, request-rate, or
resource-usage dimension to a one-shot `make check-lock` invocation that would be meaningful as a
Prometheus/Grafana metric. The two metrics one might otherwise consider:

- **Retry count** (attempts before success/exhaustion) — already surfaced textually via the
  `WARNING`-equivalent per-attempt message above rather than as an emitted metric, since there is
  no metrics backend wired into GitHub Actions jobs for this repository and a single ephemeral CI
  job has no time series to aggregate against.
- **Pass/fail rate over time** — already available for free via GitHub Actions' own per-workflow
  run history/status API without any code change in this repo; duplicating it as an
  application-level metric would be redundant.

## Monitoring Integration

- [ ] Prometheus metrics — N/A, see above
- [ ] Grafana dashboards — N/A, see above
- [ ] Alerting rules — N/A; GitHub Actions' built-in branch-protection/notification on a failing
  required check already serves this role for `dev`
- [ ] Log aggregation (ELK, Loki, etc.) — N/A; GitHub Actions retains step logs natively

## Validation Results

- [x] Log messages (stderr) are correctly formatted and distinct per failure mode — verified by
  `tests/test_makefile_check_lock_retry.py` (`TestCheckLockReportsExhaustedCompileFailure`,
  `TestCheckLockStillCatchesGenuineDrift`), which assert on the exact distinguishing substrings
  (`"compile failed"` + `"attempt"` vs. `"stale"`) and cross-check that each failure mode's output
  does **not** contain the other mode's marker text.
- [x] Retry-path logging works in the relevant failure/recovery scenarios — verified by
  `TestCheckLockRetriesTransientFailure` (recovers silently-but-loggedly after 2 transient
  failures) and the exhausted-retry case above.
- N/A: metrics are collected correctly — no metrics added (see Metrics Implementation)
- [x] Large data structures are not logged — messages contain only fixed strings, attempt
  counters, and a delay value; never the compiled `requirements.txt` contents.
- N/A: metrics are available for monitoring — no metrics added (see Metrics Implementation)

## Notes

This is a Makefile/CI-gate hardening task, not an application feature, so the STEP 6 template's
"Logging Implementation" / "Metrics Implementation" sections are answered with an explicit N/A
+ justification for the metrics/monitoring-integration portions (per the task instruction), while
documenting the operator-facing `stderr` diagnostics added in Step 4 as the CI-appropriate
observability equivalent of application logs. No new code was written for this step; it documents
logging already introduced in Step 4 (`Makefile:46-73`) and confirmed by the Step 3/4 tests in
`tests/test_makefile_check_lock_retry.py`.

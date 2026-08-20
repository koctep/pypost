# PYPOST-1067: Observability Implementation

## Decision

Production observability changes are **N/A** for this task. No logging or metrics code was added.

The changed operation derives and compiles a regular expression once during module import. It is
deterministic, uses only the static `MYPY_PATHS` tuple, performs no network or persistent I/O, and
does not create a separately actionable runtime event. The script is a one-shot CI quality gate,
not a long-running service. Adding an import log, timing metric, or regex dump would add noise and
would change the existing CLI/reporting interface that the requirements explicitly preserve.

## Existing Observable Outcomes

The gate already exposes operational state at the process boundary:

| Outcome | Channel | Observable information | Exit status |
| --- | --- | --- | --- |
| Baseline matches | Standard output | Known error count and configured paths | `0` |
| Baseline updated | Standard output | Baseline filename and recorded error count | `0` |
| Baseline missing | Standard error | Recovery command | `1` |
| Baseline malformed | Standard error | Format/version problem and recovery command | `1` |
| New errors | Standard error | Path, message, code, line numbers, and multiplicity | `1` |
| Resolved errors | Standard error | Path, message, code, and multiplicity | `1` |
| Any baseline drift | Standard error | Baseline and current total counts | `1` |

The configured scope is also observable in `mypy-baseline.json` through its `scope` field. The
successful-run message lists `MYPY_PATHS`, so a maintainer can confirm the effective checked scope
without exposing the internal regular expression.

## Logging Implementation

### Added Logs

N/A. No new EMERG, ALERT, CRIT, ERR, WARNING, NOTICE, INFO, or DEBUG messages were added.

The existing CLI deliberately uses standard output and standard error rather than application
logging. Preserving those channels avoids timestamp, logger-name, or handler configuration noise
in CI output and keeps current consumers compatible.

### Error and Report Behavior

- Parsed in-scope diagnostics continue through the existing baseline comparison and reports.
- Out-of-scope and prefix-lookalike diagnostics remain excluded rather than generating noise.
- The script does not dump the full mypy subprocess output; reports contain only parsed,
  actionable diagnostics and aggregate counts.
- The regex derivation introduces no new exception handling or failure mode requiring a log.

## Metrics Implementation

N/A. No performance, throughput, business, or system-health metrics were added.

Regex construction occurs once and is negligible relative to the mypy subprocess. A duration or
counter would require a monitoring dependency and lifecycle for a local CI script without an
actionable service-level objective. Process duration and pass/fail status remain available from
the invoking CI system.

## Monitoring Integration

- [ ] Prometheus metrics — N/A for a one-shot quality gate.
- [ ] Grafana dashboards — N/A.
- [ ] Alerting rules — N/A; CI failure status is the existing alert mechanism.
- [ ] Log aggregation — N/A; stdout and stderr are retained by CI.

## Privacy and Sensitive Data

- No new data is emitted.
- `MYPY_PATHS` contains repository-relative source directories, not credentials or user data.
- The derived regex and raw mypy subprocess output are not logged.
- Existing diagnostic reports may contain source paths and type-checker messages because those
  details are required to repair a failed quality gate; this behavior is unchanged.
- No environment values, file contents, baseline payloads, tokens, or secrets are added to output.

## Validation Results

- The configured-path extension test directly verifies that `_parse_errors()` recognizes a
  diagnostic under a newly configured path and rejects a prefix lookalike.
- The escaping/overlap test directly verifies `_parse_errors()` recognition and boundaries for
  overlapping configured paths containing a regular-expression metacharacter.
- The full mypy-baseline test module covers repository baseline artifact presence and scope,
  parser extraction, baseline update and success flows, resolved-error CLI output and exit
  status, new/fixed diff and report helpers, multiset behavior, legacy-format rejection, and
  baseline write/load round trips.
- No production or test code changed during Step 6.

## Notes

The current CLI output is the appropriate observability surface. If the gate later becomes a
long-running service, metrics and structured logging should be reconsidered with explicit
cardinality, retention, and sensitive-data requirements.

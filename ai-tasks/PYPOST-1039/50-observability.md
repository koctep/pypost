# PYPOST-1039: Observability Implementation

## Logging Implementation

### Added Logs

No application log event was added for the protected live Jira MCP smoke.  This
is intentional: all smoke inputs and response data are sensitive in context,
including the Jira base URL, credentials, project key, account identity, issue
keys, board metadata, and response bodies.  Emitting even a success event with
those values would expand the protected-job secret surface without providing a
useful operator signal.

The smoke instead has these safe observability boundaries:

- **INFO / NOTICE:** the protected GitHub Actions job writes exactly one
  value-free summary: `Jira MCP live smoke: passed`, `Jira MCP live smoke:
  intentionally skipped`, or `Jira MCP live smoke: failed`.  It derives the
  intentional-skip state only from a local JUnit record whose sole case has the
  fixed skip reason; it never copies test output into the job summary.
- **ERR:** a failed call is reduced to one fixed operation label (`tool setup`,
  `current user`, `issue search`, `issue retrieval`, `board listing`, or local
  MCP transport) before pytest reports it.  It does not include exception text,
  endpoint, credentials, request payload, or response body.
- **DEBUG:** logging is disabled for the entire local-MCP/live-Jira call window
  with `logging.disable(logging.CRITICAL)`.  This deliberately suppresses
  framework and HTTP debug output that could otherwise include protected values
  or response-derived content.  The previous global logging threshold is
  restored in `finally`.

The local current-user stub uses the same suppression and additionally disables
the standard-library HTTP handler log.  It validates only the fixed request
path; its synthetic credential and response values are never written to a log
assertion or test output.

### Log Structure

- Structured logs: no new application event; the existing test output uses
  fixed, value-free labels only.
- Includes context: yes, but only the allowlisted operation label on failure.
- Log levels: pytest failure plus suppressed runtime logging during protected
  operations.

## Metrics Implementation (if applicable)

No new metrics were added.  The smoke is a dispatch-only, low-frequency
release-health check rather than a production request path.  GitHub Actions
job status supplies the useful health signal (pass/fail) without recording
Jira-derived timing, throughput, status, or identity data.

### Performance Metrics

- **Response time:** intentionally not emitted; timing could become a side
  channel for the protected Jira target.
- **Throughput:** not applicable; the smoke makes exactly four fixed calls.
- **Error rate:** supplied by protected workflow job outcome, not a new metric.

### Business Metrics

No business metric is applicable.  The smoke does not create, update, or count
Jira business entities.

### System Health Metrics

- **Component status:** the protected `jira-mcp-live-smoke` job outcome plus
  its value-free passed / intentionally-skipped / failed summary is the only
  required status signal.
- **Resource usage:** not applicable to this short, opt-in test.

## Monitoring Integration

- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [x] Protected CI job status and value-free three-state job summary
- [x] Runtime log suppression while secrets or Jira-derived data are in memory

## Validation Results

- [x] Protected-call failures use fixed labels rather than raw exceptions.
- [x] The job summary distinguishes the one fixed intentional-skip condition
  from a passed or failed protected run without copying pytest output.
- [x] Logging is suppressed around both the local stub and live smoke call
  windows, and the previous setting is restored in `finally`.
- [x] All four live tools are separately locked to fixed read-only methods,
  paths, inputs, and bodies before registration.
- [x] No new logs or metrics include credentials, service URLs, project keys,
  account identifiers, issue/board data, request payloads, or response bodies.
- [x] The absent-opt-in path is a fixed intentional skip and does not read Jira
  configuration.

## Notes

No live Jira credentials were used during this step.  A real protected run is
authorized only through the dispatch-only workflow and remains outside normal
PR validation.  The suppression test is a safety boundary, not evidence that
the framework's sanitizer would redact every possible value; no such claim is
made here.

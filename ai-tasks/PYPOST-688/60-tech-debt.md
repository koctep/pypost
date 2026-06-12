# PYPOST-688: Technical Debt Analysis

**Task type:** Observability and logging audit (no application code changes).

**Source:** `30-audit-report.md` — P1/P2/P3 remediation recommendations.

Twelve remediation items for follow-up ticketing.

## Shortcuts Taken

- **Static analysis only:** No runtime log capture or metrics scrape under load.
- **PYPOST-685 cross-ref:** Sensitive-data findings cite E-003/M-004; full secrets matrix not
  re-run.
- **No code fixes in scope:** Findings document gaps; remediation deferred to follow-up work.

## Code Quality Issues

Observability issues observed in the audited codebase (not introduced by this task):

- **Resolved URLs in ERROR logs (P1):** `http_client.py` logs full rendered URLs.
- **print() bypass (P1):** `config_manager.py`, `style_manager.py` use stdout not logging.
- **Hardcoded log level (P2):** `main.py` basicConfig INFO only.
- **Alert endpoint in logs (P2):** `AlertManager.emit` WARNING includes full endpoint.
- **Monolithic metrics init (P2):** `_init_metrics` ~196 LOC.

## Missing Tooling

- No settings or env var for application log level
- No centralized logging convention doc (key=value event catalog)
- No automated check for `print()` in `pypost/` (flake8 print plugin or custom lint)

## Performance Concerns

N/A for this audit. Metrics cardinality and log volume under load not profiled.

## Follow-up Tasks

### P1 — Critical / credential exposure or guardrail bypass

#### R-P1-001 — Redact resolved URLs in http_client ERROR logs

- **Priority:** P1
- **Finding refs:** L-001, PYPOST-685 E-003
- **Description:** `HTTPClient.send_request` logs fully rendered URL on timeout, connection
  failure, and RequestException. Query parameters may contain API keys.
- **Remediation:** Log method + host + path (strip query) or apply URL redaction helper shared
  with history masking policy. Update `expected_log_allowlist.yaml` message prefixes if shapes
  change.
- **Jira:** [PYPOST-741](https://pypost.atlassian.net/browse/PYPOST-741)

#### R-P1-002 — Replace print() with logger in config_manager and style_manager

- **Priority:** P1
- **Finding refs:** L-010, O-003
- **Description:** Five `print()` calls emit config/style errors to stdout only — invisible to
  pytest log capture and CI guardrails.
- **Remediation:** Add module loggers; use `logger.error` with structured context
  (`config_load_failed path=%s error=%s`). Add caplog test for config load failure path.

### P2 — Meaningful observability gaps
- **Jira:** [PYPOST-742](https://pypost.atlassian.net/browse/PYPOST-742)

#### R-P2-001 — Add configurable application log level

- **Priority:** P2
- **Finding refs:** O-001
- **Description:** `logging.basicConfig(level=INFO)` is hardcoded; 108 DEBUG calls unused in
  production without code edits.
- **Remediation:** Add `AppSettings.log_level` or `PYPOST_LOG_LEVEL` env; document in dev
  docs. Default INFO; allow DEBUG for support sessions.
- **Jira:** [PYPOST-743](https://pypost.atlassian.net/browse/PYPOST-743)

#### R-P2-002 — Sanitize endpoint in AlertManager application logs

- **Priority:** P2
- **Finding refs:** L-004
- **Description:** `alert_emitted` WARNING logs full `endpoint=%r` including query tokens.
- **Remediation:** Log host + path or truncated endpoint; keep full URL in JSON file only if
  required for operators (document file sensitivity).
- **Jira:** [PYPOST-744](https://pypost.atlassian.net/browse/PYPOST-744)

#### R-P2-003 — Reduce webhook URL verbosity in alert debug/warning logs

- **Priority:** P2
- **Finding refs:** L-005
- **Description:** `alert_webhook_ok` and `alert_webhook_failed` log full webhook URL.
- **Remediation:** Log scheme + host + path prefix; omit auth query params if present.
- **Jira:** [PYPOST-745](https://pypost.atlassian.net/browse/PYPOST-745)

#### R-P2-004 — Split metrics_registry._init_metrics by domain

- **Priority:** P2
- **Finding refs:** O-004, PYPOST-687 complexity note
- **Description:** Single 196-LOC method registers all 31 Prometheus instruments.
- **Remediation:** Extract `_init_gui_metrics`, `_init_http_metrics`, `_init_mcp_metrics`,
  `_init_encryption_metrics` helpers; no behavior change.
- **Jira:** [PYPOST-746](https://pypost.atlassian.net/browse/PYPOST-746)

#### R-P2-005 — Document logging event naming convention

- **Priority:** P2
- **Finding refs:** O-002
- **Description:** Mix of key=value events and legacy human-readable strings (`Connection
  failed: GET url`).
- **Remediation:** Add section to `doc/dev/observability_audit.md` or new `logging.md` with
  event catalog and migration guidance for legacy modules.
- **Jira:** [PYPOST-747](https://pypost.atlassian.net/browse/PYPOST-747)

#### R-P2-006 — Sanitize MCP activity log detail field

- **Priority:** P2
- **Finding refs:** MCP activity gap in 30-audit-report
- **Description:** `McpActivityEntry.detail` may store execution error messages with upstream
  fragments; shown in UI dialog.
- **Remediation:** Truncate or classify detail text; avoid echoing full response bodies in
  activity viewer.

### P3 — Minor hygiene
- **Jira:** [PYPOST-748](https://pypost.atlassian.net/browse/PYPOST-748)

#### R-P3-001 — Link observability doc to testing.md log_cli section

- **Priority:** P3
- **Finding refs:** O-007
- **Description:** Local `log_cli=true` vs CI `log_cli=false` documented in testing.md but not
  cross-linked from observability summary.
- **Remediation:** Add reciprocal links between `observability_audit.md` and `testing.md`.
- **Jira:** [PYPOST-749](https://pypost.atlassian.net/browse/PYPOST-749)

#### R-P3-002 — Publish Prometheus metrics inventory in dev docs

- **Priority:** P3
- **Finding refs:** Metrics inventory table
- **Description:** 31 counters/histograms/gauge registered; no single operator-facing catalog
  beyond scrape endpoint.
- **Remediation:** Add metrics name/label table to observability doc or extend
  `metric_rename_migration.md`.
- **Jira:** [PYPOST-750](https://pypost.atlassian.net/browse/PYPOST-750)

#### R-P3-003 — Standardize http_client log messages to key=value format

- **Priority:** P3
- **Finding refs:** O-002 legacy format
- **Description:** After URL redaction (R-P1-001), migrate remaining messages to
  `http_request_timeout method=%s host=%s` style for allowlist consistency.
- **Remediation:** Update allowlist rules in same PR as redaction.
- **Jira:** [PYPOST-751](https://pypost.atlassian.net/browse/PYPOST-751)

#### R-P3-004 — Add flake8 or custom lint rule for print in pypost/

- **Priority:** P3
- **Finding refs:** L-010 prevention
- **Description:** No merge gate prevents new print() in application code.
- **Remediation:** Enable flake8-print (T201) for `pypost/` or extend audit script.
- **Jira:** [PYPOST-752](https://pypost.atlassian.net/browse/PYPOST-752)

## Blocker Review

**SAFE TO CLOSE** — audit deliverables complete; no application code changes required.
Observability stack is functional; URL redaction and print→logger fixes should be scheduled
first. Twelve remediation items documented above (orchestrator tickets separately).

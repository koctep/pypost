# PYPOST-687: Observability Implementation

**Task type:** Audit only — no application code changes.

## Logging Implementation

### Application error logging

PyPost uses **stdlib `logging`** with module-level loggers (`logging.getLogger(__name__)`). No
structured logging framework (JSON logs, OpenTelemetry log export) in application code.

**High-activity error modules (audit grep):**

| Module | `logger.error`+ calls | Role |
| --- | ---: | --- |
| `encryption_migration.py` | 12 | Migration failures per environment |
| `storage.py` | 9 | Persistence I/O errors |
| `request_manager.py` | 9 | Collection file operations |
| `request_service.py` | 6 | Execution failures |
| `mcp_client_service.py` | 5 | MCP client errors |
| `collection_tree_actions.py` | 7 | UI action failures |

**Assessment (PASS):** Critical paths (storage, execution, encryption) log failures. Volume is
proportionate to I/O surface.

### User-visible error observability

| Layer | Mechanism |
| --- | --- |
| UI | `collection_item_dialogs.py` — QMessageBox wrappers |
| Presenters | Import dialog helpers; log + show pattern |
| Core | Log-only; exceptions bubble or convert to result types |

**Gap (P3):** No unified correlation ID between log line and user dialog — desktop app acceptable.

## Metrics Implementation

Application metrics (`MetricsManager`, Prometheus counters) track **runtime behavior** (requests,
MCP tools, masking) — not code-quality signals.

Maintainability guardrails use **tests and scripts**, not metrics:

| Guardrail | Mechanism |
| --- | --- |
| SOLID caps | `scripts/audit_baseline_metrics.py --check` + `test_solid_audit_baseline.py` |
| Lint | `make lint` (local; not CI-gated) |
| Test ERROR logs | `verify_test_log_guardrails.py` (CI) |

## Monitoring Integration

N/A — no new production monitoring. Audit documents **error-path observability** for
maintainers:

| ID | Severity | Finding |
| --- | --- | --- |
| O-001 | PASS | Module loggers used consistently in core I/O |
| O-002 | PASS | UI errors centralized in `collection_item_dialogs.py` |
| O-003 | P2 | 29 `except Exception` handlers — not all use `logger.exception` |
| O-004 | P2 | Lint failures invisible to CI — no automated hygiene signal |
| O-005 | P3 | Cap violations surface via pytest, not runtime metrics |

## Validation Results

- [x] Error logging patterns documented
- [x] No production instrumentation changes required
- [x] Gaps noted for Step 6 follow-ups (R-P2-004, R-P2-007, R-P3-003)

## Follow-up

See `60-tech-debt.md` — observability-related items folded into error-handling and CI lint tickets.

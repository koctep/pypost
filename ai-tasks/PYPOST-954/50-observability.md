# PYPOST-954: Observability

## Scope

Test-only hardening of packaging doc-token contract tests. No runtime logging,
metrics, or production paths changed.

## Events / signals

| Signal | Where | Notes |
| --- | --- | --- |
| Contract test failure | pytest | Clear `doc_label: missing 'token'` messages via shared helper |
| Import contract failure | `test_packaging_doc_lock_helper` | Prevents reintroducing local `_read` copies |

## N/A

- No new DEBUG/INFO log lines
- No Prometheus or MCP observability changes
- No GUI or live MCP sessions required for locks

## Verification

Disk-read unit tests only; module `pytestmark = pytest.mark.timeout(10)`.

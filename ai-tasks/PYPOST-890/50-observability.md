# PYPOST-890: Observability Implementation

## Verdict

**N/A — no new production observability.** This story adds an agent UI e2e
presentation matrix (method × body) plus optional harness identity for
request detail tabs. No production Send / chunk-flush / response-display
paths were changed; product defects stay out of scope for
[PYPOST-891](https://pypost.atlassian.net/browse/PYPOST-891).

## Logging Implementation

### Added Logs

None added in this step.

| Level | Location | Notes |
| --- | --- | --- |
| EMERG / ALERT / CRIT | — | N/A |
| ERR / WARNING / NOTICE | — | N/A |
| INFO / DEBUG | — | N/A for this story |

### Why no new logs

| Change | Observability impact |
| --- | --- |
| `REQUEST_DETAIL_TABS` + `set_widget_id` on `detail_tabs` | Identity only; no operational branch |
| `tests/test_agent_e2e_presentation_matrix.py` | Asserts once-only body/status; pytest failure is the signal |
| `ai-tasks/PYPOST-890/findings.md` | Triage artifact for PYPOST-891; not runtime logging |

Logging widget-id assignment or per-cell body fill would add noise without
diagnosing presentation cardinality. Product lifecycle logs already bookend
Send finish (see PYPOST-887): `request_finished`, `request_error`, etc. Do
**not** log request/response body contents.

### Existing harness logging (reused, unchanged)

`stub_agent_e2e_http` already emits:

- **INFO** `agent_e2e_http_stub_installed name=<catalog>` — matrix cells
  pass `name=presentation_matrix_{method}_{shape}`

Sibling agent e2e DEBUG/INFO (session lifecycle, actions, wait) continue to
fire when the suite runs; see [logging.md](../../doc/dev/logging.md) and
agent e2e capability docs.

### Log Structure

- Structured logs: yes (existing `key=value` style in fixtures / presenters)
- Includes context: N/A — no new statements in this story
- Log levels: none added

## Metrics Implementation (if applicable)

### Performance Metrics

None. Architecture expected no new production metrics for a test-only matrix.

### Business Metrics

None. Once-only presentation is enforced by e2e asserts, not counters.

### System Health Metrics

None.

## Monitoring Integration

- [ ] Prometheus metrics — N/A (desktop / agent e2e matrix)
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation — N/A

CI / local gate remains `make test-agent-e2e` (smoke slice) plus optional
full matrix with slow params; pytest assert + `findings.md` for triage.

## Validation Results

- [x] No new production log statements introduced
- [x] No large / sensitive payloads logged
- [x] Existing stub INFO catalog `name=` covers matrix canned results
- [ ] Metrics collected — N/A (none added)
- [x] Failure diagnostics: pytest assert message (count + panel excerpt)
  and wait timeout diagnostics (`cell`, `response_excerpt`)

## Notes

- Product discard / double-body race observability stays under PYPOST-887.
- Discoverability of the matrix in `doc/dev/` is Step 8 (FR7), not logging.
- Observability ready for production: **N/A** (no production path change
  requiring new monitoring).

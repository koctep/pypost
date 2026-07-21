# Agent E2E Double Response-Body Lock (PYPOST-889)

## Overview

One agent UI e2e scenario locks the
[PYPOST-887](https://pypost.atlassian.net/browse/PYPOST-887) regression: after
Send, the response panel must show the stub body **exactly once** (not
duplicated by a late chunk flush after `display_response`).

Product fix ownership stays with PYPOST-887
([Response Streaming Display](response-streaming-display.md)). This page
documents the **agent-driven** Send → panel lock only.

Golden e2e asserts status + body **presence**. This lock asserts **cardinality**
(`joined.count(token) == 1`) for the reported PUT + malformed body case.

## Architecture

| Piece | Role |
| --- | --- |
| `tests/test_agent_e2e_double_response_body.py` | Scenario + exactly-once assert |
| `CANNED_DOUBLE_BODY_LOCK_OK` | Plain-text stub body (`pypost-887-lock-body-once`) |
| `canned_send_with_one_chunk` | Side effect that emits one chunk (arms flush timer) |
| `REQUEST_BODY_EDIT` | Fill reported request body via identity |
| `RESPONSE_PANEL` snapshot walk | Count stub token under the panel |

Harness: blank `agent_e2e_session`, `stub_agent_e2e_http`, wait/snapshot — same
stack as [Agent Golden E2E](agent_golden_e2e.md). HTTP catalog:
[agent_e2e_http.md](agent_e2e_http.md).

## API / Usage

### How to run

```bash
make test-agent-e2e
make test-agent-e2e PYTEST_ARGS="tests/test_agent_e2e_double_response_body.py -v"
```

### Scenario (summary)

1. Fill URL + select PUT + fill `{ { "data": { } } }` via `REQUEST_BODY_EDIT`.
2. Stub Send with `canned_send_with_one_chunk(CANNED_DOUBLE_BODY_LOCK_OK)`.
3. Wait until status + lock body token appear under `RESPONSE_PANEL`.
4. Assert the lock body token appears **exactly once** in joined panel values.

Default HEAD (discard present) is **green**. To prove red-on-bug locally,
temporarily no-op `_discard_chunk_buffer` in `_on_request_finished`, run the
lock (expect count 2), then restore discard — do not commit the no-op.

## Configuration

| Constant | Value |
| --- | --- |
| URL | `https://example.test/pypost-887-double-body` |
| Method / request body | PUT / `{ { "data": { } } }` |
| Stub body | `pypost-887-lock-body-once` (`text/plain`) |
| Module timeout / Send settle | 60 s / 15 s |

No extra env vars. Prefer `make test-agent-e2e` for offscreen Qt.

## Troubleshooting

| Failure | What to do |
| --- | --- |
| `count != 1` (double body) | Check `_discard_chunk_buffer` before `display_response`; |
| | see [response-streaming-display.md](response-streaming-display.md) |
| Wait timeout | Confirm stub uses `canned_send_with_one_chunk` (plain |
| | `return_value` never arms the flush timer) |
| Missing body control | `REQUEST_BODY_EDIT` in [ui_identity.md](ui_identity.md) |

## Related

- [Agent UI E2E](agent_e2e.md)
- [Agent Golden E2E](agent_golden_e2e.md)
- [Agent E2E HTTP Fixture Layer](agent_e2e_http.md)
- [Agent E2E Presentation Matrix](agent_e2e_presentation_matrix.md)
- [Response Streaming Display (PYPOST-887)](response-streaming-display.md)
- [UI Widget Identity](ui_identity.md)

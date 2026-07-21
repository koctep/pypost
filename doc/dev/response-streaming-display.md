# Response Streaming Display (PYPOST-887)

## Overview

While an HTTP response streams, `TabsPresenter` shows body text incrementally via
a debounced chunk buffer. When the worker finishes, the UI replaces that text
with the full `ResponseData` body through `display_response`. Pending flush state
must be discarded first so a late timer cannot append after the final set.

## Architecture

```text
RequestWorker.chunk_received(chunk)
  → TabsPresenter._on_chunk_received
      buffer chunks; arm single-shot QTimer (~33 ms)
  → _flush_chunk_buffer
      ResponseView.append_body(joined chunks)

RequestWorker.finished(response) / error / new Send
  → _discard_chunk_buffer(tab)   # stop timer, drop buffer
  → (finish only) ResponseView.display_response(response)  # setText
```

| Piece | Role |
| --- | --- |
| `_chunk_buffers` / `_chunk_flush_timers` | Per-tab (`id(tab)`) state on `TabsPresenter` |
| `_chunk_flush_ms` | Debounce interval (default **33**) |
| `_discard_chunk_buffer` | `stop` + `deleteLater` on timer; pop buffer |
| `ResponseView.append_body` | Streaming insert |
| `ResponseView.display_response` | Final replace (`setText` of full body) |

Related pipeline (worker → service → HTTP): [Request Execution](request_execution.md).

## API / Usage

### `_discard_chunk_buffer(tab)`

Stops any pending flush timer for `tab` and drops buffered chunks. Call sites:

1. `_on_request_finished` — before `display_response`
2. `_on_request_error` — before UI reset (avoids append into cleared / empty body)
3. `_handle_send_request` — after `clear_body`, before starting a new worker

### `_on_chunk_received` / `_flush_chunk_buffer`

Normal streaming path. Do not flush after discard has cleared the tab’s entries;
a discarded timer must not fire `append_body`.

## Configuration

No settings or env vars. Flush interval is the presenter field `_chunk_flush_ms`
(33 ms), chosen to coalesce fast `iter_content` chunks without flooding the UI.

## Troubleshooting

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| Response body appears **twice** | Late `_flush_chunk_buffer` after `display_response` | `_discard_chunk_buffer` called before `display_response`; timer `deleteLater` |
| Body appends after Stop / error clear | Flush after error without discard | `_on_request_error` discard call |
| Stale chunks on re-Send | Buffer not cleared with `clear_body` | `_handle_send_request` discard |

Regression: `tests/test_tabs_presenter_response_display.py` (presenter unit).
Agent UI e2e lock (Send → panel, exactly once):
[agent_e2e_double_response_body.md](agent_e2e_double_response_body.md)
(`tests/test_agent_e2e_double_response_body.py`). Method × body presentation
matrix: [agent_e2e_presentation_matrix.md](agent_e2e_presentation_matrix.md)
(`tests/test_agent_e2e_presentation_matrix.py`).

```bash
make test PYTEST_ARGS="tests/test_tabs_presenter_response_display.py -v"
make test-agent-e2e \
  PYTEST_ARGS="tests/test_agent_e2e_double_response_body.py -v"
make test-agent-e2e \
  PYTEST_ARGS='tests/test_agent_e2e_presentation_matrix.py -m "agent_e2e and not slow" -v'
```

Observability: discard is silent by design; use existing `request_finished` /
`request_error` / `request_send_initiated` logs (see
`ai-tasks/PYPOST-887/50-observability.md`). Never log chunk body text.

## Key files

| File | Role |
| --- | --- |
| `pypost/ui/presenters/tabs_presenter.py` | Buffer/timer maps; send-path discard |
| `pypost/ui/presenters/tabs_presenter_worker.py` | Chunk, flush, discard, finish/error |
| `pypost/ui/widgets/response_view.py` | `append_body` / `display_response` |
| `tests/test_tabs_presenter_response_display.py` | Double-body race coverage |

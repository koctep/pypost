# PYPOST-1425: Observability

## Logging Added / Updated

### CollectionFetchWorker (`pypost.ui.workers.collection_fetch_worker`)

| Event | Level | Parameters | When |
| ----- | ----- | ---------- | ---- |
| `collection_variable_fetch_worker_cancelled` | DEBUG | `generation_id`, `connection_id` | `cancel()` (unchanged; now also fires CTS abort) |
| `collection_variable_fetch_worker_transport_aborted` | DEBUG | `generation_id`, `error` | `OperationCancelledError` after transport abort |
| Existing started / completed / failed / interrupted events | DEBUG/WARNING | unchanged | Unchanged |

### ManifestDiscoveryWorker (`pypost.ui.workers.manifest_discovery_worker`)

| Event | Level | Parameters | When |
| ----- | ----- | ---------- | ---- |
| `collection_variable_manifest_discovery_worker_cancelled` | DEBUG | `generation_id` | `cancel()` (unchanged; now also fires CTS abort) |
| `collection_variable_manifest_discovery_worker_transport_aborted` | DEBUG | `generation_id`, `error` | `OperationCancelledError` after transport abort |
| Existing started / completed / failed / interrupted events | DEBUG/WARNING | unchanged | Unchanged |

### CancellationTokenSource (`pypost.core.cancellation`)

| Event | Level | Parameters | When |
| ----- | ----- | ---------- | ---- |
| `Cancellation requested for token source: reason=%s callbacks_count=%d` | DEBUG | reason, callback count | Existing PYPOST-1437 cancel path; now exercised by UI workers |

## Metrics

No new Prometheus/OTel metrics in this task. Abort latency is covered by automated
tests asserting prompt worker join after cancel.

## Validation

- Quiet cancel path does not emit `fetch_failed` / `discovery_failed` (avoids false
  error banners).
- Transport abort is distinguishable in DEBUG logs via `*_transport_aborted`.

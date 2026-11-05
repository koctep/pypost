# PYPOST-1426: Observability Report

## Analysis

This task adds fault-injection **tests** for remote collection import. Production
logging for fetch failures and transport abort already exists from PYPOST-1415 /
PYPOST-1425. No new production log events or metrics were required.

## Existing Events Exercised by the Suite

| Event | Level | Logger | When fault suite hits it |
| ----- | ----- | ------ | ------------------------ |
| `collection_json_parse_failed` | WARNING | `pypost.core.collection_serializer` | Truncated JSON helper / side effect |
| `collection_deserialization_failed` | WARNING | `pypost.core.collection_serializer` | Malformed variable name/type JSON |
| `collection_variable_fetch_worker_failed` | WARNING | `pypost.ui.workers.collection_fetch_worker` | Reset, broken pipe, serialization faults |
| `collection_variable_remote_fetch_failed` | ERROR | `pypost.ui.dialogs.import_collection_variables_dialog` | Dialog inline-error path |
| `collection_variable_fetch_worker_transport_aborted` | DEBUG | fetch worker | Cancel during mid-stream block |
| `collection_variable_remote_fetch_cancelled` | INFO | dialog | Cancel loading mid-stream |

## Logging Added

None — reused existing structured event prefixes.

## Metrics Added

None — test-only deliverable; no new counters/histograms.

## Caplog Contract

Dialog/worker fault tests use strong behavioral assertions (inline banner, empty
table, retry, abort timing) per do-testing **C3**. Serializer WARNING paths are
incidental to real `deserialize_collection_from_json` calls in helpers.

## Validation

- Fault scenarios produce the expected ERROR/WARNING worker and dialog events in
  live pytest logs during suite runs.
- Cancel-during-stream does **not** emit `collection_variable_remote_fetch_failed`
  for the cancelled generation.

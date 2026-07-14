# PYPOST-698: Allow RequestService injection in RequestWorker

## Goals

Enable `RequestWorker` to accept an injected `ExecuteRequestProtocol` or factory for narrower
integration tests (S-HTTP-003).

## Definition of Done

- [x] Optional `service` and `service_factory` constructor parameters
- [x] Default behavior unchanged (constructs `RequestService`)
- [x] Tests in `test_execute_request_protocol.py`

## Verdict

**SAFE TO CLOSE**

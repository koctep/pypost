# PYPOST-194: Close debt — named default request timeout

## Goals

Close follow-up debt from [PYPOST-26](https://pypost.atlassian.net/browse/PYPOST-26): replace
magic `30.0` timeout literal with a named module constant.

## Definition of Done

- [x] `DEFAULT_REQUEST_TIMEOUT = 30.0` exported from `pypost.core.http_client`
- [x] `HTTPClient.send_request` passes constant to `requests`
- [x] Test asserts timeout kwarg matches constant

## Task Description

Sprint 492 debt closure. Per-request timeout UI remains deferred to [PYPOST-200](https://pypost.atlassian.net/browse/PYPOST-200).

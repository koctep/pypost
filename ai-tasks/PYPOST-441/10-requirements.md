# PYPOST-441: AlertManager close idempotence test

Sprint 489 follow-up: close technical debt item filed from [PYPOST-420](https://pypost.atlassian.net/browse/PYPOST-420).

**Goal:** Verify double `close()` does not raise and keeps log output stable.

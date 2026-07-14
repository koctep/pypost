# PYPOST-749 — Developer Documentation

> Parent: [PYPOST-749](https://pypost.atlassian.net/browse/PYPOST-749)

## What Changed

Added reciprocal cross-links for pytest `log_cli` documentation between the observability audit
summary and the testing developer reference.

## Documentation Updated

| File | Change |
| --- | --- |
| `doc/dev/testing.md` | Link to observability audit Test and CI Logging; References entry |
| `doc/dev/observability_audit.md` | Anchor link to testing log_cli section in intro |

## For Maintainers

When changing `log_cli` defaults, CI overrides, or ERROR allowlist baseline, update both
documents and keep the cross-links in sync.

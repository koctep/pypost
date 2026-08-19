# PYPOST-996: Observability

## Diagnostic Signals

- Target stderr explicitly logs each retry attempt (`$(TARGET): uv pip compile attempt N/3 failed, retrying in Xs...`).
- Stale lock vs compile failures produce distinct, unambiguous error messages.

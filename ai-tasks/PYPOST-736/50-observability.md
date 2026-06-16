# PYPOST-736: Observability

GitHub Actions job logs now include a "Run lint" step output for every push/PR,
visible in the Actions UI alongside test results. A failing lint step now fails
the whole `test` job (`fail-fast: false` only applies across matrix entries, not
within a job's steps), giving immediate visibility into lint regressions.

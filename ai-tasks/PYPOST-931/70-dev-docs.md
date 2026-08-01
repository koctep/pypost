# PYPOST-931: Dev Docs

## Updated developer documentation

| File | Change |
| --- | --- |
| `doc/dev/testing.md` | § Agent e2e CI double-run — refresh procedure, harness row |
| `doc/dev/agent_e2e.md` | CI note links `make refresh-ci-duration-evidence` |

## Maintainer workflow

1. `make refresh-ci-duration-evidence` — print markdown table from Actions API.
2. Paste into `doc/dev/testing.md` § **CI duration evidence**; update `n=`
   and fetch date in prose.
3. `make check-ci-duration-evidence` — verify procedure anchors remain.
4. `make test PYTEST_ARGS='tests/test_refresh_ci_duration_evidence.py -v'`.

Optional: set `GITHUB_TOKEN` or `GH_TOKEN` for higher GitHub API rate limits.

## Locks

- `tests/test_refresh_ci_duration_evidence.py` — script, Makefile, doc wiring.

## Related

- Evidence publisher: PYPOST-907
- Discoverability: PYPOST-908 (can close — automation was deferred to 931)
- ENABLE threshold: PYPOST-930

# PYPOST-966: Observability

## Test Signals

| Test | Signal |
| --- | --- |
| `test_post_install_sanity_includes_pypost_version_read` | Fast guard — snippet list must include pypost check |
| `TestSlowInstallSmoke.test_install_succeeds_with_project_pyproject` | Slow — runs all snippets after network install |
| `_assert_post_install_sanity` failure message | Subprocess stderr/stdout surfaced on snippet failure |

## Failure Modes

| Failure | Likely cause |
| --- | --- |
| pydantic import fails | Dependency install regression (existing PYPOST-559 signal) |
| pypost.version assert fails | Seed missing `version.py`, broken install layout, empty `__version__` |
| Contract test fails | Snippet list regressed — pypost check removed |

## Operator Notes

- Snippet tuple is grep-friendly: `POST_INSTALL_SANITY_SNIPPETS`.
- Slow smoke remains network-heavy; fast contract catches policy drift without pip.

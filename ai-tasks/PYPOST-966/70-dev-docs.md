# PYPOST-966: Dev Docs

## Changes

| File | Update |
| --- | --- |
| `doc/dev/testing.md` | § Slow smoke — post-install sanity snippets (`POST_INSTALL_SANITY_SNIPPETS`) |
| `doc/dev/testing.md` | Makefile integration table — slow install smoke row mentions post-install checks |

## Maintainer Notes

When adding post-install checks, extend `POST_INSTALL_SANITY_SNIPPETS` in
`tests/test_makefile.py` and ensure snippets avoid Qt/UI imports unless the slow smoke job
explicitly provisions runtime for them.

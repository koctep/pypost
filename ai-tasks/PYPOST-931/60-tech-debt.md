# PYPOST-931: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Automation for refreshing agent-e2e overlap evidence is delivered: script,
Makefile targets, maintainer procedure in `doc/dev/testing.md`, and wiring lock.
No workflow selection change. No auto-commit of scraped numbers. Items below
are non-blocking. **Do not create Jira tickets in this step.**

## Shortcuts Taken

- **Did not auto-update committed evidence table** — maintainers paste after
  review (honest numbers policy).
- **Did not run live Actions fetch in CI** — unit tests use fixtures; live
  fetch is maintainer-only (`make refresh-ci-duration-evidence`).
- **Did not add gh CLI checklist** — Python script + documented make target
  satisfy “script or checklist”; gh REST equivalent noted in architecture.
- **Full `make check` not re-run** — targeted lock + `--check` only.

## Code Quality Issues

- None that block close. Optional: shared GitHub API helper if more Actions
  scrapers appear (today: single script).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Script + Makefile + doc procedure lock | Covered |
| Duration formatting / job extract | Covered (fixtures) |
| Live Actions integration in CI | Not covered — maintainer manual |
| Auto-sync testing.md from API | Not implemented — intentional |

Timeout markers: module `pytestmark` on lock tests. **No timeout-marker
blockers.**

## Performance Concerns

- Script scans up to 15 completed runs with one jobs API call each — acceptable
  for occasional maintainer use; not on CI hot path.

## Follow-Up Tasks

None required. Related tickets:

- [PYPOST-930](https://pypost.atlassian.net/browse/PYPOST-930) — ENABLE trim
  when threshold met (use refreshed evidence via this script).
- [PYPOST-908](https://pypost.atlassian.net/browse/PYPOST-908) — optional
  discoverability acceptance already met; safe to close independently.

## PYPOST-908 closure

**Can close:** Yes. PYPOST-908 DoD was discoverable timing notes in docs +
lock (no automation in scope). Published numbers remain in `testing.md`; this
ticket adds refresh tooling only and does not reopen 908 acceptance.

## Blocker Verdict

**SAFE TO CLOSE** — refresh automation + procedure + lock satisfy DoD; no
blockers relative to acceptance criteria.

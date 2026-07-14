# PYPOST-788: setup.md dependency list architecture

## Approach

Replace the stale five-item bullet list with:

1. A **summary table** of all 11 direct production packages from `requirements.in` (role only).
2. A **link** to [dependencies_audit.md](../../doc/dev/dependencies_audit.md) § Production
   Dependencies for pinned versions and audit notes.

No new files. No Makefile or lock changes.

## Content mapping

| setup.md section | Source of truth |
| --- | --- |
| Production package names | `requirements.in` (11 direct deps) |
| Pinned versions | `dependencies_audit.md` production table |
| MCP transitive stack | `dependencies_audit.md` § MCP Stack (linked, not duplicated) |

## Placement

Keep the section under **§ 2. Install Dependencies**, after the dev lock file subsection and
before **§ Project metadata (`pyproject.toml`)**, preserving the existing doc flow.

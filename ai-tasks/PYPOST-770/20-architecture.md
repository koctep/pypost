# PYPOST-770: Architecture

## Approach

Documentation-only change. No application code.

## Target edit

Add one bullet at the top of the `## Development` list in root `README.md`:

```markdown
*   [Developer documentation](doc/dev/README.md) — setup, architecture, capability docs, and audits.
```

Place before existing `make lint` / `make test` / `make clean` bullets so documentation is the
first developer resource listed.

## Rationale

- Relative path `doc/dev/README.md` works on GitHub and in local clones.
- Descriptive link text distinguishes dev docs from user-facing `doc/prometheus_monitoring.md` and
  `doc/mcp_integration.md` links in the Vision section.

## Out of scope

- `doc/dev/README.md` TOC updates (PYPOST-771)
- User guide (`doc/README.md`)

## Verification

- `rg 'doc/dev/README.md' README.md` returns the new bullet
- `make check` passes

# PYPOST-713: Document plaintext collection storage

## Goals

Operators need clear guidance that request templates in collection JSON files are stored
in cleartext on disk, and that secrets should live in hidden environment variables rather
than embedded directly in request fields.

## User Stories

- As an operator, I want to know where collection data is stored and that it is not
  encrypted, so I can protect my data directory and avoid hardcoding secrets in templates.
- As a developer, I want cross-links between the security audit (S-005) and collection
  storage docs so remediation status is traceable.

## Definition of Done

- `doc/dev/collection_storage.md` documents plaintext persistence and operator security
  guidance (use hidden env vars for secrets; do not embed credentials in URL/headers/body).
- `doc/dev/security_audit.md` cross-links to the collection storage doc and marks S-005
  operator documentation as addressed.
- `make check` passes.

## Task Description

Finding S-005 (R-P3-001) from PYPOST-685: `{data_dir}/collections/*.json` stores full
`RequestData` (URL, headers, params, body, post-script) without encryption. This is
expected for a local API client but must be documented as operator responsibility.

## Q&A

- **Why not encrypt collections?** Out of scope — remediation is operator documentation only.
- **Where should secrets go?** Hidden environment variables; see
  [hidden_variables.md](../../doc/dev/hidden_variables.md) and
  [environment_encryption_at_rest.md](../../doc/dev/environment_encryption_at_rest.md).

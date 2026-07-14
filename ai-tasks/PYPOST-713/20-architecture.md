# PYPOST-713: Architecture

## Approach

Pure documentation change, no code. Add an operator-facing **Security** section to
`doc/dev/collection_storage.md` describing:

- What is persisted (`RequestData` fields in `{data_dir}/collections/{id}.json`)
- Cleartext on disk with no encryption layer (contrast with hidden env encryption)
- Recommended pattern: `{{VAR}}` placeholders + hidden environment variables
- Operational risks: backups, sync folders, shared machines, version control

Update `doc/dev/security_audit.md`:

- Link S-005 finding to the new guidance
- Add `collection_storage.md` to intro and Related sections
- Mark R-P3-001 / PYPOST-713 as resolved in recommendations table

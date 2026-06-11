# Roadmap: PYPOST-493

## Step Status

- [x] STEP 1–7 complete

## Summary

- Extracted `_sync_env_variables_from_table` shared by edits and deletes
- Delete path removes table row + sync instead of full `on_env_selected` reload
- `_append_trailing_add_row` / `_ensure_trailing_add_row_present` preserve add row UX

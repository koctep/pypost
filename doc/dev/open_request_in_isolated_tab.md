# Open Request in Isolated Tab

## Overview

Users can open multiple tabs for the same saved request. The Collections tree holds canonical
saved instances from storage, but each open tab must own its own in-memory draft. Left-click
and the **New tab** context menu both supply deep copies of `RequestData` so unsaved edits
do not leak across tabs or back into the tree model.

When the same saved request is open in more than one isolated tab, [PYPOST-408](https://pypost.atlassian.net/browse/PYPOST-408)
adds **awareness and naming consistency**: sibling tabs are notified when another tab saves,
tab labels stay aligned after rename or save-driven name changes, and users can adopt the
latest on-disk version without silent data loss.

## Architecture

- **`CollectionsPresenter`**: emits deep copies on both `open_request_in_tab` (left-click) and
  `open_request_in_isolated_tab` (**New tab** context menu).
- **`TabsPresenter`**: owns tab widgets, save handling, label sync, and sibling notification;
  `add_new_tab` deep-copies any non-`None` `request_data` before creating `RequestTab`.
- **`RequestTab`**: holds per-tab `persisted_baseline` (last adopted on-disk snapshot) and
  `stale_persisted` (session flag when the user dismissed a stale notice or kept a draft).
- **`pypost/core/request_sync.py`**: pure helpers to snapshot, compare, and detect dirty state
  across persisted editor fields.

### Persisted baseline

Each `RequestTab` stores `persisted_baseline: RequestData | None` — a deep copy of the request
fields that are written to disk. The baseline is set when:

- A tab is opened (`add_new_tab`, `restore_tabs`)
- The tab's save completes (overwrite path)
- The user chooses **Load latest** after a sibling save
- Collections rename updates `persisted_baseline.name` on matching tabs

**Dirty** means the current editor UI differs from `persisted_baseline` (via
`is_tab_dirty`). **Stale** means disk moved ahead of the tab's baseline because another tab
saved the same request id.

### Save broadcast

On successful **overwrite** save (`_handle_save_request` when the request id already exists):

1. The saving tab updates `request_data`, `persisted_baseline`, and clears `stale_persisted`.
2. `request_persisted.emit(request_id, snapshot, source_tab)` notifies sibling handlers.
3. `_sync_tab_labels_for_request` updates tab titles when the saved name changed.
4. `request_saved` still triggers Collections reload (unchanged).

First-time save and Save As do **not** emit `request_persisted` (no sibling tabs share the new
id yet).

### Sibling notification (`_on_request_persisted`)

For every other open tab with the same `request_data.id`:

| Tab state | Dialog | User choice |
| --- | --- | --- |
| **Dirty** (unsaved edits) | Warning: saved elsewhere | **Keep my changes** — editor unchanged, `stale_persisted = True` |
| **Dirty** | | **Load latest** — reload editor from disk snapshot |
| **Clean** | Information: may show outdated saved content | **Dismiss** — editor unchanged, `stale_persisted = True` |
| **Clean** | | **Load latest** — reload editor from disk snapshot |

Tabs whose baseline already matches the new snapshot are skipped (no dialog).

### Save-from-stale guard

If a tab has `stale_persisted` set and disk is newer than its baseline, `_check_stale_before_save`
prompts before overwrite save. The standard overwrite confirmation also mentions a newer on-disk
version when the tab baseline differs from disk (even without `stale_persisted`).

## Implementation Details

1. **Left-click**
   Clicking a request row in Collections emits `open_request_in_tab` with
   `RequestData.model_copy(deep=True)`. Folder rows still expand/collapse only.
2. **Context menu**
   The `CollectionsPresenter` provides a **New tab** option when right-clicking a request node.
   When chosen, it emits `open_request_in_isolated_tab` with the same deep-copy contract.
3. **Tab injection**
   `MainWindow` routes both signals to `TabsPresenter.add_new_tab`. That method deep-copies
   non-`None` payloads again before constructing `RequestTab`, so every caller gets an owned
   buffer even if a shared reference is passed.
4. **Restoration on startup**
   `TabsPresenter.restore_tabs()` passes deep copies when restoring tabs so multiple restored
   tabs do not bind to the same memory reference.

## API / Usage

### `request_sync.snapshot_persisted_fields(data)`

Returns a deep copy of `RequestData` used as a persisted-field snapshot. Comparison uses
`_PERSISTED_FIELD_NAMES` (name, url, method, headers, params, body, body_type, yaml_as_json,
post_script, expose_as_mcp, retry_policy).

### `request_sync.persisted_fields_equal(a, b)`

Returns `True` when two requests match on all persisted editor fields.

### `request_sync.is_tab_dirty(tab)`

Returns `True` when the tab editor differs from `tab.persisted_baseline`.

### `TabsPresenter.request_persisted`

```python
request_persisted = Signal(str, object, object)
# (request_id, persisted_snapshot, source_tab)
```

Connected internally to `_on_request_persisted`. Emitted after overwrite saves only.

## Configuration

No environment variables or settings keys are specific to isolated-tab sync. Overwrite
confirmation still respects `AppSettings.confirm_overwrite_request`.

## Troubleshooting

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| Sibling tab never gets a stale dialog | Tabs do not share the same saved `id`, or baseline already matches disk | Confirm both tabs opened the same saved request; check `request_persisted` emission on save |
| Tab title not updated after save rename | Label sync only runs for matching `request_data.id` | Verify `_sync_tab_labels_for_request` and that save was an overwrite, not Save As |
| User saves over newer disk without extra prompt | Tab was not marked `stale_persisted` (user never saw/dismissed sibling notice) | Non-stale path still uses standard overwrite confirm when baseline ≠ disk |
| Edits in tab A appear in tab B | Caller bypassed `add_new_tab` or mutated shared tree `UserRole` data | Confirm tab was opened via Collections or restore; check `add_new_tab` copy path |

### Logging

- `save_request_overwrite_succeeded` / `save_request_overwrite_cancelled` — standard overwrite
  save paths.
- `save_request_stale_cancelled` — user declined overwrite when `stale_persisted` and disk is
  newer than baseline.

Stale-dialog button choices (Keep / Load latest / Dismiss) are not logged.

## Limitations and Future Work

- **No persistent stale indicator** after the dialog is dismissed; `stale_persisted` is
  session-only until reload or save. A non-modal banner or tab tooltip is optional follow-up.
- **External disk changes** (hand-edited collection files while PyPost is open) are not
  detected; notification is limited to saves within the running session.
- **No merge/diff** for concurrent drafts; users choose keep draft or load latest explicitly.
- **Performance**: `persisted_fields_equal` compares full persisted fields (including large
  bodies) on each sibling notification; acceptable for typical requests.

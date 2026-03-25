# PYPOST-405: Review and Technical Debt

## Review
The goal of this task was to add an independent "New tab" context menu action on request items in the collections tree. This allows users to open duplicate editors for the same saved request without those tabs inadvertently sharing unsaved state due to Python object reference sharing.

The implementation satisfied the definition of done:
- Context menu option appears only for `request` items.
- Tab opening logic uses `model_copy(deep=True)` so that `RequestData` graphs are isolated.
- The `restore_tabs` routine on startup was also fixed so that multiple tabs tracking the same `id` aren't aliased to the identical model reference.
- Both observability and code cleanup steps were performed, keeping logs detailed and code concise.

## Technical Debt Analysis
- **Left-click tree navigation:** [PYPOST-406] (Priority: Medium) Currently, if a user clicks a request in the tree that is already open in a tab, it might just focus that tab, or if opened multiple times by manually adding a tab and selecting it, it could still be linking to the same underlying `RequestData` instance depending on the exact flow used. Left-clicks were deliberately kept out of scope for this story, but the team should unify the object-copying behavior whenever a fresh tab is populated from the tree.
- **RequestData Deep Copy Overheads:** [PYPOST-407] (Priority: Low) Doing deep copies works well enough, but if `RequestData` becomes significantly heavier (e.g. holding very large response buffers directly, which it currently avoids since they're in `ResponseView`/`History`), deep copies might impose minor memory cost spikes.
- **Syncing names/metadata across duplicates:** [PYPOST-408] (Priority: Medium) When a request is renamed, `rename_request_tabs` correctly updates the titles of all isolated tabs that share that `id`. However, if other metadata changes from another tab (e.g. saving an updated URL), the stale tabs do not get notified. This represents a known trade-off accepted in the design phase, but in a future iteration, an event bus could proactively warn tabs that the disk state has changed.
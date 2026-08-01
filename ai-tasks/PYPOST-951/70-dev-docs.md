# PYPOST-951: Dev Docs

## Updates

- [x] `doc/dev/agent_golden_e2e.md` — new section **Tab-strip hazards:
  removeTab orphans** (symptoms, safe strip pattern, post-strip scoping);
  plus-tab and troubleshooting cross-links
- [x] `doc/dev/ui_actions.md` — troubleshooting entry for find/action failure
  after tab strip (PYPOST-951)
- [x] `doc/dev/agent_e2e.md` — umbrella troubleshooting row for orphan finds
  after strip

## Verification

- [x] Broader warning covers `removeTab`, `deleteLater`, `processEvents`, and
  window-scoped vs current-tab identity scoping
- [x] Safe pattern references `_strip_request_tabs` in golden test module
- [x] Cross-links use stable anchor `#tab-strip-hazards-removetab-orphans`

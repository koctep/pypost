# Technical Debt Analysis: PYPOST-1190

## Debt Assessment

- **Scope Completed**: Unsaved HTTP draft tab closing is now fully wired to the shared Discard / Keep dialog (`prompt_unsaved_draft_tab_close`) with factory dirty detection.
- **Future Considerations**:
  - Consistent naming across protocol draft observability test classes (currently colocated in `TestWebsocketDraftObservability`).

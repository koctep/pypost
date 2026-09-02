# PYPOST-1244: Add candidate display limit and prefix trie indexing

## Research

The shared widget in `pypost/ui/widgets/variable_autocomplete_line_edit.py` currently scans
every variable name on each trigger. The existing API supplies names only and is shared by
query parameters, headers, and request-body editors.

## Implementation Plan

1. Add a small in-memory prefix trie that stores variable names at terminal nodes.
2. Rebuild the trie in `set_variables()` and during construction.
3. Resolve case-insensitive prefix matches from the trie and truncate the result list before
   populating the existing popup.
4. Preserve the current public methods, logging, metrics, selection behavior, and masking.
5. Step 3 will assert the default and custom limits, indexed lookup behavior, and refresh.

## Architecture

`VariableAutocompleteLineEdit` owns a name-only `PrefixTrie` and a positive candidate limit.
`trigger_autocomplete()` extracts the active reference prefix, queries the trie, and passes at
most the configured number of names to the existing popup. `set_variables()` replaces the
name snapshot and rebuilds the index, allowing delegates to refresh open editors as before.

The trie is an internal lookup optimization; no host integration or value-resolution contract
changes.

## Q&A

- Q: Does the result limit alter selection semantics? A: No; it only bounds popup candidates.
- Q: Are variable values involved? A: No, only names are stored in the index.

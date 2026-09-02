# Variable Autocomplete Performance

`VariableAutocompleteLineEdit` indexes variable names in a case-insensitive prefix trie.
Autocomplete queries walk the prefix and return at most `candidate_limit` names.

The default candidate limit is 30. Integrations may pass a positive `candidate_limit` when
constructing an editor. Calling `set_variables()` rebuilds the index and discards old names.
Only names are indexed; variable values are never read by this component.

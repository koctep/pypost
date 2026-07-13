# PYPOST-755: Guard JSON pretty-print for large bodies

Skip `json.loads`/`json.dumps` in `display_response` when body exceeds
`LARGE_DOC_CHAR_THRESHOLD` (100 KB). Show raw text instead.

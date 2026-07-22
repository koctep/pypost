# PYPOST-845: Architecture

Add `PLUS_TAB_PLACEHOLDER` in `widget_ids.py`. In `RequestTabHeader.ensure_plus_tab`,
call `set_widget_id(placeholder, PLUS_TAB_PLACEHOLDER)` instead of raw
`setObjectName("plus_tab_placeholder")`.

"""PYPOST-1245 red repros for shared validation and popup UI tokens."""

import inspect

import pytest

pytestmark = pytest.mark.timeout(60)


def test_shared_ui_tokens_define_validation_palette_and_popup_geometry():
    from pypost.ui.styles.ui_tokens import (
        AUTOCOMPLETE_POPUP_MAX_HEIGHT,
        AUTOCOMPLETE_POPUP_MIN_WIDTH,
        AUTOCOMPLETE_POPUP_ROW_HEIGHT,
        AUTOCOMPLETE_POPUP_VERTICAL_PADDING,
        VALIDATION_COLUMN_ERROR_COLOR,
        VALIDATION_LABEL_BACKGROUND,
        VALIDATION_LABEL_FOREGROUND,
        VALIDATION_LINE_BACKGROUND,
    )

    assert VALIDATION_LINE_BACKGROUND.name() == "#ffdcdc"
    assert VALIDATION_COLUMN_ERROR_COLOR.name() == "#dc3232"
    assert VALIDATION_LABEL_BACKGROUND == "#fdd"
    assert VALIDATION_LABEL_FOREGROUND == "#900"
    assert (AUTOCOMPLETE_POPUP_MIN_WIDTH, AUTOCOMPLETE_POPUP_MAX_HEIGHT) == (180, 160)
    assert (AUTOCOMPLETE_POPUP_ROW_HEIGHT, AUTOCOMPLETE_POPUP_VERTICAL_PADDING) == (24, 8)


def test_affected_widgets_reference_shared_tokens():
    import pypost.ui.widgets.code_editor as code_editor
    import pypost.ui.widgets.mcp_server_headers_table as headers_table
    import pypost.ui.widgets.variable_autocomplete_line_edit as autocomplete
    import pypost.ui.widgets.validate.validation_controller as validation_controller

    source = "\n".join(
        inspect.getsource(module)
        for module in (
            code_editor,
            headers_table,
            autocomplete,
            validation_controller,
        )
    )
    assert "ui_tokens" in source

"""PYPOST-792: tab layout regression guards (macOS broken tab rendering).

Two root causes are pinned here:

* The shipped stylesheet must not override ``QTabBar::tab`` geometry: setting
  any box-model property on the ``::tab`` sub-control disables native tab
  rendering and collapses every tab to its bare text width, so adjacent labels
  render as one string ("CollectionsHistory", "ParamsHeadersBodyScriptMCP").
* ``PyPostStyle`` must not force an oversized tab close-indicator metric: the
  old unconditional 48px value produced close buttons drawn over tab titles.
"""

import re

import pytest
from PySide6.QtWidgets import QApplication, QStyle, QTabBar, QTabWidget, QWidget

from pypost.ui.styles.style_manager import StyleManager
from pypost.ui.styles.custom_style import PyPostStyle
from pypost.ui.widgets.tab_header import RequestTabHeader

pytestmark = pytest.mark.timeout(60)

SIDEBAR_LABELS = ("Collections", "History")
EDITOR_SUBTAB_LABELS = ("Params", "Headers", "Body", "Script", "MCP")

# Every native style pads tabs well beyond the text advance (Fusion adds
# PM_TabBarTabHSpace = 24px); the broken zero-padding rule collapsed the tab
# to the bare text width, so a small positive threshold discriminates cleanly.
MIN_TAB_HORIZONTAL_PADDING_PX = 6


@pytest.fixture(scope="module")
def qapp_with_styles():
    """QApplication with the production stylesheet applied, restored on exit."""
    app = QApplication.instance() or QApplication([])
    orig_stylesheet = app.styleSheet()
    StyleManager().apply_styles(app)
    yield app
    app.setStyleSheet(orig_stylesheet)


def _make_tab_bar(labels) -> QTabBar:
    # expanding=False keeps tabRect() at content size (as in the request tab
    # bar and QTabWidget layouts); the default expanding mode stretches tabs
    # to the widget width, which would mask a collapsed-padding regression.
    bar = QTabBar()
    bar.setExpanding(False)
    for label in labels:
        bar.addTab(label)
    bar.ensurePolished()
    return bar


def _assert_native_tab_spacing(bar: QTabBar, labels) -> None:
    metrics = bar.fontMetrics()
    rects = [bar.tabRect(i) for i in range(bar.count())]
    for rect, label in zip(rects, labels):
        advance = metrics.horizontalAdvance(label)
        assert rect.width() >= advance + MIN_TAB_HORIZONTAL_PADDING_PX, (
            f"tab '{label}' is {rect.width()}px wide for {advance}px of text: "
            "no padding around the label, native tab rendering is disabled"
        )
    for i, first in enumerate(rects):
        for second in rects[i + 1:]:
            assert not first.intersects(second), (
                f"tab rects {first} and {second} overlap"
            )


def test_loaded_styles_do_not_customize_tab_geometry():
    """No shipped QSS rule may target QTabBar::tab (kills native layout)."""
    styles = StyleManager().load_styles()
    active_rules = re.sub(r"/\*.*?\*/", "", styles, flags=re.DOTALL)
    assert not re.search(r"QTabBar::tab\b", active_rules), (
        "QTabBar::tab rule found in shipped QSS; styling this sub-control "
        "disables native tab rendering (PYPOST-792)"
    )


def test_sidebar_tabs_have_native_spacing(qapp_with_styles):
    bar = _make_tab_bar(SIDEBAR_LABELS)
    _assert_native_tab_spacing(bar, SIDEBAR_LABELS)


def test_editor_subtabs_have_native_spacing(qapp_with_styles):
    bar = _make_tab_bar(EDITOR_SUBTAB_LABELS)
    _assert_native_tab_spacing(bar, EDITOR_SUBTAB_LABELS)


@pytest.fixture()
def qapp_pypost_style(qapp_with_styles):
    """App running the production PyPostStyle; style and palette restored."""
    app = qapp_with_styles
    orig_style = app.style()
    orig_palette = app.palette()
    app.setStyle(PyPostStyle())
    yield app
    try:
        app.setStyle(orig_style)
    except RuntimeError:
        # Qt deleted the previous style instance; fall back to a fresh one.
        app.setStyle(PyPostStyle())
    app.setPalette(orig_palette)


def _close_indicator_metrics():
    return (QStyle.PM_TabCloseIndicatorWidth, QStyle.PM_TabCloseIndicatorHeight)


def test_close_indicator_defaults_to_base_style_metric(qapp):
    """Without an explicit override PyPostStyle must report native metrics."""
    style = PyPostStyle()
    for metric in _close_indicator_metrics():
        assert style.pixelMetric(metric) == style.baseStyle().pixelMetric(metric)


def test_close_indicator_override_is_opt_in(qapp):
    style = PyPostStyle()
    style.set_close_button_size(48)
    for metric in _close_indicator_metrics():
        assert style.pixelMetric(metric) == 48


def test_apply_theme_system_uses_native_close_metrics(qapp_pypost_style):
    """The production 'system' theme path must not force a close-button size."""
    app = qapp_pypost_style
    # Clear the stylesheet: app.style() must be the real style, not the
    # QStyleSheetStyle wrapper Qt installs while a stylesheet is active.
    app.setStyleSheet("")
    try:
        StyleManager().apply_theme(app, "system")
        style = app.style()
        assert isinstance(style, PyPostStyle)
        for metric in _close_indicator_metrics():
            assert style.pixelMetric(metric) == style.baseStyle().pixelMetric(metric)
    finally:
        StyleManager().apply_styles(app)


def _tab_close_button(bar: QTabBar, index: int):
    for side in (QTabBar.ButtonPosition.LeftSide, QTabBar.ButtonPosition.RightSide):
        button = bar.tabButton(index, side)
        if button is not None:
            return button
    return None


def test_request_tab_close_button_uses_native_size(qapp_pypost_style):
    """A request tab's close button is laid out at the native indicator size.

    Containment alone cannot catch the regression offscreen: with an oversized
    metric the tab simply grows around the 48px button (the title overlap only
    materializes under the native macOS renderer). Comparing the laid-out
    button against the *base* style's metric discriminates on every platform.
    """
    tabs = QTabWidget()
    header = RequestTabHeader()
    header.attach(tabs)
    index = tabs.insertTab(header.insert_index_before_plus(), QWidget(), "test")
    tabs.show()
    QApplication.processEvents()
    try:
        button = _tab_close_button(header.tab_bar, index)
        assert button is not None, "closable request tab has no close button"
        geometry = button.geometry()
        assert geometry.height() > 0, "close button was never laid out"

        # app.style() is Qt's stylesheet wrapper here; an unconfigured
        # PyPostStyle forwards to the same platform-default base metrics
        # (see test_close_indicator_defaults_to_base_style_metric).
        probe = PyPostStyle()
        assert geometry.width() == probe.pixelMetric(QStyle.PM_TabCloseIndicatorWidth)
        assert geometry.height() == probe.pixelMetric(QStyle.PM_TabCloseIndicatorHeight)

        tab_rect = header.tab_bar.tabRect(index)
        assert geometry.height() <= tab_rect.height()
        assert geometry.width() <= tab_rect.width()
    finally:
        tabs.deleteLater()

"""Request tab bar chrome: closable tabs, trailing + control, label updates."""

from __future__ import annotations


from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QPushButton, QTabBar, QTabWidget, QWidget

PLUS_TAB_MARKER = "pypost_plus_tab"
ADD_TAB_BUTTON_SIZE = 24


class RequestTabHeader(QObject):
    """Owns request-tab bar controls: close buttons, trailing + tab, and label helpers."""

    new_tab_requested = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tab_bar = QTabBar()
        self._tab_bar.setExpanding(False)
        self._tabs: QTabWidget | None = None
        self._tab_bar.tabBarClicked.connect(self._on_tab_bar_clicked)

    @property
    def tab_bar(self) -> QTabBar:
        return self._tab_bar

    @property
    def tab_widget(self) -> QTabWidget | None:
        return self._tabs

    def attach(self, tab_widget: QTabWidget) -> None:
        """Wire this header to a tab widget and install the trailing + control."""
        self._tabs = tab_widget
        tab_widget.setTabBar(self._tab_bar)
        tab_widget.setTabsClosable(True)
        self.ensure_plus_tab()

    def ensure_plus_tab(self) -> None:
        """Add the trailing plus placeholder tab when missing."""
        if self._tabs is None or self.plus_tab_index() >= 0:
            return
        placeholder = QWidget()
        placeholder.setObjectName("plus_tab_placeholder")
        index = self._tabs.addTab(placeholder, "")
        self._tab_bar.setTabData(index, PLUS_TAB_MARKER)
        plus_btn = QPushButton("+")
        plus_btn.setToolTip("New Tab (Ctrl+N)")
        plus_btn.setFixedSize(ADD_TAB_BUTTON_SIZE, ADD_TAB_BUTTON_SIZE)
        plus_btn.clicked.connect(self.new_tab_requested.emit)
        self._tab_bar.setTabButton(index, QTabBar.ButtonPosition.LeftSide, plus_btn)
        self._tab_bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, None)

    def plus_tab_index(self) -> int:
        for i in range(self._tab_bar.count()):
            if self._tab_bar.tabData(i) == PLUS_TAB_MARKER:
                return i
        return -1

    def is_plus_tab_index(self, index: int) -> bool:
        if not 0 <= index < self._tab_bar.count():
            return False
        return self._tab_bar.tabData(index) == PLUS_TAB_MARKER

    def navigable_tab_indices(self) -> list[int]:
        if self._tabs is None:
            return []
        return [i for i in range(self._tabs.count()) if not self.is_plus_tab_index(i)]

    def insert_index_before_plus(self) -> int:
        """Index where a new request tab should be inserted, or -1 if no plus tab."""
        return self.plus_tab_index()

    def set_tab_label(self, index: int, label: str) -> None:
        if self._tabs is not None:
            self._tabs.setTabText(index, label)

    def _on_tab_bar_clicked(self, index: int) -> None:
        if self.is_plus_tab_index(index):
            self.new_tab_requested.emit()

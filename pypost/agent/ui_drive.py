"""Duck-typed UI drive session protocol shared by spawn and attach paths."""

from __future__ import annotations

from typing import Protocol

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from pypost.agent.ui_actions import (
    find_widget,
    ui_click,
    ui_fill,
    ui_select,
    ui_send_key,
)
from pypost.ui.widget_ids import REQUEST_TABS


class UiDriveSession(Protocol):
    """Minimal surface for ``AgentUiActionsMcpServer`` tool dispatch."""

    def ui_click(self, widget_id: str, *, in_current_tab: bool = False) -> None: ...

    def ui_fill(
        self,
        widget_id: str,
        text: str,
        *,
        in_current_tab: bool = False,
        via_key_clicks: bool = False,
        delay: int = -1,
    ) -> None: ...

    def ui_select(
        self,
        widget_id: str,
        option: str | int,
        *,
        in_current_tab: bool = False,
    ) -> None: ...

    def ui_send_key(
        self,
        widget_id: str,
        key: str,
        *,
        modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
        in_current_tab: bool = False,
    ) -> None: ...


class MainWindowUiDrive:
    """Drive ``ui_*`` against a live main-window root (attach host)."""

    def __init__(self, window: QWidget) -> None:
        self._window = window

    def _action_root(self, *, in_current_tab: bool) -> QWidget:
        if not in_current_tab:
            return self._window
        tabs = find_widget(self._window, REQUEST_TABS)
        current = tabs.currentWidget()
        if current is None:
            raise RuntimeError("No current request tab")
        return current

    def ui_click(self, widget_id: str, *, in_current_tab: bool = False) -> None:
        ui_click(self._action_root(in_current_tab=in_current_tab), widget_id)

    def ui_fill(
        self,
        widget_id: str,
        text: str,
        *,
        in_current_tab: bool = False,
        via_key_clicks: bool = False,
        delay: int = -1,
    ) -> None:
        ui_fill(
            self._action_root(in_current_tab=in_current_tab),
            widget_id,
            text,
            via_key_clicks=via_key_clicks,
            delay=delay,
        )

    def ui_select(
        self,
        widget_id: str,
        option: str | int,
        *,
        in_current_tab: bool = False,
    ) -> None:
        ui_select(
            self._action_root(in_current_tab=in_current_tab),
            widget_id,
            option,
        )

    def ui_send_key(
        self,
        widget_id: str,
        key: str,
        *,
        modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
        in_current_tab: bool = False,
    ) -> None:
        ui_send_key(
            self._action_root(in_current_tab=in_current_tab),
            widget_id,
            key,
            modifiers=modifiers,
        )

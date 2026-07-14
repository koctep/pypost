from PySide6.QtWidgets import QProxyStyle, QStyle


class PyPostStyle(QProxyStyle):
    """Custom style for PyPost application.

    All metrics come from the base (platform) style by default so tabs render
    natively. The tab close-indicator size can be overridden explicitly via
    :meth:`set_close_button_size`; no production caller does so (PYPOST-792:
    an unconditional 48px indicator was drawn over request tab titles).
    """

    _CLOSE_INDICATOR_METRICS = (
        QStyle.PM_TabCloseIndicatorWidth,
        QStyle.PM_TabCloseIndicatorHeight,
    )

    def __init__(self, base_style=None):
        super().__init__(base_style)
        self.close_button_size: int | None = None

    def pixelMetric(self, metric, option=None, widget=None):
        """Return the configured close-indicator size, else the base metric."""
        if metric in self._CLOSE_INDICATOR_METRICS and self.close_button_size is not None:
            return self.close_button_size
        return super().pixelMetric(metric, option, widget)

    def set_close_button_size(self, size: int) -> None:
        """Set the size of the tab close button.

        Args:
            size: Width and height in pixels used for the
                ``PM_TabCloseIndicatorWidth``/``Height`` metrics.
        """
        self.close_button_size = size

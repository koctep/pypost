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
        """Opt-in override for tab close-indicator width and height metrics.

        Production code leaves ``close_button_size`` at ``None`` so
        ``PM_TabCloseIndicatorWidth`` / ``Height`` come from the platform style
        (PYPOST-792). Call this only when native metrics are unsuitable — for
        example a future platform where indicators are clipped, an accessibility
        requirement for larger hit targets, or a targeted experiment in tests.

        Do **not** call globally at startup; an oversized value (e.g. 48px) draws
        the close control over tab titles while native padding stays intact.

        Args:
            size: Width and height in pixels for both close-indicator metrics.
        """
        self.close_button_size = size

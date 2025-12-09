from PySide6.QtWidgets import QProxyStyle, QStyle
from PySide6.QtCore import QSize

class PyPostStyle(QProxyStyle):
    """Custom style for PyPost application."""
    
    def __init__(self, base_style=None):
        super().__init__(base_style)
        self.close_button_size = 48  # Default size for close button
    
    def pixelMetric(self, metric, option=None, widget=None):
        """Override pixel metrics for custom sizing."""
        if metric == QStyle.PM_TabCloseIndicatorWidth:
            return self.close_button_size
        elif metric == QStyle.PM_TabCloseIndicatorHeight:
            return self.close_button_size
        return super().pixelMetric(metric, option, widget)
    
    def set_close_button_size(self, size: int):
        """Set the size of the tab close button."""
        self.close_button_size = size


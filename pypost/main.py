import sys
import logging
from PySide6.QtWidgets import QApplication
from pypost.ui.main_window import MainWindow
from pypost.ui.styles.custom_style import PyPostStyle
from pypost.core.config_manager import ConfigManager
from pypost.core.metrics import MetricsManager
from pypost.core.template_service import TemplateService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    logger.info("PyPost starting up")
    app = QApplication(sys.argv)
    app.setApplicationName("PyPost")

    # Initialize Config and Metrics
    config_manager = ConfigManager()
    settings = config_manager.load_config()

    metrics_manager = MetricsManager()
    metrics_manager.start_server(settings.metrics_host, settings.metrics_port)

    template_service = TemplateService()
    logger.info("template_service_created id=%d", id(template_service))

    # Apply custom style
    custom_style = PyPostStyle()
    custom_style.set_close_button_size(48)
    app.setStyle(custom_style)

    window = MainWindow(metrics=metrics_manager, template_service=template_service)
    window.show()

    exit_code = app.exec()

    # Stop metrics server on exit
    logger.info("PyPost shutting down")
    metrics_manager.stop_server()

    sys.exit(exit_code)

if __name__ == "__main__":
    main()

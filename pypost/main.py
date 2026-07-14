import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from pypost.core.alert_manager import AlertManager
from pypost.core.config_manager import ConfigManager
from pypost.core.metrics import MetricsManager
from pypost.core.template_service import TemplateService
from pypost.ui.main_window import MainWindow
from pypost.ui.styles.custom_style import PyPostStyle

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    logger.info("PyPost starting up")
    app = QApplication(sys.argv)
    app.setApplicationName("PyPost")

    # Composition root: load settings once for MetricsManager, AlertManager, and
    # MainWindow. The same ConfigManager instance is injected into MainWindow.
    config_manager = ConfigManager()
    settings = config_manager.load_config()

    metrics_manager = MetricsManager()
    metrics_manager.start_server(settings.metrics_host, settings.metrics_port)

    template_service = TemplateService(metrics=metrics_manager)
    logger.info("template_service_created id=%d", id(template_service))

    log_path = Path(settings.alert_log_path) if settings.alert_log_path else None
    alert_manager = AlertManager(
        log_path=log_path,
        webhook_url=settings.alert_webhook_url,
        webhook_auth_header=settings.alert_webhook_auth_header,
    )
    logger.info(
        "alert_manager_created log_path=%s webhook_url_set=%s",
        log_path,
        bool(settings.alert_webhook_url),
    )

    # Apply custom style (native metrics by default; see PyPostStyle)
    app.setStyle(PyPostStyle())

    window = MainWindow(
        metrics=metrics_manager,
        template_service=template_service,
        config_manager=config_manager,
        alert_manager=alert_manager,
    )
    window.show()

    exit_code = app.exec()

    # Stop metrics server on exit
    logger.info("PyPost shutting down")
    metrics_manager.stop_server()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

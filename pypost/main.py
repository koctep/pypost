import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QApplication

from pypost.core.alert_manager import AlertManager
from pypost.core.config_manager import ConfigManager
from pypost.core.history_manager import HistoryManager
from pypost.core.qt.mcp_server import MCPServerManager
from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.core.qt.metrics import MetricsManager
from pypost.core.qt.state_manager import StateManager
from pypost.core.request_manager import RequestManager
from pypost.core.storage import StorageManager
from pypost.core.template_service import TemplateService
from pypost.models.settings import AppSettings
from pypost.ui.main_window import MainWindow

_LOG_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


def _resolve_log_level(name: str) -> int:
    return _LOG_LEVELS.get((name or "INFO").upper(), logging.INFO)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ComposedApp:
    """Wired application graph shared by interactive main and agent sessions."""

    window: MainWindow
    metrics: MetricsManager
    mcp_manager: MCPServerManager
    mcp_registry: MCPServerRegistry
    config_manager: ConfigManager
    settings: AppSettings


def compose_app(
    *,
    config_dir: Path | str | None = None,
    data_dir: Path | str | None = None,
    metrics_host: str | None = None,
    metrics_port: int | None = None,
    apply_log_level: bool = True,
) -> ComposedApp:
    """Build managers and MainWindow with injectable paths and metrics bind.

    Both interactive ``main()`` and ``AgentAppSession`` use this factory so the
    object graph stays singular; only event-loop ownership and isolation knobs
    differ between callers.
    """
    config_kwargs: dict[str, Any] = {}
    if config_dir is not None:
        config_kwargs["config_dir"] = config_dir
    config_manager = ConfigManager(**config_kwargs)
    settings = config_manager.load_config()
    state_manager = StateManager(config_manager, settings)

    if metrics_host is not None:
        settings.metrics_host = metrics_host
    if metrics_port is not None:
        settings.metrics_port = metrics_port

    if apply_log_level:
        logging.getLogger().setLevel(_resolve_log_level(settings.log_level))
        logger.info("log_level_applied level=%s", settings.log_level.upper())

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

    history_kwargs: dict[str, Any] = {
        "defer_initial_load": True,
        "metrics": metrics_manager,
    }
    if data_dir is not None:
        history_kwargs["history_path"] = Path(data_dir) / "history.json"
    history_manager = HistoryManager(**history_kwargs)
    logger.info("history_manager_created id=%d", id(history_manager))

    storage_kwargs: dict[str, Any] = {"metrics": metrics_manager}
    if data_dir is not None:
        storage_kwargs["data_dir"] = data_dir
    storage = StorageManager(**storage_kwargs)
    storage.apply_encryption_settings(settings)
    logger.info("storage_created id=%d encryption_applied=true", id(storage))

    request_manager = RequestManager(storage, defer_initial_load=True)
    logger.info("request_manager_created id=%d", id(request_manager))

    mcp_manager = MCPServerManager(
        metrics=metrics_manager,
        template_service=template_service,
    )
    logger.info("mcp_manager_created id=%d", id(mcp_manager))

    window = MainWindow(
        metrics=metrics_manager,
        template_service=template_service,
        config_manager=config_manager,
        settings=settings,
        state_manager=state_manager,
        alert_manager=alert_manager,
        history_manager=history_manager,
        storage=storage,
        request_manager=request_manager,
        mcp_manager=mcp_manager,
    )
    return ComposedApp(
        window=window,
        metrics=metrics_manager,
        mcp_manager=mcp_manager,
        mcp_registry=window.mcp_controller.registry,
        config_manager=config_manager,
        settings=settings,
    )


def main() -> None:
    logger.info("app_startup")
    app = QApplication(sys.argv)
    app.setApplicationName("PyPost")

    composed = compose_app()
    composed.window.show()

    from pypost.agent.attach_ipc import AgentUiAttachHost

    attach_host = AgentUiAttachHost(composed.window)
    logger.info(
        "agent_ui_attach_host_lifecycle action=start endpoint=%s",
        attach_host.endpoint,
    )
    try:
        attach_host.start()
    except OSError as exc:
        logger.error(
            "agent_ui_attach_host_lifecycle action=start_failed "
            "endpoint=%s error=%s",
            attach_host.endpoint,
            type(exc).__name__,
        )
        raise
    try:
        exit_code = app.exec()
    finally:
        logger.info(
            "agent_ui_attach_host_lifecycle action=stop endpoint=%s",
            attach_host.endpoint,
        )
        attach_host.stop()

    logger.info("app_shutdown")
    composed.mcp_registry.stop_all()
    composed.metrics.stop_server()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

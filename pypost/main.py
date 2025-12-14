import sys
from PySide6.QtWidgets import QApplication
from pypost.ui.main_window import MainWindow
from pypost.ui.styles.custom_style import PyPostStyle
from pypost.core.config_manager import ConfigManager
from pypost.core.metrics import MetricsManager

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PyPost")
    
    # Initialize Config and Metrics
    config_manager = ConfigManager()
    settings = config_manager.load_config()
    
    metrics_manager = MetricsManager()
    metrics_manager.start_server(settings.metrics_host, settings.metrics_port)
    
    # Apply custom style
    custom_style = PyPostStyle()
    custom_style.set_close_button_size(48)
    app.setStyle(custom_style)

    window = MainWindow()
    window.show()

    exit_code = app.exec()
    
    # Stop metrics server on exit
    metrics_manager.stop_server()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

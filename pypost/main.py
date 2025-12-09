import sys
from PySide6.QtWidgets import QApplication
from pypost.ui.main_window import MainWindow
from pypost.ui.styles.custom_style import PyPostStyle

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PyPost")
    
    # Apply custom style
    custom_style = PyPostStyle()
    custom_style.set_close_button_size(48)
    app.setStyle(custom_style)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

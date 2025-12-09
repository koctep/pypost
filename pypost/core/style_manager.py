import os
from pathlib import Path
from PySide6.QtWidgets import QApplication

class StyleManager:
    def __init__(self):
        # Path to pypost/ui/styles
        # This file is in pypost/core/style_manager.py, so parent.parent is pypost/
        self.root_dir = Path(__file__).parent.parent
        self.styles_dir = self.root_dir / 'ui' / 'styles'
        self.icons_dir = self.root_dir / 'ui' / 'resources' / 'icons'

    def load_styles(self) -> str:
        """Reads all .qss files from the styles directory and returns the combined stylesheet."""
        if not self.styles_dir.exists():
            return ""

        combined_style = ""
        try:
            # Sort files to ensure deterministic loading order (e.g. alphabetical)
            qss_files = sorted(self.styles_dir.glob("*.qss"))
            
            for file_path in qss_files:
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        combined_style += f"\n/* File: {file_path.name} */\n{content}\n"
                except Exception as e:
                    print(f"Error reading style file {file_path}: {e}")
                    
        except Exception as e:
            print(f"Error scanning styles directory: {e}")

        # Replace placeholders with absolute path
        # Convert to absolute path and resolve any symlinks
        icons_path = self.icons_dir.resolve().as_posix()
        combined_style = combined_style.replace("%ICONS_DIR%", icons_path)

        return combined_style

    def apply_styles(self, app_or_widget):
        """Applies the loaded styles to the given application or widget."""
        style_sheet = self.load_styles()
        # Replace existing stylesheet to avoid accumulation on reload
        app_or_widget.setStyleSheet(style_sheet)

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QComboBox, QLabel, QSplitter, QTreeView, QTabWidget, QMessageBox,
                               QPushButton, QApplication)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QFont, QIcon, QShortcut, QKeySequence
from PySide6.QtCore import Qt
from pathlib import Path
from pypost.ui.widgets.request_editor import RequestWidget
from pypost.ui.widgets.response_view import ResponseView
from pypost.core.worker import RequestWorker
from pypost.models.models import RequestData, Collection, Environment
from pypost.core.storage import StorageManager
from pypost.core.config_manager import ConfigManager
from pypost.core.style_manager import StyleManager
from pypost.ui.dialogs.save_dialog import SaveRequestDialog
from pypost.ui.dialogs.env_dialog import EnvironmentDialog
from pypost.ui.dialogs.settings_dialog import SettingsDialog

class RequestTab(QWidget):
    def __init__(self, request_data: RequestData = None):
        super().__init__()
        self.request_data = request_data
        self.layout = QVBoxLayout(self)
        self.splitter = QSplitter(Qt.Vertical)

        self.request_editor = RequestWidget(request_data)
        self.response_view = ResponseView()

        self.splitter.addWidget(self.request_editor)
        self.splitter.addWidget(self.response_view)

        self.layout.addWidget(self.splitter)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyPost")
        self.resize(1200, 800)

        self.storage = StorageManager()
        self.config_manager = ConfigManager()
        self.style_manager = StyleManager()
        
        # Load icons
        icons_dir = Path(__file__).parent / 'resources' / 'icons'
        self.icons = {
            'collection': QIcon(str(icons_dir / 'collection.svg')),
            'GET': QIcon(str(icons_dir / 'method-get.svg')),
            'POST': QIcon(str(icons_dir / 'method-post.svg')),
            'PUT': QIcon(str(icons_dir / 'method-put.svg')),
            'DELETE': QIcon(str(icons_dir / 'method-delete.svg')),
            'PATCH': QIcon(str(icons_dir / 'method-patch.svg')),
        }
        
        self.collections = []
        self.environments = []
        self.settings = self.config_manager.load_config()

        self.apply_settings(self.settings)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)

        # Top Bar
        self.top_bar = QHBoxLayout()
        self.env_selector = QComboBox()
        self.env_selector.addItems(["No Environment"])
        self.env_selector.currentIndexChanged.connect(self.on_env_changed)

        manage_env_btn = QPushButton("Manage")
        manage_env_btn.clicked.connect(self.open_env_manager)

        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self.open_settings)

        self.top_bar.addWidget(QLabel("Environment:"))
        self.top_bar.addWidget(self.env_selector)
        self.top_bar.addWidget(manage_env_btn)
        self.top_bar.addStretch()
        self.top_bar.addWidget(settings_btn)

        self.main_layout.addLayout(self.top_bar)

        # Main Content (Splitter)
        self.splitter = QSplitter(Qt.Horizontal)

        # Left Sidebar (Collections)
        self.collections_view = QTreeView()
        self.collections_view.setHeaderHidden(True)
        self.collections_model = QStandardItemModel()
        self.collections_view.setModel(self.collections_model)
        self.collections_view.clicked.connect(self.on_collection_clicked)
        self.splitter.addWidget(self.collections_view)

        # Right Content (Request Tabs)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.splitter.addWidget(self.tabs)

        self.splitter.setSizes([300, 900])
        self.main_layout.addWidget(self.splitter)

        # Load data
        self.load_collections()
        self.load_environments()

        # Restore open tabs
        self.restore_tabs()

        # Setup keyboard shortcuts
        self._setup_shortcuts()

    def restore_tabs(self):
        tabs_restored = False
        if self.settings.open_tabs:
            for request_id in self.settings.open_tabs:
                found_request = None
                # Search for request in collections
                for col in self.collections:
                    for req in col.requests:
                        if req.id == request_id:
                            found_request = req
                            break
                    if found_request:
                        break
                
                if found_request:
                    self.add_new_tab(found_request, save_state=False)
                    tabs_restored = True
        
        # If no tabs restored, open a default new one
        if not tabs_restored:
            self.add_new_tab(save_state=False)

    def load_collections(self):
        self.collections = self.storage.load_collections()
        self.collections_model.clear()

        for col in self.collections:
            col_item = QStandardItem(col.name)
            col_item.setData(col.id, Qt.UserRole)
            col_item.setEditable(False)
            col_item.setIcon(self.icons['collection'])

            for req in col.requests:
                req_item = QStandardItem(f"{req.method} {req.name}")
                req_item.setData(req, Qt.UserRole) # Store RequestData object
                req_item.setEditable(False)
                
                # Set icon based on HTTP method
                if req.method in self.icons:
                    req_item.setIcon(self.icons[req.method])
                
                col_item.appendRow(req_item)

            self.collections_model.appendRow(col_item)

    def load_environments(self):
        self.environments = self.storage.load_environments()
        
        # Block signals to prevent on_env_changed from firing during load
        self.env_selector.blockSignals(True)
        self.env_selector.clear()
        self.env_selector.addItem("No Environment", None)

        selected_index = 0
        for i, env in enumerate(self.environments):
            self.env_selector.addItem(env.name, env)
            if self.settings.last_environment_id == env.id:
                selected_index = i + 1

        self.env_selector.setCurrentIndex(selected_index)
        self.env_selector.blockSignals(False)

    def on_env_changed(self, index):
        selected_env = self.env_selector.itemData(index)
        if isinstance(selected_env, Environment):
            self.settings.last_environment_id = selected_env.id
        else:
            self.settings.last_environment_id = None
        
        self.config_manager.save_config(self.settings)

    def save_tabs_state(self):
        open_tabs_ids = []
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if isinstance(tab, RequestTab) and tab.request_data and tab.request_data.id:
                open_tabs_ids.append(tab.request_data.id)
        
        self.settings.open_tabs = open_tabs_ids
        self.config_manager.save_config(self.settings)

    def open_env_manager(self):
        dialog = EnvironmentDialog(self.environments, self)
        dialog.exec()
        # Save changes
        self.storage.save_environments(self.environments)
        self.load_environments() # Refresh combo

    def open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            new_settings = dialog.get_settings()
            if new_settings:
                self.settings = new_settings
                self.config_manager.save_config(self.settings)
                self.apply_settings(self.settings)

    def apply_settings(self, settings):
        app = QApplication.instance()
        if app:
            font = app.font()
            font.setPointSize(settings.font_size)
            app.setFont(font)
            
            # Apply external styles
            self.style_manager.apply_styles(app)

    def add_new_tab(self, request_data: RequestData = None, save_state: bool = True):
        tab = RequestTab(request_data)
        tab.request_editor.send_requested.connect(self.handle_send_request)
        tab.request_editor.save_requested.connect(self.handle_save_request)

        name = request_data.name if request_data else "New Request"
        self.tabs.addTab(tab, name)
        self.tabs.setCurrentWidget(tab)
        
        if save_state:
            self.save_tabs_state()

    def close_tab(self, index):
        self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self.add_new_tab(save_state=False)
        
        self.save_tabs_state()

    def on_collection_clicked(self, index):
        item = self.collections_model.itemFromIndex(index)
        data = item.data(Qt.UserRole)

        if isinstance(data, RequestData):
            # Check if already open
            for i in range(self.tabs.count()):
                tab = self.tabs.widget(i)
                if isinstance(tab, RequestTab) and tab.request_data and tab.request_data.id == data.id:
                    self.tabs.setCurrentIndex(i)
                    return

            self.add_new_tab(data)
        else:
            # It's a folder/collection - toggle expansion
            if self.collections_view.isExpanded(index):
                self.collections_view.collapse(index)
            else:
                self.collections_view.expand(index)

    def handle_save_request(self, request_data: RequestData):
        dialog = SaveRequestDialog(self.collections, self)
        if dialog.exec():
            # Update request data
            request_data.name = dialog.request_name

            # Find or create collection
            target_collection = None

            if dialog.selected_collection_id:
                for col in self.collections:
                    if col.id == dialog.selected_collection_id:
                        target_collection = col
                        break
            elif dialog.new_collection_name:
                target_collection = Collection(name=dialog.new_collection_name)
                self.collections.append(target_collection)

            if target_collection:
                # Check if updating existing request in collection
                existing_index = -1
                for i, req in enumerate(target_collection.requests):
                    if req.id == request_data.id:
                        existing_index = i
                        break

                if existing_index >= 0:
                    target_collection.requests[existing_index] = request_data
                else:
                    target_collection.requests.append(request_data)

                # Save to disk
                self.storage.save_collection(target_collection)

                # Reload UI
                self.load_collections()

                # Update tab title
                current_index = self.tabs.currentIndex()
                self.tabs.setTabText(current_index, request_data.name)
                
                # Update saved request in tab
                tab = self.tabs.widget(current_index)
                if isinstance(tab, RequestTab):
                     tab.request_data = request_data

                # Save tab state as ID might have been assigned/changed if it was new
                self.save_tabs_state()

    def handle_send_request(self, request_data: RequestData):
        sender_tab = None
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab.request_editor == self.sender():
                sender_tab = tab
                break

        if not sender_tab:
            return

        sender_tab.request_editor.send_btn.setEnabled(False)
        sender_tab.request_editor.send_btn.setText("Sending...")

        # Get current environment variables
        variables = {}
        selected_env = self.env_selector.currentData()
        if isinstance(selected_env, Environment):
            variables = selected_env.variables

        worker = RequestWorker(request_data, variables=variables)
        worker.finished.connect(lambda resp: self.on_request_finished(sender_tab, resp))
        worker.error.connect(lambda err: self.on_request_error(sender_tab, err))
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        worker.start()

        sender_tab.worker = worker

    def on_request_finished(self, tab: RequestTab, response):
        tab.response_view.display_response(response)
        tab.request_editor.send_btn.setEnabled(True)
        tab.request_editor.send_btn.setText("Send")

    def on_request_error(self, tab: RequestTab, error_msg):
        QMessageBox.critical(self, "Error", f"Request failed: {error_msg}")
        tab.request_editor.send_btn.setEnabled(True)
        tab.request_editor.send_btn.setText("Send")

    def _setup_shortcuts(self):
        """Initializes all global shortcuts."""
        # Exit application (Ctrl+Q)
        exit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        exit_shortcut.activated.connect(self.handle_exit)

        # Create new tab (Ctrl+N)
        new_tab_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_tab_shortcut.activated.connect(self.handle_new_tab)

        # Close current tab (Ctrl+W)
        close_tab_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_tab_shortcut.activated.connect(self.handle_close_tab)

        # Switch to next tab (Ctrl+Tab)
        # QTabWidget handles Ctrl+Tab automatically, but add explicit handling
        next_tab_shortcut = QShortcut(QKeySequence("Ctrl+Tab"), self)
        next_tab_shortcut.activated.connect(self.handle_next_tab)

        # Switch to previous tab (Ctrl+Shift+Tab)
        prev_tab_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        prev_tab_shortcut.activated.connect(self.handle_previous_tab)

        # Switch to specific tab (Alt+1 to Alt+9)
        for i in range(1, 10):
            idx = i - 1  # Store index in local variable for correct closure
            shortcut = QShortcut(QKeySequence(f"Alt+{i}"), self)
            shortcut.activated.connect(lambda index=idx: self.handle_switch_to_tab(index))

        # Open settings (Ctrl+, or F12)
        settings_shortcut1 = QShortcut(QKeySequence("Ctrl+,"), self)
        settings_shortcut1.activated.connect(self.handle_open_settings)
        settings_shortcut2 = QShortcut(QKeySequence("F12"), self)
        settings_shortcut2.activated.connect(self.handle_open_settings)

        # Manage environments (Ctrl+E)
        env_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        env_shortcut.activated.connect(self.handle_open_environments)

        # Focus on URL field (Ctrl+L or Alt+D)
        focus_url_shortcut1 = QShortcut(QKeySequence("Ctrl+L"), self)
        focus_url_shortcut1.activated.connect(self.handle_focus_url)
        focus_url_shortcut2 = QShortcut(QKeySequence("Alt+D"), self)
        focus_url_shortcut2.activated.connect(self.handle_focus_url)

        # Send request (F5) - global
        send_request_shortcut = QShortcut(QKeySequence("F5"), self)
        send_request_shortcut.activated.connect(self.handle_send_request_global)

        # Switch between request editor tabs (Ctrl+P/H/B) - global
        params_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        params_shortcut.activated.connect(self.handle_switch_to_params_global)
        headers_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        headers_shortcut.activated.connect(self.handle_switch_to_headers_global)
        body_shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        body_shortcut.activated.connect(self.handle_switch_to_body_global)

    def handle_exit(self):
        """Handler for application exit (Ctrl+Q)."""
        QApplication.instance().quit()

    def handle_new_tab(self):
        """Handler for creating new tab (Ctrl+N)."""
        self.add_new_tab()

    def handle_close_tab(self):
        """Handler for closing current tab (Ctrl+W)."""
        current_index = self.tabs.currentIndex()
        if current_index >= 0:
            self.close_tab(current_index)

    def handle_next_tab(self):
        """Handler for switching to next tab (Ctrl+Tab)."""
        current_index = self.tabs.currentIndex()
        if self.tabs.count() > 0:
            next_index = (current_index + 1) % self.tabs.count()
            self.tabs.setCurrentIndex(next_index)

    def handle_previous_tab(self):
        """Handler for switching to previous tab (Ctrl+Shift+Tab)."""
        current_index = self.tabs.currentIndex()
        if self.tabs.count() > 0:
            prev_index = (current_index - 1) % self.tabs.count()
            self.tabs.setCurrentIndex(prev_index)

    def handle_switch_to_tab(self, index: int):
        """Handler for switching to specific tab (Alt+1-9)."""
        if 0 <= index < self.tabs.count():
            self.tabs.setCurrentIndex(index)

    def handle_open_settings(self):
        """Handler for opening settings (Ctrl+, / F12)."""
        self.open_settings()

    def handle_open_environments(self):
        """Handler for opening environment manager (Ctrl+E)."""
        self.open_env_manager()

    def keyPressEvent(self, event):
        """Handles Ctrl+Enter for sending request globally."""
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Return:
            self.handle_send_request_global()
            event.accept()
            return
        super().keyPressEvent(event)

    def handle_focus_url(self):
        """Handler for setting focus on URL field (Ctrl+L / Alt+D)."""
        current_tab = self.tabs.currentWidget()
        if isinstance(current_tab, RequestTab):
            current_tab.request_editor.url_input.setFocus()
            current_tab.request_editor.url_input.selectAll()

    def handle_send_request_global(self):
        """Global handler for sending request (F5)."""
        current_tab = self.tabs.currentWidget()
        if isinstance(current_tab, RequestTab):
            current_tab.request_editor.on_send()

    def handle_switch_to_params_global(self):
        """Global handler for switching to Params tab (Ctrl+P)."""
        current_tab = self.tabs.currentWidget()
        if isinstance(current_tab, RequestTab):
            current_tab.request_editor.detail_tabs.setCurrentIndex(0)

    def handle_switch_to_headers_global(self):
        """Global handler for switching to Headers tab (Ctrl+H)."""
        current_tab = self.tabs.currentWidget()
        if isinstance(current_tab, RequestTab):
            current_tab.request_editor.detail_tabs.setCurrentIndex(1)

    def handle_switch_to_body_global(self):
        """Global handler for switching to Body tab (Ctrl+B)."""
        current_tab = self.tabs.currentWidget()
        if isinstance(current_tab, RequestTab):
            current_tab.request_editor.detail_tabs.setCurrentIndex(2)
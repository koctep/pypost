from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QComboBox, QLabel, QSplitter, QTreeView, QTabWidget, QMessageBox,
                               QPushButton, QApplication, QInputDialog)
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
from pypost.ui.dialogs.hotkeys_dialog import HotkeysDialog
from pypost.ui.dialogs.about_dialog import AboutDialog
from pypost.core.mcp_server import MCPServerManager
from pypost.core.metrics import MetricsManager

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
        self.mcp_manager = MCPServerManager()
        self.mcp_manager.status_changed.connect(self.on_mcp_status_changed)
        
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

        # Setup Menu Bar
        self._create_menu_bar()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)

        # Top Bar
        self.top_bar = QHBoxLayout()
        self.env_selector = QComboBox()
        self.env_selector.addItems(["No Environment"])
        self.env_selector.currentIndexChanged.connect(self.on_env_changed)

        self.manage_env_btn = QPushButton("Manage")
        self.manage_env_btn.clicked.connect(self.open_env_manager)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        
        self.env_label = QLabel("Environment:")
        self.mcp_status_label = QLabel("MCP: OFF")
        self.mcp_status_label.setStyleSheet("color: gray;")

        self.top_bar.addWidget(self.env_label)
        self.top_bar.addWidget(self.env_selector)
        self.top_bar.addWidget(self.manage_env_btn)
        self.top_bar.addWidget(self.mcp_status_label)
        self.top_bar.addStretch()
        self.top_bar.addWidget(self.settings_btn)

        self.main_layout.addLayout(self.top_bar)

        # Main Content (Splitter)
        self.splitter = QSplitter(Qt.Horizontal)

        # Left Sidebar (Collections)
        self.collections_view = QTreeView()
        self.collections_view.setHeaderHidden(True)
        self.collections_model = QStandardItemModel()
        self.collections_view.setModel(self.collections_model)
        self.collections_view.clicked.connect(self.on_collection_clicked)
        self.collections_view.expanded.connect(self.on_tree_expanded)
        self.collections_view.collapsed.connect(self.on_tree_collapsed)
        self.splitter.addWidget(self.collections_view)

        # Right Content (Request Tabs)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.splitter.addWidget(self.tabs)

        self.splitter.setSizes([300, 900])
        self.main_layout.addWidget(self.splitter)
        
        # Apply settings BEFORE loading tabs to ensure correct font size/style
        self.apply_settings(self.settings)

        # Load data
        self.load_collections()
        self.load_environments()

        # Restore open tabs
        self.restore_tabs()

        # Restore tree state
        self.restore_tree_state()

        # Setup keyboard shortcuts
        self._setup_shortcuts()

    def _create_menu_bar(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("File")
        
        quit_action = file_menu.addAction("Quit")
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.handle_exit)

        # Help Menu
        help_menu = menubar.addMenu("Help")

        hotkeys_action = help_menu.addAction("Hotkeys")
        hotkeys_action.triggered.connect(self.handle_show_hotkeys)

        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.handle_show_about)

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

        # Also trigger on_env_changed logic manually to start server if needed on startup
        if selected_index > 0:
             self.on_env_changed(selected_index)

    def on_env_changed(self, index):
        selected_env = self.env_selector.itemData(index)
        variables = {}
        if isinstance(selected_env, Environment):
            self.settings.last_environment_id = selected_env.id
            variables = selected_env.variables
            
            # Manage MCP Server
            if selected_env.enable_mcp:
                # Collect all requests that are exposed as tools
                tools = []
                for col in self.collections:
                    for req in col.requests:
                        if req.expose_as_mcp:
                            tools.append(req)
                self.mcp_manager.start_server(
                    port=self.settings.mcp_port, 
                    tools=tools,
                    host=self.settings.mcp_host
                )
            else:
                self.mcp_manager.stop_server()
        else:
            self.settings.last_environment_id = None
            self.mcp_manager.stop_server()
        
        self.config_manager.save_config(self.settings)

        # Update all open tabs with new variables
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if isinstance(tab, RequestTab):
                if hasattr(tab.request_editor, 'set_variables'):
                    tab.request_editor.set_variables(variables)
                if hasattr(tab.response_view, 'set_env_keys'):
                    keys = list(variables.keys()) if isinstance(selected_env, Environment) else None
                    tab.response_view.set_env_keys(keys)

    def on_mcp_status_changed(self, is_running: bool):
        if is_running:
            self.mcp_status_label.setText(f"MCP: ON ({self.settings.mcp_host}:{self.settings.mcp_port})")
            self.mcp_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.mcp_status_label.setText("MCP: OFF")
            self.mcp_status_label.setStyleSheet("color: gray;")

    def save_tabs_state(self):
        open_tabs_ids = []
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if isinstance(tab, RequestTab) and tab.request_data and tab.request_data.id:
                open_tabs_ids.append(tab.request_data.id)
        
        self.settings.open_tabs = open_tabs_ids
        self.config_manager.save_config(self.settings)

    def open_env_manager(self):
        current_env_name = self.env_selector.currentText()
        if self.env_selector.currentIndex() == 0: 
             current_env_name = None

        dialog = EnvironmentDialog(self.environments, self, current_env_name)
        dialog.exec()
        self.storage.save_environments(self.environments)
        self.load_environments() 
        
        # Force update of current environment to apply changes (e.g. MCP toggle)
        self.on_env_changed(self.env_selector.currentIndex())

    def open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            new_settings = dialog.get_settings()
            if new_settings:
                # Check if metrics settings changed
                metrics_changed = (self.settings.metrics_host != new_settings.metrics_host or 
                                   self.settings.metrics_port != new_settings.metrics_port)

                self.settings = new_settings
                self.config_manager.save_config(self.settings)
                self.apply_settings(self.settings)
                
                # Restart metrics server if needed
                if metrics_changed:
                    MetricsManager().restart_server(self.settings.metrics_host, self.settings.metrics_port)
                
                # Force update to apply port changes if needed
                self.on_env_changed(self.env_selector.currentIndex())

    def apply_settings(self, settings):
        app = QApplication.instance()
        if app:
            font = app.font()
            font.setPointSize(settings.font_size)
            app.setFont(font)
            
            self.style_manager.apply_styles(app)
            
            self.collections_view.setFont(font)
            self.env_selector.setFont(font)
            self.tabs.setFont(font)
            
            if self.menuBar():
                self.menuBar().setFont(font)
            
            self.manage_env_btn.setFont(font)
            self.settings_btn.setFont(font)
            self.env_label.setFont(font)
            self.tabs.tabBar().setFont(font)

        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if isinstance(tab, RequestTab):
                if hasattr(tab.request_editor, 'body_edit'):
                    tab.request_editor.body_edit.update_indent_size(settings.indent_size)
                    tab.request_editor.body_edit.reformat_text()
                
                if hasattr(tab.response_view, 'set_indent_size'):
                    tab.response_view.set_indent_size(settings.indent_size)

    def add_new_tab(self, request_data: RequestData = None, save_state: bool = True):
        tab = RequestTab(request_data)
        
        if hasattr(tab.request_editor, 'body_edit'):
            tab.request_editor.body_edit.update_indent_size(self.settings.indent_size)
        if hasattr(tab.response_view, 'set_indent_size'):
            tab.response_view.set_indent_size(self.settings.indent_size)

        selected_env = self.env_selector.currentData()
        if isinstance(selected_env, Environment):
            if hasattr(tab.request_editor, 'set_variables'):
                tab.request_editor.set_variables(selected_env.variables)
            if hasattr(tab.response_view, 'set_env_keys'):
                tab.response_view.set_env_keys(list(selected_env.variables.keys()))

        tab.request_editor.send_requested.connect(self.handle_send_request)
        tab.request_editor.save_requested.connect(self.handle_save_request)
        tab.response_view.variable_set_requested.connect(self.handle_variable_set_request)

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
            for i in range(self.tabs.count()):
                tab = self.tabs.widget(i)
                if isinstance(tab, RequestTab) and tab.request_data and tab.request_data.id == data.id:
                    self.tabs.setCurrentIndex(i)
                    return

            self.add_new_tab(data)
        else:
            if self.collections_view.isExpanded(index):
                self.collections_view.collapse(index)
            else:
                self.collections_view.expand(index)

    def handle_save_request(self, request_data: RequestData):
        existing_request = None
        found_collection = None
        existing_index = -1

        for col in self.collections:
            for i, req in enumerate(col.requests):
                if req.id == request_data.id:
                    existing_request = req
                    found_collection = col
                    existing_index = i
                    break
            if existing_request:
                break
        
        if existing_request:
            if self.settings.confirm_overwrite_request:
                reply = QMessageBox.question(
                    self, 
                    "Overwrite Request?", 
                    f"This will overwrite the existing request '{existing_request.name}'. Continue?",
                    QMessageBox.Yes | QMessageBox.No, 
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            found_collection.requests[existing_index] = request_data
            self.storage.save_collection(found_collection)
            
            for i in range(self.tabs.count()):
                tab = self.tabs.widget(i)
                if isinstance(tab, RequestTab) and tab.request_data.id == request_data.id:
                    self.tabs.setTabText(i, request_data.name)
                    tab.request_data = request_data
                    break
            
            self.load_collections()
            self.restore_tree_state()
            return

        dialog = SaveRequestDialog(self.collections, self)
        if dialog.exec():
            request_data.name = dialog.request_name
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
                target_collection.requests.append(request_data)
                self.storage.save_collection(target_collection)

                if target_collection.id not in self.settings.expanded_collections:
                    self.settings.expanded_collections.append(target_collection.id)
                    self.config_manager.save_config(self.settings)

                self.load_collections()
                self.restore_tree_state()

                current_index = self.tabs.currentIndex()
                self.tabs.setTabText(current_index, request_data.name)
                
                tab = self.tabs.widget(current_index)
                if isinstance(tab, RequestTab):
                     tab.request_data = request_data

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

        # Check if already running (Stop/Cancel)
        if hasattr(sender_tab, 'worker') and sender_tab.worker and sender_tab.worker.isRunning():
            sender_tab.worker.stop()
            # Disable button immediately to prevent double clicks and show feedback
            sender_tab.request_editor.send_btn.setEnabled(False)
            sender_tab.request_editor.send_btn.setText("Stopping...")
            return

        # Start new request
        sender_tab.response_view.clear_body() # Clear previous response
        sender_tab.request_editor.send_btn.setText("Stop") # Change button to Stop

        variables = {}
        selected_env = self.env_selector.currentData()
        if isinstance(selected_env, Environment):
            variables = selected_env.variables

        worker = RequestWorker(request_data, variables=variables)
        worker.finished.connect(lambda resp: self.on_request_finished(sender_tab, resp))
        worker.error.connect(lambda err: self.on_request_error(sender_tab, err))
        worker.env_update.connect(lambda vars: self.on_env_update(vars))
        worker.script_output.connect(lambda logs, err: self.on_script_output(sender_tab, logs, err))
        worker.chunk_received.connect(lambda chunk: self.on_chunk_received(sender_tab, chunk)) # Connect chunk signal
        worker.headers_received.connect(lambda status, headers: self.on_headers_received(sender_tab, status, headers))
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        worker.start()

        sender_tab.worker = worker

    def on_headers_received(self, tab: RequestTab, status: int, headers: dict):
        tab.response_view.status_label.setText(f"Status: {status}")
        # We can also update time label if we track start time, but for now Status is key.
        # Size will update with chunks.
    
    def on_chunk_received(self, tab: RequestTab, chunk: str):
        tab.response_view.append_body(chunk)
        # Update metrics (size) in real-time if needed
        # Since we don't have full response object here, we can just estimate size
        current_text = tab.response_view.body_view.toPlainText()
        size_bytes = len(current_text.encode('utf-8'))
        tab.response_view.size_label.setText(f"Size: {size_bytes} bytes")
        # Estimate Status from first chunk? No, status is header. 
        # Ideally, we should receive headers first then chunks.
        # But RequestWorker only emits finished with full response.
        # We need to signal headers separately if we want real-time status.
        # For now, Status remains "-" until finished.

    def on_request_finished(self, tab: RequestTab, response):
        tab.response_view.display_response(response)
        tab.request_editor.send_btn.setEnabled(True)
        tab.request_editor.send_btn.setText("Send")
        
        # Ensure status label is updated one last time
        tab.response_view.status_label.setText(f"Status: {response.status_code}")
        tab.response_view.time_label.setText(f"Time: {response.elapsed_time:.3f}s")
        tab.response_view.size_label.setText(f"Size: {response.size} bytes")

    def on_request_error(self, tab: RequestTab, error_msg):
        # Check if error is due to cancellation (not ideal check, but works for now)
        # If we manually stopped, we might want to just reset button.
        # But for now, just show error if it's actual error.
        # If it's just "stopped", we might want to be silent or say "Cancelled".
        
        # Reset button state
        tab.request_editor.send_btn.setEnabled(True)
        tab.request_editor.send_btn.setText("Send")

        if "cancelled" in error_msg.lower() or "aborted" in error_msg.lower():
             return

        QMessageBox.critical(self, "Error", f"Request failed: {error_msg}")

    def handle_variable_set_request(self, key, value):
        selected_env = self.env_selector.currentData()
        if not isinstance(selected_env, Environment):
            QMessageBox.warning(self, "No Environment", "Please select an environment to set variables.")
            return

        target_key = key
        
        # New Variable Case
        if target_key is None:
            text, ok = QInputDialog.getText(self, "New Variable", "Enter variable name:")
            if ok and text:
                target_key = text.strip()
                if not target_key:
                    QMessageBox.warning(self, "Invalid Name", "Variable name cannot be empty.")
                    return
            else:
                return

        # Update Variable
        selected_env.variables[target_key] = value
        self.storage.save_environments(self.environments)
        
        # Refresh UI
        self.on_env_changed(self.env_selector.currentIndex())

    def _setup_shortcuts(self):
        """Initializes all global shortcuts."""
        # Exit application (Ctrl+Q) is now handled via QAction in menu
        
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
        script_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        script_shortcut.activated.connect(self.handle_switch_to_script_global)

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

    def handle_switch_to_script_global(self):
        """Global handler for switching to Script tab (Ctrl+T)."""
        current_tab = self.tabs.currentWidget()
        if isinstance(current_tab, RequestTab):
            current_tab.request_editor.detail_tabs.setCurrentIndex(3)

    def handle_show_hotkeys(self):
        """Show hotkeys dialog."""
        dialog = HotkeysDialog(self)
        dialog.exec()

    def handle_show_about(self):
        """Show about dialog."""
        dialog = AboutDialog(self)
        dialog.exec()

    def on_tree_expanded(self, index):
        """Handle tree item expansion."""
        item = self.collections_model.itemFromIndex(index)
        data = item.data(Qt.UserRole)
        # Check if it is a collection ID (string) and not a RequestData object
        if isinstance(data, str): 
            if data not in self.settings.expanded_collections:
                self.settings.expanded_collections.append(data)
                self.config_manager.save_config(self.settings)

    def on_tree_collapsed(self, index):
        """Handle tree item collapse."""
        item = self.collections_model.itemFromIndex(index)
        data = item.data(Qt.UserRole)
        if isinstance(data, str):
            if data in self.settings.expanded_collections:
                self.settings.expanded_collections.remove(data)
                self.config_manager.save_config(self.settings)

    def restore_tree_state(self):
        """Restore expanded state of collections."""
        root = self.collections_model.invisibleRootItem()
        for row in range(root.rowCount()):
            item = root.child(row)
            data = item.data(Qt.UserRole)
            if isinstance(data, str) and data in self.settings.expanded_collections:
                self.collections_view.setExpanded(item.index(), True)

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QComboBox, QLabel, QSplitter, QTreeView, QTabWidget, QMessageBox,
                               QPushButton, QApplication)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QFont
from PySide6.QtCore import Qt
from pypost.ui.widgets.request_editor import RequestWidget
from pypost.ui.widgets.response_view import ResponseView
from pypost.core.worker import RequestWorker
from pypost.models.models import RequestData, Collection, Environment
from pypost.core.storage import StorageManager
from pypost.core.config_manager import ConfigManager
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
        self.collections_view.doubleClicked.connect(self.on_collection_double_click)
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

            for req in col.requests:
                req_item = QStandardItem(f"{req.method} {req.name}")
                req_item.setData(req, Qt.UserRole) # Store RequestData object
                req_item.setEditable(False)
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

    def on_collection_double_click(self, index):
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
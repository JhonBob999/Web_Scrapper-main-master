from PyQt5.QtCore import Qt, QTimer
from core.bot_core.bot_manager import BotManager

from ui.bot_panel.bot_creation_handler import handle_start_bot, handle_delete_bot
from ui.bot_panel.bot_launch_handler import handle_launch_selected_bot, stop_bot
from ui.bot_panel.bot_config_handler import handle_configure_bot, handle_item_edited
from ui.bot_panel.bot_log_handler import (
    handle_pause_logs, handle_resume_logs, update_bot_logs,
    handle_log_checkbox_changed, handle_log_search,
    load_log_options, save_log_options
)
from ui.bot_panel.bot_context_menu_handler import handle_context_menu
from ui.bot_panel.bot_profile_handler import handle_apply_config
from ui.bot_panel.bot_js_handler import analyze_js_from_bot, send_to_js_analyzer
from ui.bot_panel.bot_table_utils import get_selected_bot_id, handle_load_bot


class BotPanelController:
    def __init__(self, ui, parent=None, xss_controller=None):
        self.ui = ui
        self.parent = parent
        self.xss_controller = xss_controller
        self.bot_manager = BotManager()

        self.log_timer = QTimer()
        self.log_timer.setInterval(2000)
        self.log_timer.timeout.connect(lambda: update_bot_logs(self.ui, self.current_log_path))
        self.current_log_path = None

        self._setup_connections()

    def _setup_connections(self):
        self.ui.btn_startBot.clicked.connect(self._handle_start_bot)
        self.ui.btn_launchBot.clicked.connect(self._handle_launch_selected_bot)
        self.ui.btn_stopBot.clicked.connect(self.on_btn_stopBot_clicked)
        self.ui.btn_configureBot.clicked.connect(self._handle_configure_bot)
        self.ui.btn_loadBot.clicked.connect(self.on_btn_loadBot_clicked)
        self.ui.btn_applyConfig.clicked.connect(self.on_btn_applyConfig_clicked)
        self.ui.btn_deleteBot.clicked.connect(self._handle_delete_bot)
        self.ui.btn_pauseLogs.clicked.connect(self._handle_pause_logs)
        self.ui.btn_resumeLogs.clicked.connect(self._handle_resume_logs)
        # Привязка кнопки загрузки дерева
        self.ui.btn_reloadCrawlTree.clicked.connect(self.reload_crawler_tree)
        # Привязка поиска
        self.ui.line_searchCrawlerTree.textChanged.connect(self.search_crawler_tree)
        self.ui.btn_clearFilter.clicked.connect(self.clear_crawler_tree_filter)

        #CONTEXT MENU FOR BOT_WIDGET
        self.ui.bot_Widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.bot_Widget.customContextMenuRequested.connect(self._handle_context_menu)
        self.ui.bot_Widget.itemChanged.connect(self._handle_item_edited)
        #PLAINTEXT LOGS BUTTONS
        self.ui.btn_saveLogs.clicked.connect(self._on_save_log_options)
        self.ui.btn_loadLogs.clicked.connect(self._handle_load_logs)
        #ComboBox logs
        self.ui.chkLogRequests.stateChanged.connect(self._handle_log_checkbox_changed)
        self.ui.chkLogResponses.stateChanged.connect(self._handle_log_checkbox_changed)
        self.ui.chkLogConsole.stateChanged.connect(self._handle_log_checkbox_changed)
        self.ui.chkLogDockerEvents.stateChanged.connect(self._handle_log_checkbox_changed)
        #QLineEdit search Logs
        self.ui.line_searchLogs.textChanged.connect(self._handle_log_search)

    # === Button handlers ===
    def _handle_load_logs(self):
        bot_id = get_selected_bot_id(self.ui)
        if bot_id:
            from ui.bot_panel.bot_log_handler import handle_load_log_interface
            handle_load_log_interface(self.ui, bot_id, self._start_log_monitoring)

    def _start_log_monitoring(self, bot_id: str):
        self.current_log_path = f"data/bots/{bot_id}/logs.txt"
        self.log_timer.start()

    def _handle_start_bot(self):
        handle_start_bot(self.ui, self.parent)

    def _handle_launch_selected_bot(self):
        handle_launch_selected_bot(self.ui, self.parent)

    def on_btn_stopBot_clicked(self):
        stop_bot(self.ui, self.parent)

    def _handle_configure_bot(self):
        handle_configure_bot(self.ui, self.parent)

    def _handle_delete_bot(self):
        handle_delete_bot(self.ui, self.parent)

    def on_btn_loadBot_clicked(self):
        handle_load_bot(self.ui, self.parent)

    def on_btn_applyConfig_clicked(self):
        handle_apply_config(self.ui, self.parent)

    def _handle_pause_logs(self):
        handle_pause_logs(self.log_timer)

    def _handle_resume_logs(self):
        handle_resume_logs(self.log_timer, self.current_log_path, self.parent)

    def _handle_log_checkbox_changed(self):
        handle_log_checkbox_changed(self.ui, lambda: get_selected_bot_id(self.ui))

    def _handle_log_search(self, text):
        handle_log_search(self.ui, self.current_log_path, text)

    def _on_save_log_options(self):
        bot_id = get_selected_bot_id(self.ui)
        if bot_id:
            save_log_options(self.ui, bot_id)

    # === Table / Context ===
    def _handle_context_menu(self, position):
        handle_context_menu(self.parent, self.ui, self.xss_controller, position)

    def _handle_item_edited(self, item, column):
        handle_item_edited(item)

    # === Crawl Tree ===
    def reload_crawler_tree(self):
        from core.crawler_view_loader import load_crawl_result
        bot_id = get_selected_bot_id(self.ui)
        if not bot_id:
            return
        load_crawl_result(bot_id, self.ui.crawler_treeWidget)

    def search_crawler_tree(self):
        from core.crawler_view_loader import search_in_tree
        search_in_tree(self.ui.crawler_treeWidget, self.ui.line_searchCrawlerTree.text())

    def clear_crawler_tree_filter(self):
        from core.crawler_view_loader import clear_filter
        self.ui.line_searchCrawlerTree.clear()
        clear_filter(self.ui.crawler_treeWidget)

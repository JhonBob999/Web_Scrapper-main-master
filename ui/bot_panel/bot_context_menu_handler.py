from ui.bot_panel.bot_creation_handler import save_bot_status
from ui.bot_panel.bot_launch_handler import launch_bot, stop_bot
from ui.bot_panel.bot_config_handler import configure_bot, rename_bot
from ui.bot_panel.bot_profile_handler import save_bot_profile, load_bot_profile
from ui.bot_panel.bot_js_handler import send_to_js_analyzer, analyze_js_from_bot
from dialogs.bot_logs_dialog import BotLogsDialog
from PyQt5.QtWidgets import QMessageBox
from ui.bot_panel.bot_panelContextMenu import open_bot_context_menu
import os


def handle_context_menu(parent, ui, xss_controller, position):
    def launch(item):
        launch_bot(item)

    def stop(item):
        stop_bot(ui, parent)

    def configure(item):
        configure_bot(item, parent)

    def rename(item):
        rename_bot(item, parent)

    def save_profile(item):
        save_bot_profile(item, parent)

    def load_profile(item):
        load_bot_profile(item, parent)

    def send_to_js(item):
        send_to_js_analyzer(item, xss_controller, ui.bot_Widget)

    def analyze_js(item):
        analyze_js_from_bot(item, ui.bot_Widget)

    def view_logs(item):
        bot_id = item.text(1)
        log_path = f"data/bots/{bot_id}/logs.txt"

        if not os.path.exists(log_path):
            QMessageBox.warning(parent, "No Logs", f"No logs found for bot: {bot_id}")
            return

        dialog = BotLogsDialog(bot_id, log_path, parent=parent)
        dialog.exec_()

    callbacks = {
        "launch": launch,
        "stop": stop,
        "configure": configure,
        "save_profile": save_profile,
        "load_profile": load_profile,
        "rename": rename,
        "send_to_js": send_to_js,
        "analyze_js": analyze_js,
        "view_logs": view_logs
    }

    open_bot_context_menu(parent, ui.bot_Widget, position, callbacks)

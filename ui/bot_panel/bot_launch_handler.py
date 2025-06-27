import os
import json
from PyQt5.QtWidgets import QMessageBox
from core.bot_core.bot_manager import BotManager

bot_manager = BotManager()

def handle_launch_selected_bot(ui, parent):
    selected_items = ui.bot_Widget.selectedItems()
    if not selected_items:
        QMessageBox.warning(parent, "No Selection", "Please select a bot to launch.")
        return

    for item in selected_items:
        launch_bot(item)


def launch_bot(item):
    bot_id = item.text(1)
    config_path = os.path.join("data", "bots", bot_id, "config.json")
    if not os.path.exists(config_path):
        QMessageBox.warning(None, "Missing Config", f"No config found for bot: {bot_id}")
        return

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to load config:\n{str(e)}")
        return

    bot_type = config.get("bot_type", bot_id.split("_")[0])
    bot_manager.start_existing_bot(bot_id, bot_type, config)
    item.setText(3, "Running")


def stop_bot(ui, parent):
    selected_item = ui.bot_Widget.currentItem()
    if not selected_item:
        QMessageBox.warning(parent, "No Selection", "Please select a bot to stop.")
        return

    bot_id = selected_item.text(1)
    try:
        bot_manager.stop_bot(bot_id)
        QMessageBox.information(parent, "Success", f"Bot '{bot_id}' has been stopped.")
        selected_item.setText(3, "Stopped")
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"Failed to stop bot '{bot_id}':\n{str(e)}")

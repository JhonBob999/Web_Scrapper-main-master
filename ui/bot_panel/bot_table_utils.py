import os
import json
from datetime import datetime
from PyQt5.QtWidgets import QTreeWidgetItem, QMessageBox
from PyQt5.QtCore import Qt
from dialogs.load_bots_dialog.load_bots_dialog import LoadBotsDialog


def get_selected_bot_id(ui):
    item = ui.bot_Widget.currentItem()
    if item:
        return item.text(1)  # Колонка с Bot ID
    return None


def handle_load_bot(ui, parent):
    dialog = LoadBotsDialog(parent=parent)
    if dialog.exec_() == dialog.Accepted:
        bot_ids = dialog.get_selected_bots()

        for bot_id in bot_ids:
            status_path = f"data/bots/{bot_id}/status.json"
            config_path = f"data/bots/{bot_id}/config.json"

            bot_type = bot_id.split("_")[0]  # fallback
            status = "Ready"
            alias = "Loaded Bot"
            domain = ""
            profile = "default"
            created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            comment = ""

            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                        domain = config_data.get("target", "")
                        profile = config_data.get("profile_name", "default")
                except Exception as e:
                    print(f"[ERROR] Failed to read config: {e}")

            if os.path.exists(status_path):
                try:
                    with open(status_path, "r", encoding="utf-8") as f:
                        status_data = json.load(f)
                        status = status_data.get("status", "Ready")
                        comment = status_data.get("comment", "")
                        created = status_data.get("created", created)
                        alias = status_data.get("alias", alias)
                except Exception as e:
                    print(f"[ERROR] Failed to read status: {e}")

            item = QTreeWidgetItem([
                bot_type, bot_id, alias, status, domain, profile, created, comment
            ])
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            ui.bot_Widget.addTopLevelItem(item)

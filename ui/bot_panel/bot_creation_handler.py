import os
import json
import shutil
from datetime import datetime
from PyQt5.QtWidgets import QDialog, QMessageBox, QTreeWidgetItem
from PyQt5.QtCore import Qt
from dialogs.create_bot_dialog.create_bot_dialog import CreateBotDialog


def handle_start_bot(ui, parent):
    print("[DEBUG] Start Bot button clicked.")
    dialog = CreateBotDialog(parent)
    if dialog.exec_() == QDialog.Accepted:
        bot_data = dialog.get_bot_data()
        bot_type = bot_data["bot_type"]
        bot_id = bot_data["bot_id"]
        alias = bot_data["alias"]

        print(f"[DEBUG] Creating bot: {bot_id} (type: {bot_type}, alias: {alias})")
        create_bot_entry(ui, bot_id, bot_type, alias)


def create_bot_entry(ui, bot_id: str, bot_type: str, alias: str):
    bot_folder = os.path.join("data", "bots", bot_id)
    os.makedirs(bot_folder, exist_ok=True)

    config = {
        "bot_type": bot_type,
        "target": "",
        "depth": 1,
        "profile_name": "default",
        "headless": True
    }

    config_path = os.path.join(bot_folder, "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    open(os.path.join(bot_folder, "logs.txt"), "a").close()
    os.makedirs(os.path.join(bot_folder, "extra_data"), exist_ok=True)

    entrypoint_src = os.path.join("bots", bot_type, "entrypoint.py")
    entrypoint_dst = os.path.join(bot_folder, "entrypoint.py")
    try:
        shutil.copy(entrypoint_src, entrypoint_dst)
        print(f"[INFO] Copied entrypoint from {entrypoint_src} to {entrypoint_dst}")
    except Exception as e:
        print(f"[ERROR] Failed to copy entrypoint.py: {e}")

    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "Ready"
    domain = config["target"]
    profile = config["profile_name"]
    comment = ""

    item = QTreeWidgetItem([
        bot_type, bot_id, alias, status, domain, profile, created, comment
    ])
    item.setFlags(item.flags() | Qt.ItemIsEditable)

    ui.bot_Widget.addTopLevelItem(item)

    save_bot_status(bot_id, status, domain, comment, created)
    print(f"[INFO] Bot '{bot_id}' created and added to table.")
    
    
def handle_delete_bot(ui, parent):
    selected_item = ui.bot_Widget.currentItem()
    if not selected_item:
        QMessageBox.warning(parent, "No Selection", "Please select a bot to delete.")
        return

    bot_id = selected_item.text(1)

    confirm = QMessageBox.question(
        parent,
        "Confirm Deletion",
        f"Are you sure you want to delete bot '{bot_id}'?\nThis will stop the bot and remove all its data.",
        QMessageBox.Yes | QMessageBox.No
    )

    if confirm != QMessageBox.Yes:
        return

    try:
        # Остановить Docker (если работает)
        from core.bot_core.bot_manager import BotManager
        BotManager().stop_bot(bot_id)

        # Удалить папку бота
        bot_path = os.path.join("data", "bots", bot_id)
        shutil.rmtree(bot_path, ignore_errors=True)

        # Удалить строку из таблицы
        index = ui.bot_Widget.indexOfTopLevelItem(selected_item)
        ui.bot_Widget.takeTopLevelItem(index)

        QMessageBox.information(parent, "Bot Deleted", f"Bot '{bot_id}' was deleted successfully.")
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"Failed to delete bot '{bot_id}':\n{e}")



def save_bot_status(bot_id: str, status: str, domain: str, comment: str, created: str):
    status_path = os.path.join("data", "bots", bot_id, "status.json")
    status_data = {
        "status": status,
        "target": domain,
        "comment": comment,
        "created": created
    }
    try:
        with open(status_path, "w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=4)
    except Exception as e:
        print(f"[ERROR] Failed to save status.json: {e}")

import os
import json
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QTreeWidgetItem
from dialogs.bot_config_dialogs.bot_config_dialog import BotConfigDialog
from dialogs.crawler_config_dialog.crawler_config_dialog import CrawlerConfigDialog


def handle_configure_bot(ui, parent):
    selected_item = ui.bot_Widget.currentItem()
    if not selected_item:
        QMessageBox.warning(parent, "No Selection", "Please select a bot.")
        return

    bot_id = selected_item.text(1)
    bot_type = selected_item.text(0)

    # Select proper config dialog
    if bot_type == "xss-bot":
        dialog = BotConfigDialog(bot_id=bot_id, parent=parent)
    elif bot_type == "crawler-bot":
        dialog = CrawlerConfigDialog(bot_id=bot_id, parent=parent)
    else:
        QMessageBox.warning(parent, "Unsupported", f"No config dialog available for: {bot_type}")
        return

    if dialog.exec_() == dialog.Accepted:
        _refresh_ui_columns_from_config(selected_item, bot_id)


def configure_bot(item: QTreeWidgetItem, parent):
    bot_id = item.text(1)
    bot_type = item.text(0)

    if bot_type == "xss-bot":
        dialog = BotConfigDialog(bot_id=bot_id, parent=parent)
    elif bot_type == "crawler-bot":
        dialog = CrawlerConfigDialog(bot_id=bot_id, parent=parent)
    else:
        QMessageBox.warning(parent, "Unsupported", f"No config dialog available for: {bot_type}")
        return

    if dialog.exec_() == dialog.Accepted:
        _refresh_ui_columns_from_config(item, bot_id)



def _refresh_ui_columns_from_config(item: QTreeWidgetItem, bot_id: str):
    config_path = os.path.join("data", "bots", bot_id, "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            domain = config.get("target", "")
            if domain:
                item.setText(4, domain)

            profile = config.get("profile_name", "")
            if profile:
                item.setText(5, profile)

        except Exception as e:
            print(f"[ERROR] Failed to refresh UI after config update: {e}")


def handle_item_edited(item: QTreeWidgetItem):
    # Only trigger on comment column
    COMMENT_COLUMN = 7
    if item.columnCount() <= COMMENT_COLUMN:
        return
    bot_id = item.text(1)
    status = item.text(3)
    domain = item.text(4)
    comment = item.text(7)
    created = item.text(6)

    _save_bot_status(bot_id, status, domain, comment, created)


def rename_bot(item: QTreeWidgetItem, parent):
    bot_id = item.text(1)
    current_name = item.text(2)

    new_name, ok = QInputDialog.getText(parent, "Rename Bot", "Enter new bot name:", text=current_name)
    if not ok or not new_name.strip():
        return

    new_name = new_name.strip()
    item.setText(2, new_name)

    status_path = f"data/bots/{bot_id}/status.json"
    if os.path.exists(status_path):
        try:
            with open(status_path, "r", encoding="utf-8") as f:
                status_data = json.load(f)
        except Exception:
            status_data = {}

        status_data["alias"] = new_name
        try:
            with open(status_path, "w", encoding="utf-8") as f:
                json.dump(status_data, f, indent=4)
        except Exception as e:
            print(f"[ERROR] Cannot save new alias: {e}")


def _save_bot_status(bot_id: str, status: str, domain: str, comment: str, created: str):
    status_path = f"data/bots/{bot_id}/status.json"
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

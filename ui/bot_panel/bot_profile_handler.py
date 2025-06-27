import os
import json
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from dialogs.apply_config_dialog.apply_config_dialog import ApplyConfigDialog
from dialogs.bot_config_dialogs.bot_config_dialog import BotConfigDialog


def handle_apply_config(ui, parent):
    dialog = ApplyConfigDialog(parent=parent)
    if dialog.exec_() == dialog.Accepted:
        profile_path = dialog.get_selected_profile_path()
        if not profile_path:
            return

        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            QMessageBox.warning(parent, "Error", f"Failed to load profile:\n{str(e)}")
            return

        for item in ui.bot_Widget.selectedItems():
            bot_id = item.text(1)
            config_path = os.path.join("data", "bots", bot_id, "config.json")

            try:
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
            except Exception as e:
                QMessageBox.warning(parent, "Error", f"Failed to apply config to {bot_id}:\n{str(e)}")
                continue

            # Обновляем UI
            domain = config.get("target", "")
            if domain:
                item.setText(4, domain)

            profile_name = config.get("profile_name", "")
            if profile_name:
                item.setText(5, profile_name)


def save_bot_profile(item, parent):
    bot_id = item.text(1)
    dialog = BotConfigDialog(bot_id=bot_id, parent=parent)
    dialog.save_as_profile()


def load_bot_profile(item, parent):
    bot_id = item.text(1)

    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        "Load Profile",
        "assets/bot_profiles/",
        "JSON Files (*.json)"
    )

    if not file_path:
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"Failed to load profile:\n{str(e)}")
        return

    bot_config_path = os.path.join("data", "bots", bot_id, "config.json")
    os.makedirs(os.path.dirname(bot_config_path), exist_ok=True)

    try:
        with open(bot_config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        QMessageBox.information(parent, "Success", f"Profile applied to bot:\n{bot_id}")
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"Failed to apply config:\n{str(e)}")

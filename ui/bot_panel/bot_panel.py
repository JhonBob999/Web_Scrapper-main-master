from PyQt5.QtWidgets import QMessageBox, QTreeWidgetItem, QDialog
from core.bot_core.bot_manager import BotManager
from dialogs.bot_config_dialogs.bot_config_dialog import BotConfigDialog
from dialogs.load_bots_dialog.load_bots_dialog import LoadBotsDialog
from dialogs.apply_config_dialog.apply_config_dialog import ApplyConfigDialog
import json
import os

class BotPanelController:
    def __init__(self, ui, parent=None):
        self.ui = ui  # ссылка на ui из Qt Designer
        self.parent = parent  # ✅ Сохраняем родителя
        self.bot_manager = BotManager()  # ✅ создаём объект
        self._setup_connections()

    def _setup_connections(self):
        self.ui.btn_startBot.clicked.connect(self._handle_start_bot)
        self.ui.btn_stopBot.clicked.connect(self.on_btn_stopBot_clicked)
        self.ui.btn_configureBot.clicked.connect(self._handle_configure_bot)
        self.ui.btn_loadBot.clicked.connect(self.on_btn_loadBot_clicked)
        self.ui.btn_applyConfig.clicked.connect(self.on_btn_applyConfig_clicked)

    def _handle_start_bot(self):
        print("[DEBUG] Start Bot button clicked.")
        bot_type = "xss-bot"  # пока что вручную, потом из GUI
        config = {
            "target": "http://localhost:8080/test3.html",
            "param": "q",
            "headless": True
        }

        bot_id = self.bot_manager.start_bot(bot_type, config)
        if bot_id:
            print(f"[GUI] Bot {bot_id} successfully launched.")
            item = QTreeWidgetItem([bot_id, "Running"])
            self.ui.bot_Widget.addTopLevelItem(item)
        else:
            print("[GUI] Failed to start bot.")
            
    def on_btn_stopBot_clicked(self):
        selected_item = self.ui.bot_Widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self.parent, "No Selection", "Please select a bot to stop.")
            return

        bot_id = selected_item.text(0)
        try:
            self.bot_manager.stop_bot(bot_id)
            QMessageBox.information(self.parent, "Success", f"Bot '{bot_id}' has been stopped.")

            # ✅ Обновляем статус во второй колонке
            selected_item.setText(1, "Stopped")

        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Failed to stop bot '{bot_id}':\n{str(e)}")
            
    def _handle_configure_bot(self):
        selected_item = self.ui.bot_Widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self.parent, "No Selection", "Please select a bot.")
            return

        bot_id = selected_item.text(0)
        dialog = BotConfigDialog(bot_id=bot_id, parent=self.parent)
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.get_config()
            if config:
                with open(f"data/bots/{bot_id}/config.json", "w") as f:
                    json.dump(config, f, indent=4)
                    
                    
    def on_btn_loadBot_clicked(self):
        dialog = LoadBotsDialog(parent=self.parent)
        if dialog.exec_() == QDialog.Accepted:
            bot_ids = dialog.get_selected_bots()
            for bot_id in bot_ids:
                item = QTreeWidgetItem([bot_id, "Ready"])
                self.ui.bot_Widget.addTopLevelItem(item)
                
                
    def on_btn_applyConfig_clicked(self):
        dialog = ApplyConfigDialog(parent=self.parent)
        if dialog.exec_() == QDialog.Accepted:
            profile_path = dialog.get_selected_profile_path()
            if not profile_path:
                return

            try:
                with open(profile_path, "r") as f:
                    config = json.load(f)
            except Exception as e:
                QMessageBox.warning(self.parent, "Error", f"Failed to load profile:\n{str(e)}")
                return

            # Применяем конфиг ко всем выделенным ботам
            for item in self.ui.bot_Widget.selectedItems():
                bot_id = item.text(0)
                config_path = os.path.join("data", "bots", bot_id, "config.json")
                try:
                    with open(config_path, "w") as f:
                        json.dump(config, f, indent=4)
                except Exception as e:
                    QMessageBox.warning(self.parent, "Error", f"Failed to apply config to {bot_id}:\n{str(e)}")





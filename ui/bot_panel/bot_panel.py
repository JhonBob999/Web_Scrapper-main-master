from PyQt5.QtWidgets import QMessageBox, QTreeWidgetItem, QDialog, QFileDialog, QLineEdit
from PyQt5.QtCore import Qt
from core.bot_core.bot_manager import BotManager
from dialogs.bot_config_dialogs.bot_config_dialog import BotConfigDialog
from dialogs.load_bots_dialog.load_bots_dialog import LoadBotsDialog
from dialogs.apply_config_dialog.apply_config_dialog import ApplyConfigDialog
from ui.bot_panel.bot_panelContextMenu import open_bot_context_menu
from datetime import datetime
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
        self.ui.btn_launchBot.clicked.connect(self._handle_launch_selected_bot)
        self.ui.btn_stopBot.clicked.connect(self.on_btn_stopBot_clicked)
        self.ui.btn_configureBot.clicked.connect(self._handle_configure_bot)
        self.ui.btn_loadBot.clicked.connect(self.on_btn_loadBot_clicked)
        self.ui.btn_applyConfig.clicked.connect(self.on_btn_applyConfig_clicked)
        #CONTEXT MENU FOR BOT_WIDGET
        self.ui.bot_Widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.bot_Widget.customContextMenuRequested.connect(self._handle_context_menu)
        self.ui.bot_Widget.itemChanged.connect(self._handle_item_edited)

    def _handle_start_bot(self):
        print("[DEBUG] Start Bot button clicked.")
        bot_type = "xss-bot"
        config = {
            "target": "http://localhost:8080/test3.html",
            "param": "q",
            "headless": True,
            "profile_name": "default"
        }

        bot_id = self.bot_manager.start_bot(bot_type, config)
        if bot_id:
            print(f"[GUI] Bot {bot_id} successfully launched.")
            
            alias = "New Bot"  # пока дефолт, потом сделаем окно
            status = "Running"
            domain = config.get("target", "")
            profile = config.get("profile_name", "default")
            created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            comment = ""

            item = QTreeWidgetItem([
                bot_type, bot_id, alias, status, domain, profile, created, comment
            ])
            item.setFlags(item.flags() | Qt.ItemIsEditable)

            self.ui.bot_Widget.addTopLevelItem(item)

            # сохраняем статус
            self.save_bot_status(bot_id, status, domain, comment, created)

        else:
            print("[GUI] Failed to start bot.")
            
    def _handle_launch_selected_bot(self):
        selected_items = self.ui.bot_Widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self.parent, "No Selection", "Please select a bot to launch.")
            return

        for item in selected_items:
            self.launch_bot(item)
    
    def on_btn_stopBot_clicked(self):
        selected_item = self.ui.bot_Widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self.parent, "No Selection", "Please select a bot to stop.")
            return

        bot_id = selected_item.text(1)
        try:
            self.bot_manager.stop_bot(bot_id)
            QMessageBox.information(self.parent, "Success", f"Bot '{bot_id}' has been stopped.")

            # ✅ Обновляем статус во второй колонке
            selected_item.setText(2, "Stopped")

        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Failed to stop bot '{bot_id}':\n{str(e)}")
            
    def _handle_configure_bot(self):
        selected_item = self.ui.bot_Widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self.parent, "No Selection", "Please select a bot.")
            return

        bot_id = selected_item.text(1)
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
                bot_type = bot_id.split("_")[0]
                status_path = f"data/bots/{bot_id}/status.json"
                config_path = f"data/bots/{bot_id}/config.json"
                status = "Ready"
                alias = "Loaded Bot"
                domain = ""
                profile = "default"
                created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                comment = ""

                if os.path.exists(status_path):
                    with open(status_path, "r") as f:
                        status_data = json.load(f)
                        status = status_data.get("status", "Ready")
                        domain = status_data.get("target", "")
                        comment = status_data.get("comment", "")
                        created = status_data.get("created", created)

                if os.path.exists(config_path):
                    with open(config_path, "r") as f:
                        config_data = json.load(f)
                        profile = config_data.get("profile_name", "default")

                item = QTreeWidgetItem([
                    bot_type, bot_id, alias, status, domain, profile, created, comment
                ])
                item.setFlags(item.flags() | Qt.ItemIsEditable)
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
                bot_id = item.text(1)
                config_path = os.path.join("data", "bots", bot_id, "config.json")
                try:
                    with open(config_path, "w") as f:
                        json.dump(config, f, indent=4)
                except Exception as e:
                    QMessageBox.warning(self.parent, "Error", f"Failed to apply config to {bot_id}:\n{str(e)}")
                    
    def _handle_context_menu(self, position):
        callbacks = {
            "launch": self.launch_bot,
            "stop": self.stop_bot,
            "configure": self.configure_bot,
            "save_profile": self.save_bot_profile,
            "load_profile": self.load_bot_profile,
        }
        open_bot_context_menu(self.parent, self.ui.bot_Widget, position, callbacks)
        
    def start_bot(self, item):
        bot_id = item.text(1)

        config_path = os.path.join("data", "bots", bot_id, "config.json")
        if not os.path.exists(config_path):
            QMessageBox.warning(self.parent, "Missing Config", f"No config found for bot: {bot_id}")
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Failed to load config:\n{str(e)}")
            return

        # 🧠 Вот здесь вытаскиваем bot_type из bot_id
        bot_type = bot_id.split("_")[0]  # 'xss-bot' из 'xss-bot_2025...'

        self.bot_manager.start_bot(bot_type, config)

    def stop_bot(self, item):
        bot_id = item.text(1)
        self.bot_manager.stop_bot(bot_id)
        item.setText(2, "Stopped")
        
    def configure_bot(self, item):
        bot_id = item.text(1)
        dialog = BotConfigDialog(bot_id=bot_id, parent=self.parent)
        dialog.exec_()

    def save_bot_profile(self, item):
        bot_id = item.text(1)
        dialog = BotConfigDialog(bot_id=bot_id, parent=self.parent)
        dialog.save_as_profile()

    def load_bot_profile(self, item):
        bot_id = item.text(1)

        # Выбор JSON-файла с профилем
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent,
            "Load Profile",
            "assets/bot_profiles/",
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        # Загружаем конфиг из профиля
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Failed to load profile:\n{str(e)}")
            return

        # Путь до текущего бота
        bot_config_path = os.path.join("data", "bots", bot_id, "config.json")
        os.makedirs(os.path.dirname(bot_config_path), exist_ok=True)

        try:
            with open(bot_config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            QMessageBox.information(self.parent, "Success", f"Profile applied to bot:\n{bot_id}")
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Failed to apply config:\n{str(e)}")
            
    def launch_bot(self, item):
        bot_id = item.text(1)
        bot_type = bot_id.split("_")[0]

        config_path = os.path.join("data", "bots", bot_id, "config.json")
        if not os.path.exists(config_path):
            QMessageBox.warning(self.parent, "Missing Config", f"No config found for bot: {bot_id}")
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Failed to load config:\n{str(e)}")
            return

        # 🔥 вся логика проверки происходит внутри
        self.bot_manager.start_existing_bot(bot_id, bot_type, config)

        # 💡 можешь optionally обновить статус
        item.setText(2, "Running")
        
        
        
    def save_bot_status(self, bot_id: str, status: str, domain: str, comment: str, created: str):
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
            
            
    def _handle_item_edited(self, item: QTreeWidgetItem, column: int):
        if column != 7:
            return  # Только колонка Comment

        bot_id = item.text(1)
        status = item.text(3)
        domain = item.text(4)
        comment = item.text(7)
        created = item.text(6)

        self.save_bot_status(bot_id, status, domain, comment, created)












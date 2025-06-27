from PyQt5.QtWidgets import QMessageBox, QTreeWidgetItem, QDialog, QFileDialog, QLineEdit, QInputDialog
from PyQt5.QtCore import Qt, QTimer
from core.bot_core.bot_manager import BotManager
from core.js_tree_loader import load_js_tree_from_bot
from dialogs.bot_config_dialogs.bot_config_dialog import BotConfigDialog
from dialogs.load_bots_dialog.load_bots_dialog import LoadBotsDialog
from dialogs.apply_config_dialog.apply_config_dialog import ApplyConfigDialog
from dialogs.log_viewer_dialog import LogViewerDialog
from dialogs.js_selection_dialog import JsSelectionDialog
from ui.bot_panel.bot_panelContextMenu import open_bot_context_menu
from ui.xss_controller import XssController
from datetime import datetime
import json
import os
import shutil

class BotPanelController:
    def __init__(self, ui, parent=None, xss_controller=None):
        self.ui = ui  # ссылка на ui из Qt Designer
        self.parent = parent  # ✅ Сохраняем родителя
        self.bot_manager = BotManager()  # ✅ создаём объект
        self.xss_controller = xss_controller
        self._setup_connections()

    def _setup_connections(self):
        self.ui.btn_startBot.clicked.connect(self._handle_start_bot)
        self.ui.btn_launchBot.clicked.connect(self._handle_launch_selected_bot)
        self.ui.btn_stopBot.clicked.connect(self.on_btn_stopBot_clicked)
        self.ui.btn_configureBot.clicked.connect(self._handle_configure_bot)
        self.ui.btn_loadBot.clicked.connect(self.on_btn_loadBot_clicked)
        self.ui.btn_applyConfig.clicked.connect(self.on_btn_applyConfig_clicked)
        self.ui.btn_deleteBot.clicked.connect(self._handle_delete_bot)
        #CONTEXT MENU FOR BOT_WIDGET
        self.ui.bot_Widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.bot_Widget.customContextMenuRequested.connect(self._handle_context_menu)
        self.ui.bot_Widget.itemChanged.connect(self._handle_item_edited)
        #PLAINTEXT LOGS BUTTONS
        self.ui.btn_saveLogs.clicked.connect(self._on_save_log_options)
        self.ui.btn_loadLogs.clicked.connect(self._load_log_interface)
        # Таймер для логов
        self.log_timer = QTimer()
        self.log_timer.setInterval(2000)  # 2 секунды
        self.log_timer.timeout.connect(self._update_bot_logs)
        self.current_log_path = None  # путь до logs.txt для выбранного бота


    def _load_log_interface(self):
        bot_id = self.get_selected_bot_id()
        if bot_id:
            self.load_log_options(bot_id)
            self._start_log_monitoring(bot_id)
            
            
    def _analyze_js_from_bot(self, item):


        bot_id = item.text(1)
        bot_path = os.path.join("data", "bots", bot_id)
        js_path = os.path.join(bot_path, "extra_data", "js_list.json")
        config_path = os.path.join(bot_path, "config.json")

        if not os.path.exists(js_path):
            QMessageBox.warning(self.ui.bot_Widget, "JS List Not Found", f"No js_list.json found for bot {bot_id}.")
            return

        try:
            with open(js_path, "r", encoding="utf-8") as f:
                js_data = json.load(f)
        except Exception as e:
            QMessageBox.warning(self.ui.bot_Widget, "Error", f"Failed to read js_list.json:\n{e}")
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception:
            config_data = {}

        target = config_data.get("target", "unknown.local")
        base_url = target if target.startswith("http") else f"http://{target}"

        # ✅ Универсальный парсинг
        if isinstance(js_data, list):
            domain = target.replace("http://", "").replace("https://", "").split("/")[0]
            js_urls = js_data
        elif isinstance(js_data, dict):
            domain, js_urls = next(iter(js_data.items()))
        else:
            QMessageBox.warning(self.ui.bot_Widget, "JS Format Error", "Invalid format in js_list.json")
            return

        dialog = JsSelectionDialog(domain=domain, js_urls=js_urls, base_url=base_url, parent=self.ui.bot_Widget)
        dialog.exec_()


            
            
    def _send_to_js_analyzer(self, item):
        bot_id = item.text(1)  # Предположительно bot_id в колонке 1
        bot_path = os.path.join("data", "bots", bot_id)
        
        config_path = os.path.join(bot_path, "config.json")
        js_list_path = os.path.join(bot_path, "extra_data", "js_list.json")

        if not os.path.exists(js_list_path):
            QMessageBox.warning(self, "JS List Not Found", f"No js_list.json found for bot {bot_id}.")
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Config Load Error", f"Failed to load config.json: {e}")
            return

        try:
            with open(js_list_path, "r", encoding="utf-8") as f:
                js_list = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "JS List Load Error", f"Failed to load js_list.json: {e}")
            return

        # ✅ передаём в loader
        load_js_tree_from_bot(js_list, config_data, self.xss_controller)


    def _handle_start_bot(self):
        print("[DEBUG] Start Bot button clicked.")
        bot_type = "xss-bot"
        config = {
            "target": "http://localhost:8080/test3.html",
            "param": "q",
            "headless": True,
            "profile_name": "default"
        }

        bot_id = self.bot_manager.create_bot(bot_type, config)
        if bot_id:
            print(f"[GUI] Bot {bot_id} successfully launched.")
            
            alias = "New Bot"  # пока дефолт, потом сделаем окно
            status = "Ready"
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
            selected_item.setText(3, "Stopped")

        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Failed to stop bot '{bot_id}':\n{str(e)}")
            
            
    def _handle_delete_bot(self):
        selected_item = self.ui.bot_Widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self.parent, "No Selection", "Please select a bot to delete.")
            return

        bot_id = selected_item.text(1)

        confirm = QMessageBox.question(
            self.parent,
            "Confirm Deletion",
            f"Are you sure you want to delete bot '{bot_id}'?\nThis will stop the bot and remove all its data.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            # Остановить Docker (если работает)
            self.bot_manager.stop_bot(bot_id)

            # Удалить папку бота
            bot_path = os.path.join("data", "bots", bot_id)
            shutil.rmtree(bot_path, ignore_errors=True)

            # Удалить строку из таблицы
            index = self.ui.bot_Widget.indexOfTopLevelItem(selected_item)
            self.ui.bot_Widget.takeTopLevelItem(index)

            QMessageBox.information(self.parent, "Bot Deleted", f"Bot '{bot_id}' was deleted successfully.")

        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Failed to delete bot '{bot_id}':\n{e}")

            
    def _handle_configure_bot(self):
        selected_item = self.ui.bot_Widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self.parent, "No Selection", "Please select a bot.")
            return

        bot_id = selected_item.text(1)
        dialog = BotConfigDialog(bot_id=bot_id, parent=self.parent)

        if dialog.exec_() == QDialog.Accepted:
            # Загружаем config.json заново
            config_path = os.path.join("data", "bots", bot_id, "config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)

                    domain = config.get("target", "")
                    if domain:
                        selected_item.setText(4, domain)

                    profile = config.get("profile_name", "")
                    if profile:
                        selected_item.setText(5, profile)

                except Exception as e:
                    print(f"[ERROR] Failed to refresh UI after config: {e}")

                    
                    
    def on_btn_loadBot_clicked(self):
        dialog = LoadBotsDialog(parent=self.parent)
        if dialog.exec_() == QDialog.Accepted:
            bot_ids = dialog.get_selected_bots()

            for bot_id in bot_ids:
                bot_type = bot_id.split("_")[0]
                status_path = f"data/bots/{bot_id}/status.json"
                config_path = f"data/bots/{bot_id}/config.json"

                # Дефолты
                status = "Running"
                alias = "Loaded Bot"
                domain = ""
                profile = "default"
                created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                comment = ""

                # Сначала читаем config.json (важнее!)
                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r", encoding="utf-8") as f:
                            config_data = json.load(f)
                            domain = config_data.get("target", "")
                            profile = config_data.get("profile_name", "default")
                    except Exception as e:
                        print(f"[ERROR] Failed to read config: {e}")

                # Потом статус
                if os.path.exists(status_path):
                    try:
                        with open(status_path, "r", encoding="utf-8") as f:
                            status_data = json.load(f)
                            status = status_data.get("status", "Ready")
                            comment = status_data.get("comment", "")
                            created = status_data.get("created", created)
                    except Exception as e:
                        print(f"[ERROR] Failed to read status: {e}")

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
                    with open(config_path, "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=4)
                except Exception as e:
                    QMessageBox.warning(self.parent, "Error", f"Failed to apply config to {bot_id}:\n{str(e)}")
                    continue

                # 🔄 Обновляем колонку 4 (Domain)
                domain = config.get("target", "")
                if domain:
                    item.setText(4, domain)

                # 🔄 Обновляем колонку 5 (Profile), если есть
                profile_name = config.get("profile_name", "")
                if profile_name:
                    item.setText(5, profile_name)

                    
    def _handle_context_menu(self, position):
        callbacks = {
            "launch": self.launch_bot,
            "stop": self.stop_bot,
            "configure": self.configure_bot,
            "save_profile": self.save_bot_profile,
            "load_profile": self.load_bot_profile,
            "rename": self.rename_bot,
            "send_to_js": self._send_to_js_analyzer,
            "analyze_js": self._analyze_js_from_bot,
            "view_logs": self.open_log_viewer
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
        item.setText(3, "Stopped")
        
    def configure_bot(self, item):
        bot_id = item.text(1)
        dialog = BotConfigDialog(bot_id=bot_id, parent=self.parent)

        if dialog.exec_() == QDialog.Accepted:
            config_path = os.path.join("data", "bots", bot_id, "config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)

                    # 🔄 Обновляем колонку 4 (Domain)
                    domain = config.get("target", "")
                    if domain:
                        item.setText(4, domain)

                    # 🔄 Обновляем колонку 5 (Profile)
                    profile = config.get("profile_name", "")
                    if profile:
                        item.setText(5, profile)

                except Exception as e:
                    print(f"[ERROR] Failed to load updated config: {e}")


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
        item.setText(3, "Running")
        
        
        
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
        
    def rename_bot(self, item: QTreeWidgetItem):
        bot_id = item.text(1)
        current_name = item.text(2)

        new_name, ok = QInputDialog.getText(self.parent, "Rename Bot", "Enter new bot name:", text=current_name)
        if not ok or not new_name.strip():
            return

        new_name = new_name.strip()
        item.setText(2, new_name)

        # Обновим status.json
        status_path = f"data/bots/{bot_id}/status.json"
        if os.path.exists(status_path):
            try:
                with open(status_path, "r", encoding="utf-8") as f:
                    status_data = json.load(f)
            except:
                status_data = {}

            status_data["alias"] = new_name
            try:
                with open(status_path, "w", encoding="utf-8") as f:
                    json.dump(status_data, f, indent=4)
            except Exception as e:
                print(f"[ERROR] Cannot save new alias: {e}")
                      
    def open_log_viewer(self, item):
        bot_id = item.text(1)
        log_path = f"data/bots/{bot_id}/logs.txt"

        if not os.path.exists(log_path):
            QMessageBox.warning(self.parent, "No Logs", f"No logs found for bot: {bot_id}")
            return

        dialog = LogViewerDialog(bot_id, log_path, parent=self.parent)
        dialog.exec_()
        
    def load_log_options(self, bot_id: str):
        config_path = f"data/bots/{bot_id}/config.json"
        if not os.path.exists(config_path):
            return

        with open(config_path, "r") as f:
            config = json.load(f)
            log_opts = config.get("log_options", {})

        self.ui.chkLogRequests.setChecked(log_opts.get("requests", True))
        self.ui.chkLogResponses.setChecked(log_opts.get("responses", True))
        self.ui.chkLogConsole.setChecked(log_opts.get("console", False))
        self.ui.chkLogDockerEvents.setChecked(log_opts.get("docker", False))
        
    def save_log_options(self, bot_id: str):
        config_path = f"data/bots/{bot_id}/config.json"
        if not os.path.exists(config_path):
            return

        with open(config_path, "r") as f:
            config = json.load(f)

        config["log_options"] = {
            "requests": self.ui.chkLogRequests.isChecked(),
            "responses": self.ui.chkLogResponses.isChecked(),
            "console": self.ui.chkLogConsole.isChecked(),
            "docker": self.ui.chkLogDockerEvents.isChecked()
        }

        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
            
    def _on_save_log_options(self):
        bot_id = self.get_selected_bot_id()
        if bot_id:
            self.save_log_options(bot_id)
            
    def get_selected_bot_id(self):
        item = self.ui.bot_Widget.currentItem()
        if item:
            return item.text(1)  # Колонка с Bot ID
        return None
    
    
    def _update_bot_logs(self):
        if not self.current_log_path or not os.path.exists(self.current_log_path):
            return

        try:
            with open(self.current_log_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.ui.plainText_botLogs.setPlainText(content)
        except Exception as e:
            print(f"[LOG ERROR] Failed to read logs.txt: {e}")
            
    def _start_log_monitoring(self, bot_id: str):
        self.current_log_path = f"data/bots/{bot_id}/logs.txt"
        self.log_timer.start()
        
    def _stop_log_monitoring(self):
        self.log_timer.stop()
        self.current_log_path = None
        self.ui.plainText_botLogs.clear()



















from PyQt5.QtWidgets import QMessageBox, QTreeWidgetItem
from core.bot_core.bot_manager import BotManager

class BotPanelController:
    def __init__(self, ui, parent=None):
        self.ui = ui  # ссылка на ui из Qt Designer
        self.parent = parent  # ✅ Сохраняем родителя
        self.bot_manager = BotManager()  # ✅ создаём объект
        self._setup_connections()

    def _setup_connections(self):
        self.ui.btn_startBot.clicked.connect(self._handle_start_bot)
        self.ui.btn_stopBot.clicked.connect(self.on_btn_stopBot_clicked)

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




from core.bot_core.bot_manager import BotManager

class BotPanelController:
    def __init__(self, ui, parent=None):
        self.ui = ui  # ссылка на ui из Qt Designer
        self.bot_manager = BotManager()  # создаём менеджер
        self._setup_connections()

    def _setup_connections(self):
        self.ui.btn_startBot.clicked.connect(self._handle_start_bot)

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
        else:
            print("[GUI] Failed to start bot.")

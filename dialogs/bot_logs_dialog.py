from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPlainTextEdit, QPushButton
import os

class BotLogsDialog(QDialog):
    def __init__(self, bot_id: str, log_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Logs for {bot_id}")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout()
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)

        # Загрузка логов
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.log_view.setPlainText(content)
            except Exception as e:
                self.log_view.setPlainText(f"[ERROR] Failed to load logs:\n{e}")
        else:
            self.log_view.setPlainText("Log file not found.")

        layout.addWidget(self.log_view)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

        self.setLayout(layout)

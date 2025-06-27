# dialogs/create_bot_dialog/create_bot_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton
)
from PyQt5.QtCore import QDateTime

class CreateBotDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Bot")

        self.selected_bot_type = None
        self.bot_alias = None

        self.layout = QVBoxLayout()

        # Bot Type
        self.layout.addWidget(QLabel("Select Bot Type:"))
        self.combo_bot_type = QComboBox()
        self.combo_bot_type.addItems(["xss-bot", "crawler_bot"])  # Добавь свои типы
        self.layout.addWidget(self.combo_bot_type)

        # Alias
        self.layout.addWidget(QLabel("Bot Name (optional):"))
        self.line_bot_alias = QLineEdit()
        self.layout.addWidget(self.line_bot_alias)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Cancel")
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)

        self.layout.addLayout(btn_layout)
        self.setLayout(self.layout)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def get_bot_data(self):
        bot_type = self.combo_bot_type.currentText()
        alias = self.line_bot_alias.text().strip()

        timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
        bot_id = f"{bot_type}_{timestamp}"

        return {
            "bot_type": bot_type,
            "bot_id": bot_id,
            "alias": alias or bot_id
        }

import os
import json
from PyQt5.QtWidgets import (
    QDialog, QListWidget, QTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QListWidgetItem
)
from PyQt5.QtCore import Qt

class LoadBotsDialog(QDialog):
    def __init__(self, bots_path="data/bots", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Load Bots")
        self.resize(700, 400)

        self.bots_path = os.path.abspath(bots_path)
        self.selected_bots = []

        self._init_ui()
        self._load_bot_list()

    def _init_ui(self):
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._preview_config)

        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)

        self.btn_add = QPushButton("Add to UI")
        self.btn_add.clicked.connect(self._handle_add)

        layout = QHBoxLayout()
        layout.addWidget(self.list_widget, 2)
        layout.addWidget(self.text_preview, 3)

        bottom_layout = QVBoxLayout()
        bottom_layout.addLayout(layout)
        bottom_layout.addWidget(self.btn_add)

        self.setLayout(bottom_layout)

    def _load_bot_list(self):
        if not os.path.exists(self.bots_path):
            QMessageBox.warning(self, "Missing Path", f"Bots folder not found: {self.bots_path}")
            return

        for name in os.listdir(self.bots_path):
            full_path = os.path.join(self.bots_path, name)
            if os.path.isdir(full_path):
                self.list_widget.addItem(QListWidgetItem(name))

    def _preview_config(self, item: QListWidgetItem):
        bot_id = item.text()
        config_path = os.path.join(self.bots_path, bot_id, "config.json")

        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    content = json.load(f)
                pretty = json.dumps(content, indent=4)
                self.text_preview.setPlainText(pretty)
            except Exception as e:
                self.text_preview.setPlainText(f"Error loading config: {str(e)}")
        else:
            self.text_preview.setPlainText("No config.json found.")

    def _handle_add(self):
        self.selected_bots = [item.text() for item in self.list_widget.selectedItems()]
        if not self.selected_bots:
            QMessageBox.warning(self, "No Selection", "Please select at least one bot to load.")
            return
        self.accept()

    def get_selected_bots(self):
        return self.selected_bots

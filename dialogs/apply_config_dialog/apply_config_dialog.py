import os
import json
from PyQt5.QtWidgets import (
    QDialog, QListWidget, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QMessageBox, QListWidgetItem
)
from PyQt5.QtCore import Qt

class ApplyConfigDialog(QDialog):
    def __init__(self, profiles_path="assets/bot_profiles", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Apply Config to Selected Bots")
        self.resize(700, 400)

        self.profiles_path = os.path.abspath(profiles_path)
        self.selected_profile = None

        self._init_ui()
        self._load_profiles()

    def _init_ui(self):
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._preview_profile)

        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)

        self.btn_apply = QPushButton("Apply to Selected")
        self.btn_apply.clicked.connect(self._handle_apply)

        layout = QHBoxLayout()
        layout.addWidget(self.list_widget, 2)
        layout.addWidget(self.text_preview, 3)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addWidget(self.btn_apply)

        self.setLayout(main_layout)

    def _load_profiles(self):
        if not os.path.exists(self.profiles_path):
            QMessageBox.warning(self, "Missing Folder", f"Profile folder not found: {self.profiles_path}")
            return

        for name in os.listdir(self.profiles_path):
            if name.endswith(".json"):
                self.list_widget.addItem(QListWidgetItem(name))

    def _preview_profile(self, item: QListWidgetItem):
        file_path = os.path.join(self.profiles_path, item.text())
        try:
            with open(file_path, "r") as f:
                content = json.load(f)
            pretty = json.dumps(content, indent=4)
            self.text_preview.setPlainText(pretty)
        except Exception as e:
            self.text_preview.setPlainText(f"Error loading profile: {str(e)}")

    def _handle_apply(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Please select a profile to apply.")
            return
        self.selected_profile = item.text()
        self.accept()

    def get_selected_profile_path(self):
        if self.selected_profile:
            return os.path.join(self.profiles_path, self.selected_profile)
        return None

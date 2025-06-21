from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QCheckBox, QPlainTextEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox
)
from PyQt5.QtCore import Qt
import json
import os

class BotConfigDialog(QDialog):
    def __init__(self, bot_id: str = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bot Configuration")
        self.resize(500, 400)
        self.bot_id = bot_id

        self._init_ui()
        if self.bot_id:
            self._load_existing_config()

    def _init_ui(self):
        form_layout = QFormLayout()

        self.target_input = QLineEdit()
        form_layout.addRow("Target URL:", self.target_input)

        self.param_input = QLineEdit()
        form_layout.addRow("Param Name:", self.param_input)

        self.headless_checkbox = QCheckBox("Enable Headless Mode")
        form_layout.addRow("", self.headless_checkbox)

        self.proxy_input = QLineEdit()
        form_layout.addRow("Proxy (optional):", self.proxy_input)

        self.user_agent_input = QLineEdit()
        form_layout.addRow("User-Agent:", self.user_agent_input)

        self.headers_edit = QPlainTextEdit()
        self.headers_edit.setPlaceholderText('{\n    "Header-Name": "value"\n}')
        form_layout.addRow("Headers (JSON):", self.headers_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_save_profile = QPushButton("Save as Profile")
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save_profile)

        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save_profile.clicked.connect(self.save_as_profile)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def _load_existing_config(self):
        config_path = os.path.join("data", "bots", self.bot_id, "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                self.target_input.setText(config.get("target", ""))
                self.param_input.setText(config.get("param", ""))
                self.headless_checkbox.setChecked(config.get("headless", False))
                self.proxy_input.setText(config.get("proxy", ""))
                self.user_agent_input.setText(config.get("user_agent", ""))
                headers = config.get("headers", {})
                self.headers_edit.setPlainText(json.dumps(headers, indent=4))
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load config: {str(e)}")

    def get_config(self) -> dict:
        try:
            headers = json.loads(self.headers_edit.toPlainText() or "{}")
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Invalid Headers", "Headers must be valid JSON.")
            return None

        return {
            "target": self.target_input.text().strip(),
            "param": self.param_input.text().strip(),
            "headless": self.headless_checkbox.isChecked(),
            "proxy": self.proxy_input.text().strip(),
            "user_agent": self.user_agent_input.text().strip(),
            "headers": headers
        }
        
    def save_as_profile(self):
        from PyQt5.QtWidgets import QFileDialog
        config = self.get_config()
        if config is None:
            return  # ошибка уже показана пользователю

        default_path = os.path.join("assets", "bot_profiles")
        os.makedirs(default_path, exist_ok=True)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Profile As",
            os.path.join(default_path, "profile.json"),
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            QMessageBox.information(self, "Success", f"Profile saved to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save profile:\n{str(e)}")
            
    def accept(self):
        config = self.get_config()
        if config is None:
            return  # Ошибка уже показана пользователю

        if self.bot_id:
            config_path = os.path.join("data", "bots", self.bot_id, "config.json")
            try:
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save config:\n{str(e)}")
                return

        super().accept()



# dialogs/crawler_config_dialog/crawler_config_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QPushButton
)
import os
import json

class CrawlerConfigDialog(QDialog):
    def __init__(self, bot_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"CrawlerBot Config - {bot_id}")
        self.setMinimumWidth(400)
        self.bot_id = bot_id
        self.config_path = os.path.join("data", "bots", bot_id, "config.json")

        self._build_ui()
        self._load_config()

    def _build_ui(self):
        layout = QVBoxLayout()

        # Target URL
        layout.addWidget(QLabel("Target URL:"))
        self.line_target = QLineEdit()
        layout.addWidget(self.line_target)

        # Depth
        layout.addWidget(QLabel("Scan Depth:"))
        self.spin_depth = QSpinBox()
        self.spin_depth.setRange(0, 10)
        self.spin_depth.setValue(1)
        layout.addWidget(self.spin_depth)

        # Checkboxes
        self.chk_follow_external = QCheckBox("Follow External Links")
        self.chk_download_js = QCheckBox("Download JS Files")
        layout.addWidget(self.chk_follow_external)
        layout.addWidget(self.chk_download_js)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Save")
        btn_cancel = QPushButton("Cancel")
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # Connect
        btn_ok.clicked.connect(self._save_and_close)
        btn_cancel.clicked.connect(self.reject)

    def _load_config(self):
        if not os.path.exists(self.config_path):
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            self.line_target.setText(config.get("target", ""))
            self.spin_depth.setValue(config.get("depth", 1))
            self.chk_follow_external.setChecked(config.get("follow_external", False))
            self.chk_download_js.setChecked(config.get("download_js", False))
        except Exception as e:
            print(f"[ERROR] Failed to load crawler config: {e}")

    def _save_and_close(self):
        config = {
            "target": self.line_target.text().strip(),
            "depth": self.spin_depth.value(),
            "follow_external": self.chk_follow_external.isChecked(),
            "download_js": self.chk_download_js.isChecked(),
            "profile_name": "default",
            "headless": True
        }

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            self.accept()
        except Exception as e:
            print(f"[ERROR] Failed to save crawler config: {e}")
            self.reject()

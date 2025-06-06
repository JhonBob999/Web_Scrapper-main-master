from PyQt5.QtWidgets import QDialog, QListWidget, QVBoxLayout, QTextBrowser, QHBoxLayout, QComboBox, QLabel
from core.xss_payload_manager import load_xss_payloads
import json
import os
import html as html_utils
import pyperclip

CHEATSHEET_PATH = os.path.join("assets", "cheatsheet", "xss_cheatsheet.json")

class XssCheatsheetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🧠 XSS Cheatsheet")
        self.setMinimumSize(800, 500)

        # Левая панель — список техник XSS
        self.listWidget = QListWidget()

        # Правая панель — описание + примеры
        self.textBrowser = QTextBrowser()

        # Layout — только 2 панели: список и описание
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.listWidget, 1)
        main_layout.addWidget(self.textBrowser, 3)
        self.setLayout(main_layout)

        # Логика — только для справки!
        self.cheats = self.load_cheatsheet()
        self.populate_list()
        self.listWidget.currentItemChanged.connect(self.display_cheat)

    def load_cheatsheet(self):
        if not os.path.exists(CHEATSHEET_PATH):
            return {}
        with open(CHEATSHEET_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def populate_list(self):
        for key in self.cheats:
            title = self.cheats[key].get("title", key)
            self.listWidget.addItem(title)

    def display_cheat(self, current, previous):
        if not current:
            return
        selected_title = current.text()
        for key, data in self.cheats.items():
            if data.get("title") == selected_title:
                html = f"<h2>{data['title']}</h2>"
                html += f"<p><b>Описание:</b><br>{data['description']}</p>"

                if data.get("where"):
                    html += "<p><b>Where to find:</b><ul>"
                    for item in data["where"]:
                        html += f"<li>{item}</li>"
                    html += "</ul></p>"

                if data.get("payloads"):
                    html += "<p><b>Payload examples:</b><pre>"
                    for item in data["payloads"]:
                        html += f"{html_utils.escape(item)}\n"
                    html += "</pre></p>"
                self.textBrowser.setHtml(html)
                break
            

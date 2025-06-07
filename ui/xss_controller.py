from PyQt5.QtWidgets import QMessageBox, QListWidgetItem
from core.xss_payload_manager import load_xss_payloads
from dialogs.params_cheatsheet_dialog import ParamsCheatsheetDialog
from dialogs.payload_history_dialog import PayloadHistoryDialog
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import webbrowser, urllib.parse
import json, os

class XssController:
    def __init__(self, ui, parent_widget=None):
        self.ui = ui
        self.parent_widget = parent_widget
        self.setup_connections()
        self.ui.payload_combox.setCurrentText("html_body")
        self.load_payloads("html_body")

    def setup_connections(self):
        self.ui.btnRunXss.clicked.connect(self.run_xss_exploit)
        self.ui.payload_combox.currentTextChanged.connect(self.load_payloads)
        self.ui.Payload_listWidget.itemClicked.connect(self.insert_payload_to_field)
        self.ui.payload_search.textChanged.connect(self.filter_payloads)
        self.ui.filter_btn.clicked.connect(self.clear_payload_filter)
        self.ui.params_btn.clicked.connect(self._open_params_cheatsheet)
        self.ui.history_btn.clicked.connect(self._open_history)


    def run_xss_exploit(self):
        target = self.ui.lineEditXssTarget.text().strip()
        payload = self.ui.plainTextPayload.toPlainText().strip()
        payload_encoded = urllib.parse.quote(payload)
        headless = self.ui.chkHeadless.isChecked()

        if not target or not payload:
            QMessageBox.warning(None, "Missing Input", "Please enter both target and payload.")
            return

        param_name = self.ui.lineEditParamName.text().strip() or "q"
        full_url = f"http://{target}?{param_name}={payload_encoded}"

        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1280,720")

            # ✅ Подключаем ChromeDriver
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )

            driver.get(full_url)
            self.ui.response_textEdit.append(f"[XSS] Loaded in browser: {full_url}")

            # — Добавляем payload в историю —
            self._add_to_history(payload)

        except Exception as e:
            self.ui.response_textEdit.append(f"[ERROR] {str(e)}")
        finally:
            driver.quit()


    def load_payloads(self, context):
        payloads = load_xss_payloads(context)
        self.current_payloads = payloads  # сохраняем оригинальный список
        self.display_payloads(payloads)

    def display_payloads(self, payloads):
        self.ui.Payload_listWidget.clear()
        for item in payloads:
            list_item = QListWidgetItem(item['payload'])
            list_item.setToolTip(item['desc'])
            self.ui.Payload_listWidget.addItem(list_item)

    def insert_payload_to_field(self, item):
        payload = item.text().split(" — ")[0]
        self.ui.plainTextPayload.setPlainText(payload)
        
    def filter_payloads(self):
        query = self.ui.payload_search.text().lower()
        filtered = []
        for item in getattr(self, 'current_payloads', []):
            # Фильтруем по payload и description
            if query in item['payload'].lower() or query in item['desc'].lower():
                filtered.append(item)
        self.display_payloads(filtered)
    
    def clear_payload_filter(self):
        self.ui.payload_search.clear()
        self.display_payloads(getattr(self, 'current_payloads', []))
        
    def _open_params_cheatsheet(self):
        # Предположим, что у вас есть LineEdit: self.ui.lineEditXssTarget
        # Это реально виджет и у него есть метод window() → вернёт главное окно.
        parent_widget = self.ui.lineEditXssTarget.window()
        dialog = ParamsCheatsheetDialog(parent_widget)
        dialog.exec_()
        
    def _open_history(self):
        # parent берём из реального виджета, например:
        parent_widget = self.ui.lineEditXssTarget.window()
        dlg = PayloadHistoryDialog(parent_widget)
        dlg.exec_()
        
    def _history_path(self):
        # путь до payload_history.json
        return os.path.join(
            os.path.dirname(__file__), "..", "data", "payload_history.json"
        )

    def _load_history(self):
        try:
            with open(self._history_path(), "r", encoding="utf-8") as f:
                return json.load(f).get("history", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_history(self, history):
        # храним только последние 10
        data = {"history": history[:10]}
        with open(self._history_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _add_to_history(self, payload):
        hist = self._load_history()
        if payload in hist:
            hist.remove(payload)
        hist.insert(0, payload)
        self._save_history(hist)





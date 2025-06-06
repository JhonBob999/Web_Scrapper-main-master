from PyQt5.QtWidgets import QMessageBox, QListWidgetItem
from core.xss_payload_manager import load_xss_payloads
from dialogs.params_cheatsheet_dialog import ParamsCheatsheetDialog
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import webbrowser, urllib.parse

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


    def run_xss_exploit(self):
        target = self.ui.lineEditXssTarget.text().strip()
        payload = self.ui.plainTextPayload.toPlainText().strip()
        payload_encoded = urllib.parse.quote(payload)
        headless = self.ui.chkHeadless.isChecked()

        if not target or not payload:
            QMessageBox.warning(None, "Missing Input", "Please enter both target and payload.")
            return

        param_name = self.ui.lineEditParamName.text().strip() or "q"
        full_url = f"http://{target}?{param_name}={urllib.parse.quote(payload)}"


        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1280,720")

            # ✅ Вот здесь подключаем ChromeDriver через webdriver-manager
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )

            driver.get(full_url)
            self.ui.textEdit.append(f"[XSS] Loaded in browser: {full_url}")

        except Exception as e:
            self.ui.textEdit.append(f"[ERROR] {str(e)}")

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




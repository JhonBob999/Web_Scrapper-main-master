from PyQt5.QtWidgets import QMessageBox
from core.xss_payload_manager import load_xss_payloads
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import webbrowser, urllib.parse

class XssController:
    def __init__(self, ui):
        self.ui = ui
        self.setup_connections()
        self.ui.payload_combox.setCurrentText("html_body")
        self.load_payloads("html_body")

    def setup_connections(self):
        self.ui.btnRunXss.clicked.connect(self.run_xss_exploit)
        self.ui.payload_combox.currentTextChanged.connect(self.load_payloads)
        self.ui.Payload_listWidget.itemClicked.connect(self.insert_payload_to_field)

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
        self.ui.Payload_listWidget.clear()
        for item in payloads:
            self.ui.Payload_listWidget.addItem(f"{item['payload']} — {item['desc']}")

    def insert_payload_to_field(self, item):
        payload = item.text().split(" — ")[0]
        self.ui.plainTextPayload.setPlainText(payload)

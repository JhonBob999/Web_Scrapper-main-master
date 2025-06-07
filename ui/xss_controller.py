from PyQt5.QtWidgets import QMessageBox, QListWidgetItem, QApplication
from core.xss_payload_manager import load_xss_payloads
from dialogs.params_cheatsheet_dialog import ParamsCheatsheetDialog
from dialogs.payload_history_dialog import PayloadHistoryDialog
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import webbrowser, urllib.parse
import json, os, requests, time

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
        self.ui.runAllBtn.clicked.connect(self._run_all_payloads)


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
        
        
    def _run_all_payloads(self):
        """
        Автоматически подставляет и тестирует каждый payload из QListWidget,
        выводит подробные логи в response_textEdit и накапливает все payload в plainTextPayload.
        """
        # 1) Собираем все payload-ы из QListWidget
        list_widget = self.ui.Payload_listWidget
        count = list_widget.count()
        if count == 0:
            self.ui.response_textEdit.clear()
            self.ui.response_textEdit.insertPlainText("No payloads in list to run.")
            return
        payloads = [list_widget.item(i).text() for i in range(count)]
        total = len(payloads)

        # 2) Очистка полей и начальный лог
        self.ui.response_textEdit.clear()
        self.ui.response_textEdit.insertPlainText(f"Starting Run All ({total} payloads)\n")
        self.ui.plainTextPayload.clear()

        # 3) Прогресс-бар
        self._show_progress(total)

        results = []
        for idx, payload in enumerate(payloads, start=1):
            # 4) Накопление payload-ов в plainTextPayload
            self.ui.plainTextPayload.appendPlainText(payload)

            # 5) Формируем URL
            target = self.ui.lineEditXssTarget.text().strip()
            param  = self.ui.lineEditParamName.text().strip()
            encoded = urllib.parse.quote(payload)
            url = f"http://{target}?{param}={encoded}"

            # 6) Тестируем payload
            success, status, elapsed = self._test_payload(payload)
            results.append({
                "payload": payload,
                "success": success,
                "status": status,
                "time_ms": elapsed
            })

            # 7) Логируем в response_textEdit
            self.ui.response_textEdit.insertPlainText(
                f"[{idx}/{total}] Payload: {payload}\n"
                f"    URL: {url}\n"
                f"    Status: {status}  Elapsed: {elapsed:.1f}ms  Success: {success}\n"
            )

            # 8) Обновляем прогресс-бар
            self._update_progress(idx)

        # 9) Скрываем прогресс-бар и сохраняем результаты
        self._hide_progress()
        self.last_run_results = results

        # 10) Итоговое уведомление
        self._show_run_summary(results)


    def _get_payloads_for_context(self, context_name: str) -> list[str]:
        # контексты: Reflected, Stored, DOM
        filename = {
            "html_body": "xss_htmlbody.json",
            "js":    "xss_js.json",
            "attribute": "xss_attribute.json",
            "url_param": "xss_urlparam.json",
            "dom": "xss_params_dom.json"
            
        }.get(context_name)
        if not filename:
            return []

        path = os.path.join(os.path.dirname(__file__), "..", "assets", "cheatsheet", filename)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # предположим, у каждого объекта есть ключ "payload"
        return [item["payload"] for item in data if isinstance(item, dict) and "payload" in item]
    
    def _test_payload(self, payload: str):
        """
        Синхронно проверяет один payload:
        - Формирует URL по текущему target и param_name
        - Делаем HTTP GET
        - Возвращает (success, status_code, elapsed_ms)
        """
        target = self.ui.lineEditXssTarget.text().strip()
        param = self.ui.lineEditParamName.text().strip() or "q"
        if not target:
            return False, None, 0.0

        # Кодируем payload и собираем URL
        encoded = urllib.parse.quote(payload)
        url = f"http://{target}?{param}={encoded}"

        start = time.time()
        try:
            resp = requests.get(url, timeout=10)
            elapsed = (time.time() - start) * 1000  # в миллисекундах
            # Условие успешности можно подправить:
            success = resp.status_code == 200 and payload in resp.text
            return success, resp.status_code, elapsed
        except Exception as e:
            # В случае ошибки сети или таймаута
            return False, None, (time.time() - start) * 1000
    
    
    def _show_run_summary(self, results):
        success_count = sum(1 for r in results if r["success"])
        total = len(results)
        parent = self.ui.lineEditXssTarget.window()
        QMessageBox.information(
            parent, 
            "Run All Results",
            f"Successfully injected {success_count}/{total} payloads."
        )

    def _show_progress(self, total):
        self.ui.progressBar.setMaximum(total)
        self.ui.progressBar.setValue(0)
        self.ui.progressBar.show()

    def _update_progress(self, count):
        self.ui.progressBar.setValue(count)
        QApplication.processEvents()  # чтобы прогресс обновился в UI

    def _hide_progress(self):
        self.ui.progressBar.hide()

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

    def _open_params_cheatsheet(self):
        # Предположим, что у вас есть LineEdit: self.ui.lineEditXssTarget
        # Это реально виджет и у него есть метод window() → вернёт главное окно.
        parent_widget = self.ui.lineEditXssTarget.window()
        dialog = ParamsCheatsheetDialog(parent_widget)
        dialog.exec_()




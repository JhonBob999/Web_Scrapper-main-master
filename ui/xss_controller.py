# ui/xss_controller.py

import os
import json
import time
import requests
import urllib.parse
import webbrowser

from PyQt5.QtWidgets import (
    QMessageBox,
    QListWidgetItem,
    QApplication
)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from core.xss_payload_manager import load_xss_payloads
from dialogs.params_cheatsheet_dialog import ParamsCheatsheetDialog
from dialogs.payload_history_dialog import PayloadHistoryDialog

from threads.xss_runall_thread import XssRunAllThread



class XssController:
    def __init__(self, ui, parent_widget=None):
        self.ui = ui
        # реальный виджет-родитель (QMainWindow/QDialog) для всех диалогов
        self.parent_widget = parent_widget  
        self.setup_connections()

        # по умолчанию загружаем html_body-пейлоады
        self.ui.payload_combox.setCurrentText("html_body")
        self.load_payloads("html_body")


    def setup_connections(self):
        # Основные привязки сигналов → слотов
        self.ui.btnRunXss.clicked.connect(self.run_xss_exploit)
        self.ui.payload_combox.currentTextChanged.connect(self.load_payloads)
        self.ui.Payload_listWidget.itemClicked.connect(self.insert_payload_to_field)
        self.ui.payload_search.textChanged.connect(self.filter_payloads)
        self.ui.filter_btn.clicked.connect(self.clear_payload_filter)
        self.ui.params_btn.clicked.connect(self._open_params_cheatsheet)
        self.ui.history_btn.clicked.connect(self._open_history)
        self.ui.runAllBtn.clicked.connect(self._run_all_payloads)


    # ─── РЕФАКТОРИНГ: ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ──────────────────────────────────

    def _get_all_list_payloads(self) -> list[str]:
        """
        Считывает все payload из QListWidget и возвращает их в виде списка строк.
        """
        lw = self.ui.Payload_listWidget
        return [lw.item(i).text() for i in range(lw.count())]


    def _build_test_url(self, payload: str) -> str:
        """
        Строит URL вида http://<target>?<param>=<encoded_payload>
        """
        target = self.ui.lineEditXssTarget.text().strip()
        param  = self.ui.lineEditParamName.text().strip() or "q"
        encoded = urllib.parse.quote(payload)
        return f"http://{target}?{param}={encoded}"


    def _log_response(self, idx: int, total: int, payload: str,
                      url: str, status: int, elapsed: float, success: bool):
        """
        Записывает одну строку лога в response_textEdit.
        """
        self.ui.response_textEdit.insertPlainText(
            f"[{idx}/{total}] Payload: {payload}\n"
            f"    URL: {url}\n"
            f"    Status: {status}  Elapsed: {elapsed:.1f}ms  Success: {success}\n"
        )


    # ─── КОНЕЦ РЕФАКТОРИНГА ─────────────────────────────────────────────────────


    def run_xss_exploit(self):
        """
        Запускает одиночный XSS-тест с тем payload, который сейчас в plainTextPayload.
        """
        target = self.ui.lineEditXssTarget.text().strip()
        payload = self.ui.plainTextPayload.toPlainText().strip()
        if not target or not payload:
            QMessageBox.warning(
                self.parent_widget,
                "Missing Input",
                "Please enter both target and payload."
            )
            return

        # собираем URL
        full_url = self._build_test_url(payload)
        headless = self.ui.chkHeadless.isChecked()

        try:
            # настраиваем ChromeDriver
            opts = Options()
            if headless:
                opts.add_argument("--headless")
                opts.add_argument("--disable-gpu")
                opts.add_argument("--window-size=1280,720")

            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=opts
            )

            driver.get(full_url)
            self.ui.response_textEdit.append(f"[XSS] Loaded in browser: {full_url}")

            # сохраняем в историю
            self._add_to_history(payload)

        except Exception as e:
            self.ui.response_textEdit.append(f"[ERROR] {str(e)}")
        finally:
            driver.quit()


    def load_payloads(self, context: str):
        """
        Загружает из core.xss_payload_manager список payload-ов для выбранного контекста
        и сохраняет их для фильтрации/отображения.
        """
        payloads = load_xss_payloads(context)
        self.current_payloads = payloads
        self.display_payloads(payloads)


    def display_payloads(self, payloads: list[dict]):
        """
        Отображает список словарей {'payload':..., 'desc':...} в QListWidget.
        """
        self.ui.Payload_listWidget.clear()
        for item in payloads:
            list_item = QListWidgetItem(item['payload'])
            list_item.setToolTip(item['desc'])
            self.ui.Payload_listWidget.addItem(list_item)


    def insert_payload_to_field(self, item: QListWidgetItem):
        """
        По клику на элемент списка вставляет payload в поле plainTextPayload.
        """
        payload = item.text()
        self.ui.plainTextPayload.setPlainText(payload)


    def filter_payloads(self):
        """
        Фильтрация списка payload-ов по введённой строке в payload_search.
        """
        query = self.ui.payload_search.text().lower()
        filtered = [
            item for item in getattr(self, 'current_payloads', [])
            if query in item['payload'].lower() or query in item['desc'].lower()
        ]
        self.display_payloads(filtered)


    def clear_payload_filter(self):
        """
        Сбрасывает фильтр и показывает все payload-ы для текущего контекста.
        """
        self.ui.payload_search.clear()
        self.display_payloads(getattr(self, 'current_payloads', []))


    def _run_all_payloads(self):
        """
        Запускает фоновый поток для перебора всех payload-ов из QListWidget:
        - Накопление их в plainTextPayload и логирование через сигналы потока
        - Обновление прогресс-бара
        """
        payloads = self._get_all_list_payloads()
        total = len(payloads)

        if total == 0:
            self.ui.response_textEdit.clear()
            self.ui.response_textEdit.insertPlainText("No payloads in list to run.")
            return

        # Очистка и начальный лог
        self.ui.response_textEdit.clear()
        self.ui.response_textEdit.insertPlainText(f"Starting Run All ({total} payloads)\n")
        self.ui.plainTextPayload.clear()

        # Подготовка и запуск потока
        self.run_thread = XssRunAllThread(
            payloads=payloads,
            build_url_callback=self._build_test_url,
            test_payload_callback=self._test_payload,
            parent=self.parent_widget
        )
        # каждый log_entry будем обрабатывать вот этим слотом
        self.run_thread.log_entry.connect(self._on_thread_log)
        # по завершении — вот этим
        self.run_thread.finished.connect(self._on_thread_finish)

        # Показываем прогресс до старта потока
        self._show_progress(total)
        self.run_thread.start()


    def _on_thread_log(self, idx, total, payload, url, status, elapsed, success):
        """
        Слот для обработки сигнала log_entry из XssRunAllThread.
        Логируем строку, вставляем payload и обновляем полосу прогресса.
        """
        # накапливаем payload-ы в поле
        self.ui.plainTextPayload.appendPlainText(payload)
        # единый формат логов
        self._log_response(idx, total, payload, url, status, elapsed, success)
        # обновляем бар
        self._update_progress(idx)


    def _on_thread_finish(self, results):
        """
        Слот для обработки сигнала finished из XssRunAllThread.
        Скрывает прогресс, сохраняет результаты и показывает итоговое окно.
        """
        self._hide_progress()
        self.last_run_results = results
        self._show_run_summary(results)


    def _test_payload(self, payload: str):
        """
        Синхронное тестирование одного payload-а через requests.
        Возвращает (success: bool, status: int, elapsed_ms: float).
        """
        target = self.ui.lineEditXssTarget.text().strip()
        if not target:
            return False, None, 0.0

        # именно URL уже строим через _build_test_url
        url = self._build_test_url(payload)

        start = time.time()
        try:
            resp = requests.get(url, timeout=10)
            elapsed = (time.time() - start) * 1000
            success = (resp.status_code == 200 and payload in resp.text)
            return success, resp.status_code, elapsed
        except Exception:
            return False, None, (time.time() - start) * 1000

########### SUCCESSFULL TRIES ################
########### SUCCESSFULL TRIES ################

    def _show_run_summary(self, results: list[dict]):
        """
        Сообщает пользователю об общем количестве удачных попыток.
        """
        success_count = sum(1 for r in results if r["success"])
        total = len(results)
        QMessageBox.information(
            self.parent_widget,
            "Run All Results",
            f"Successfully injected {success_count}/{total} payloads."
        )

########### PROGRESSBAR SETTINGS ################
########### PROGRESSBAR SETTINGS ################

    def _show_progress(self, total: int):
        """Инициализирует и показывает прогресс-бар."""
        self.ui.progressBar.setMaximum(total)
        self.ui.progressBar.setValue(0)
        self.ui.progressBar.show()


    def _update_progress(self, count: int):
        """Обновляет значение прогресса и пропускает события GUI."""
        self.ui.progressBar.setValue(count)
        QApplication.processEvents()


    def _hide_progress(self):
        """Скрывает прогресс-бар."""
        self.ui.progressBar.setValue(0)


########### HISTORY BUTTON AND QDIALOG ################
########### HISTORY BUTTON AND QDIALOG ################


    def _open_history(self):
        """
        Показывает историю последних payload-ов в отдельном диалоге.
        """
        parent = self.ui.lineEditXssTarget.window()
        dlg = PayloadHistoryDialog(parent)
        dlg.exec_()


    def _history_path(self) -> str:
        """Возвращает путь до файла с историей."""
        return os.path.join(
            os.path.dirname(__file__), "..", "data", "payload_history.json"
        )


    def _load_history(self) -> list[str]:
        """Загружает из файла список последних payload-ов."""
        try:
            with open(self._history_path(), "r", encoding="utf-8") as f:
                return json.load(f).get("history", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []


    def _save_history(self, history: list[str]):
        """Сохраняет не более 10 последних записей истории."""
        data = {"history": history[:10]}
        with open(self._history_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


    def _add_to_history(self, payload: str):
        """Добавляет payload в начало истории, убирая дубликаты."""
        hist = self._load_history()
        if payload in hist:
            hist.remove(payload)
        hist.insert(0, payload)
        self._save_history(hist)

########### PARAMS CHEATSHEET BACK TO PARENT WIDGET ################
########### PARAMS CHEATSHEET BACK TO PARENT WIDGET ################

    def _open_params_cheatsheet(self):
        """
        Открывает модальное окно с Params Cheatsheet.
        Используем реальный виджет-родитель для правильной модальности.
        """
        parent = self.ui.lineEditXssTarget.window()
        dialog = ParamsCheatsheetDialog(parent)
        dialog.exec_()

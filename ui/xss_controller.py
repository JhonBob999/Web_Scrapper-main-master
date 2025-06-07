# ui/xss_controller.py

import os
import json
import time
import requests
import urllib.parse
import webbrowser
import subprocess

from PyQt5.QtWidgets import (
    QMessageBox,
    QListWidgetItem,
    QApplication,
    QMenu,
    QAction
)

from PyQt5.QtCore import (
    Qt
)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from core.xss_payload_manager import load_xss_payloads
from core.js_tree_loader import load_domain_tree

from utils.xss_utils import (
    build_test_url,
    get_listwidget_payloads,
    log_response,
    test_payload,
    add_to_payload_history,
    open_test_page,
    send_request_to_url
)


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
        self.set_payload_context(self.ui.payload_combox.currentText())


    def setup_connections(self):
        # Основные привязки сигналов → слотов
        self.ui.btnRunXss.clicked.connect(self.run_xss_exploit)
        self.ui.payload_combox.currentTextChanged.connect(self.set_payload_context)
        self.ui.Payload_listWidget.itemClicked.connect(self.insert_payload_to_field)
        self.ui.payload_search.textChanged.connect(self.filter_payloads)
        self.ui.filter_btn.clicked.connect(self.clear_payload_filter)
        self.ui.params_btn.clicked.connect(self._open_params_cheatsheet)
        self.ui.history_btn.clicked.connect(self._open_history)
        self.ui.runAllBtn.clicked.connect(self._run_all_payloads)
        self.ui.btn_testsandbox.clicked.connect(self.on_btn_testsandbox_clicked)
        self.ui.btn_run_payload.clicked.connect(self.on_btn_run_payload_clicked)
        #Testing JS Files
        self.ui.domain_combox.currentTextChanged.connect(self.on_domain_selected)
        self.load_available_domains()
        #TREEWIDGET CONTEXT MENU
        self.ui.tree_domain.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tree_domain.customContextMenuRequested.connect(self.show_tree_context_menu)

###### TREEWIDGET CONTEXT MENU CONNECTION ###########
###### TREEWIDGET CONTEXT MENU CONNECTION ###########

    def show_tree_context_menu(self, position):
        item = self.ui.tree_domain.itemAt(position)
        if not item or not item.parent():  # проверяем, что это .js файл, а не домен
            return

        parent_item = item.parent()
        domain = parent_item.text(0)
        script_name = item.text(0)

        menu = QMenu()

        # Пункт 1 — Print Info
        action_print = QAction("Print file info", self.ui.tree_domain)
        action_print.triggered.connect(lambda: self.print_file_info(domain, script_name))
        menu.addAction(action_print)

        # Пункт 2 — Open JS file
        action_open = QAction("Open JS file (if exists)", self.ui.tree_domain)
        action_open.triggered.connect(lambda: self.open_js_file(domain, script_name))
        menu.addAction(action_open)

        menu.exec_(self.ui.tree_domain.viewport().mapToGlobal(position))
        
        
    def print_file_info(self, domain, filename):
        print(f"[INFO] JS File: {filename} from {domain}")

    def open_js_file(self, domain, filename):
        path = os.path.join("data", "js_downloads", domain, filename)
        if not os.path.exists(path):
            print(f"[WARNING] File not found: {path}")
            return

        try:
            if os.name == 'nt':  # Windows
                os.startfile(path)
            elif os.name == 'posix':  # Linux/macOS
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            print(f"[ERROR] Failed to open file: {e}")

######## DOMAIN_COMBOX SELECTION #########
######## DOMAIN_COMBOX SELECTION #########

    def on_domain_selected(self, domain_name):
        base_path = f"data/exploits/{domain_name}"
        
        if not os.path.exists(base_path):
            print(f"[ERROR] Domain folder not found: {base_path}")
            return

        # Ищем .json файл в папке
        json_file = None
        for file in os.listdir(base_path):
            if file.endswith(".json"):
                json_file = os.path.join(base_path, file)
                break

        if not json_file:
            QMessageBox.warning(None, "JSON not found", f"No .json file found in {base_path}")
            return

        print(f"[INFO] Loading: {json_file}")
        load_domain_tree(self.ui.tree_domain, json_file)
        
######## DOMAIN_COMBOX LOADING #########       
######## DOMAIN_COMBOX LOADING ######### 
        
    def load_available_domains(self):
        exploits_path = "data/exploits"
        if not os.path.exists(exploits_path):
            return

        for name in os.listdir(exploits_path):
            full_path = os.path.join(exploits_path, name)
            if os.path.isdir(full_path):
                self.ui.domain_combox.addItem(name)


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
        target = self.ui.lineEditXssTarget.text().strip()
        param = self.ui.lineEditParamName.text().strip() or "q"
        full_url = build_test_url(payload, target, param)
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
            add_to_payload_history(payload)

        except Exception as e:
            self.ui.response_textEdit.append(f"[ERROR] {str(e)}")
        finally:
            driver.quit()
            

        
########### ALL PAYLOADS RUNING BLOCK ################
########### ALL PAYLOADS RUNING BLOCK ################

    def set_payload_context(self, context: str):
        """
        Public API: сменить контекст XSS, загрузить все payload-ы из core.xss_payload_manager
        и обновить отображение.
        """
        self.current_context = context
        self.current_payloads = load_xss_payloads(context)
        self._refresh_payload_list()


    def _refresh_payload_list(self, payloads: list[dict] = None):
        """
        Приватный метод: перерисовывает QListWidget.
        Если payloads не переданы, берёт self.current_payloads.
        """
        if payloads is None:
            payloads = getattr(self, 'current_payloads', [])

        lw = self.ui.Payload_listWidget
        lw.clear()
        for entry in payloads:
            item = QListWidgetItem(entry['payload'])
            item.setToolTip(entry.get('desc', ''))
            lw.addItem(item)


    def insert_payload_to_field(self, item: QListWidgetItem):
        """
        По клику на элемент списка вставляет payload в поле plainTextPayload.
        """
        payload = item.text()
        self.ui.plainTextPayload.setPlainText(payload)


    def filter_payloads(self):
        """
        Слот для текстового фильтра: отбирает записи из self.current_payloads
        и перерисовывает список.
        """
        q = self.ui.payload_search.text().lower()
        filtered = [
            item for item in getattr(self, 'current_payloads', [])
            if q in item['payload'].lower() or q in item.get('desc', '').lower()
        ]
        self._refresh_payload_list(filtered)


    def clear_payload_filter(self):
        """
        Сброс фильтра: сразу показываем все payload-ы.
        """
        self.ui.payload_search.clear()
        self._refresh_payload_list()

########### ALL PAYLOADS MAIN METHOD ################
########### ALL PAYLOADS MAIN METHOD ################

    def _run_all_payloads(self):
        """
        Запускает фоновый поток для перебора всех payload-ов из QListWidget:
        - Накопление их в plainTextPayload и логирование через сигналы потока
        - Обновление прогресс-бара
        """
        payloads = get_listwidget_payloads(self.ui.Payload_listWidget)
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
            build_url_callback=lambda payload: build_test_url(
                payload,
                self.ui.lineEditXssTarget.text().strip(),
                self.ui.lineEditParamName.text().strip() or "q"
            ),
            test_payload_callback=lambda payload: test_payload(
                payload,
                self.ui.lineEditXssTarget.text().strip(),
                self.ui.lineEditParamName.text().strip() or "q"
            ),
            parent=self.parent_widget
        )

        # каждый log_entry будем обрабатывать вот этим слотом
        self.run_thread.log_entry.connect(self._on_thread_log)
        # по завершении — вот этим
        self.run_thread.finished.connect(self._on_thread_finish)

        # Показываем прогресс до старта потока
        self._show_progress(total)
        self.run_thread.start()
        
        
    def on_btn_testsandbox_clicked(self):
        payload = self.ui.payload_line.text().strip()
        if not payload:
            return
        open_test_page(payload, use_localhost=True)
        
        
    def on_btn_run_payload_clicked(self):
        payload = self.ui.payload_line.text().strip()
        target = self.ui.domain_combox.currentText().strip()
        param = self.ui.payload_line.text().strip() or "q"

        if not target or not payload:
            QMessageBox.warning(self, "Input Error", "Please provide both payload and target.")
            return

        result = send_request_to_url(payload, target, param)
        
        log = (
            f"URL: {result['url']}\n"
            f"Status: {result['status']}\n"
            f"Time: {result['elapsed']}s\n"
        )
        if result["error"]:
            log += f"Error: {result['error']}\n"

        # ⬇️ выводим лог в payload_TextEdit
        self.ui.payload_TextEdit.appendPlainText(log)


        

        
########### THREADS FROM XSS_RUNALL_THREAD ################
########### THREADS FROM XSS_RUNALL_THREAD ################

    def _on_thread_log(self, idx, total, payload, url, status, elapsed, success):
        """
        Слот для обработки сигнала log_entry из XssRunAllThread.
        Логируем строку, вставляем payload и обновляем полосу прогресса.
        """
        # накапливаем payload-ы в поле
        self.ui.plainTextPayload.appendPlainText(payload)
        # единый формат логов
        log_response(self.ui.response_textEdit, idx, total, payload, url, status, elapsed, success)
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

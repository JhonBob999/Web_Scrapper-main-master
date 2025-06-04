from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QDialogButtonBox, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from utils.js_analyzer import analyze_js_files

class JsSelectionDialog(QDialog):
    def __init__(self, domain: str, js_urls: list[str], base_url: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"JS Files for {domain}")
        self.resize(700, 500)

        self.js_urls = js_urls
        self.base_url = base_url
        self.domain = domain

        layout = QVBoxLayout(self)

        # Список с чекбоксами
        self.list_widget = QListWidget()
        for url in js_urls:
            item = QListWidgetItem(url)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

        # Кнопки выбора всех / очистки
        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.unselect_all_btn = QPushButton("Unselect All")
        self.select_all_btn.clicked.connect(self.select_all)
        self.unselect_all_btn.clicked.connect(self.unselect_all)
        btn_layout.addWidget(self.select_all_btn)
        btn_layout.addWidget(self.unselect_all_btn)
        layout.addLayout(btn_layout)

        # Кнопки анализа и закрытия
        self.button_box = QDialogButtonBox()
        self.analyze_button = self.button_box.addButton("Analyze", QDialogButtonBox.ActionRole)
        self.close_button = self.button_box.addButton(QDialogButtonBox.Close)
        self.retire_button = self.button_box.addButton("Analyze with Retire.js", QDialogButtonBox.ActionRole)
        self.retire_button.clicked.connect(lambda: self.run_retire_analysis(self.domain))
        self.analyze_button.clicked.connect(self.run_analysis)
        self.close_button.clicked.connect(self.reject)
        layout.addWidget(self.button_box)

    def select_all(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Checked)

    def unselect_all(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)

    def run_analysis(self):
        selected_urls = [self.list_widget.item(i).text()
                         for i in range(self.list_widget.count())
                         if self.list_widget.item(i).checkState() == Qt.Checked]

        if not selected_urls:
            return

        results = analyze_js_files(selected_urls, self.base_url)
        lines = ["JS Analysis Results:\n"]
        for res in results:
            lines.append(f"{res['library']} {res['version']} → {res['url']}")

        from dialogs.page_parse_dialog import PageParseDialog
        dialog = PageParseDialog("JS Analysis", "\n".join(lines), self)
        dialog.exec_()

    def run_retire_analysis(self, domain):
        from utils.js_downloader import download_js_file
        from utils.retire_wrapper import analyze_with_retire
        from dialogs.page_parse_dialog import PageParseDialog
        from dialogs.retire_results_dialog import RetireResultsDialog
        from urllib.parse import urlparse

        save_dir = "data/js_downloads"
        parsed = urlparse(domain)
        base_url = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme else f"https://{domain}"

        selected_urls = [self.list_widget.item(i).text()
                        for i in range(self.list_widget.count())
                        if self.list_widget.item(i).checkState() == Qt.Checked]
        if not selected_urls:
            return

        summary_lines = []
        parsed_results = []

        for url in selected_urls:
            file_path = download_js_file(url, save_dir, base_url)
            if not file_path:
                summary_lines.append(f"[FAIL] {url} → download failed")
                continue

            res = analyze_with_retire(file_path)

            if res["status"] == "error":
                summary_lines.append(f"[FAIL] {url} → {res['error']}")
                continue

            if not res.get("data"):
                summary_lines.append(f"[OK] {url} → No vulnerabilities found")
                continue

            # Добавим результат для таблицы CVE
            parsed_results.append(res)

            # Строим текстовый лог
            for entry in res["data"]:
                lib = entry["results"][0]
                summary_lines.append(f"{entry['file']}")
                summary_lines.append(f"↳ {lib['component']} {lib['version']}")
                for vuln in lib["vulnerabilities"]:
                    cves = ", ".join(vuln.get("identifiers", {}).get("CVE", [])) or "-"
                    severity = vuln.get("severity", "-")
                    info = vuln.get("info", [])[0] if vuln.get("info") else "-"
                    summary_lines.append(f"  - {cves} | {severity}")
                    summary_lines.append(f"    ↪ {info}")
                summary_lines.append("")

        # Показываем оба окна
        if parsed_results:
            dialog = RetireResultsDialog(parsed_results, self)
            dialog.exec_()

        # Всегда показываем лог в текстовом виде
        msg = "\n".join(summary_lines)
        log_dialog = PageParseDialog("Retire.js Results (Log)", msg, self)
        log_dialog.exec_()





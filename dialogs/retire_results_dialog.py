from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QFileDialog, QMessageBox, QCheckBox
from PyQt5.QtCore import Qt
from utils.nvd_api import get_cve_details, get_cve_from_github_graphql
from dialogs.cve_details_dialog import CveDetailsDialog
import json
import os
import webbrowser
from datetime import datetime

class RetireResultsDialog(QDialog):
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Retire.js Report")
        self.resize(800, 500)

        self.vulnerabilities = results  # ← это список результатов

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Analyzed Files:"))

        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Library", "Version", "CVE", "Severity", "Info URL"])
        self.table.setColumnWidth(4, 300)
        layout.addWidget(self.table)

        self.save_button = QPushButton("Save Report")
        self.save_button.clicked.connect(self.save_report)
        layout.addWidget(self.save_button)
        
        self.use_github_checkbox = QCheckBox("Use GitHub instead of NVD")
        self.use_github_checkbox.setChecked(False)  # По умолчанию — NVD
        layout.addWidget(self.use_github_checkbox)
        
        self.table.cellDoubleClicked.connect(self.check_cve_on_double_click)
        
        self.populate_table()

    def populate_table(self):
        rows = []
        for result in self.vulnerabilities:
            file_path = result.get("file_path", "")
            for entry in result.get("data", []):
                for res in entry.get("results", []):
                    component = res.get("component", "")
                    version = res.get("version", "")
                    for vuln in res.get("vulnerabilities", []):
                        cves = vuln.get("identifiers", {}).get("CVE", ["N/A"])
                        cve = cves[0] if isinstance(cves, list) else str(cves)
                        severity = vuln.get("severity", "Unknown")
                        info_urls = vuln.get("info", [])
                        url = info_urls[0] if info_urls else ""
                        rows.append((component, version, cve, severity, url))

        self.table.setRowCount(len(rows))
        for i, (lib, ver, cve, sev, url) in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(lib))
            self.table.setItem(i, 1, QTableWidgetItem(ver))
            self.table.setItem(i, 2, QTableWidgetItem(cve))
            self.table.setItem(i, 3, QTableWidgetItem(sev))
            self.table.setItem(i, 4, QTableWidgetItem(url))


    def save_report(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"retire_report_{timestamp}"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            default_name,
            "JSON Report (*.json);;HTML Report (*.html)"
        )

        if path.endswith(".json"):
            raw_data = []
            for result in self.vulnerabilities:
                raw_data.append({
                    "file": result.get("file_path"),
                    "results": result.get("data")
                })
            with open(path, "w", encoding="utf-8") as f:
                json.dump(raw_data, f, indent=2)
            QMessageBox.information(self, "Saved", f"JSON saved to:\n{path}")

        elif path.endswith(".html"):
            html = self.generate_html_report()
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            QMessageBox.information(self, "Saved", f"HTML saved to:\n{path}")
            webbrowser.open(f"file:///{path}")

    def generate_html_report(self):
        html = "<html><head><meta charset='UTF-8'><title>Retire.js Report</title></head><body>"
        html += "<h2>Retire.js Analysis Results</h2>"

        for result in self.vulnerabilities:
            file_path = result.get("file_path", "Unknown file")
            html += f"<h3>File: {file_path}</h3>"
            html += "<table border='1' cellpadding='4' cellspacing='0'>"
            html += "<tr><th>Library</th><th>Version</th><th>CVE</th><th>Severity</th><th>Info URL</th></tr>"

            for entry in result.get("data", []):
                for lib in entry.get("results", []):
                    component = lib.get("component", "")
                    version = lib.get("version", "")
                    for vuln in lib.get("vulnerabilities", []):
                        cves = vuln.get("identifiers", {}).get("CVE", ["N/A"])
                        cve = cves[0] if isinstance(cves, list) else str(cves)
                        severity = vuln.get("severity", "Unknown")
                        info_urls = vuln.get("info", [])
                        url = info_urls[0] if info_urls else ""
                        html += f"<tr><td>{component}</td><td>{version}</td><td>{cve}</td><td>{severity}</td><td><a href='{url}'>{url}</a></td></tr>"

            html += "</table><br><hr><br>"

        html += "</body></html>"
        return html

    
    def check_cve_on_double_click(self, row, col):
        if col == 2:
            item = self.table.item(row, col)
            if not item:
                return
            cve_id = item.text().strip()

            if cve_id.startswith("CVE-"):
                if self.use_github_checkbox.isChecked():
                    data = get_cve_from_github_graphql(cve_id)
                    source = "GitHub"
                else:
                    data = get_cve_details(cve_id)
                    source = "NVD"

                if data:
                    dialog = CveDetailsDialog(data, self, source=source)
                    dialog.exec_()




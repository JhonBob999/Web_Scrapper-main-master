from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices



class CveDetailsDialog(QDialog):
    def __init__(self, cve_data, parent=None, source="NVD"):
        super().__init__(parent)
        self.setWindowTitle(f"CVE Details ({source})")
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        # 1. Заголовок
        cve_id = cve_data.get("cve", {}).get("CVE_data_meta", {}).get("ID", "Unknown")
        layout.addWidget(QLabel(f"<b>CVE ID:</b> {cve_id}"))

        # 2. Описание
        description = self.extract_description(cve_data)
        layout.addWidget(QLabel("<b>Description:</b>"))
        desc_box = QTextEdit(description)
        desc_box.setReadOnly(True)
        layout.addWidget(desc_box)

        # 3. CVSS Info
        cvss_text = self.extract_cvss_info(cve_data)
        if cvss_text:
            layout.addWidget(QLabel("<b>CVSS Vector:</b>"))
            cvss_box = QTextEdit(cvss_text)
            cvss_box.setReadOnly(True)
            layout.addWidget(cvss_box)

        # 4. CWE
        cwe = self.extract_cwe(cve_data)
        if cwe:
            layout.addWidget(QLabel(f"<b>CWE:</b> {cwe}"))

        # 5. Кнопка "Открыть в браузере"
        links = self.extract_urls(cve_data)
        if links:
            btn_layout = QHBoxLayout()
            for url in links:
                btn = QPushButton("Open CVE")
                btn.clicked.connect(lambda _, u=url: QDesktopServices.openUrl(QUrl(u)))
                btn_layout.addWidget(btn)
            layout.addLayout(btn_layout)

    def extract_description(self, data):
        desc_list = data.get("cve", {}).get("description", {}).get("description_data", [])
        for desc in desc_list:
            if desc.get("lang") == "en":
                return desc.get("value")
        return "No description available."

    def extract_cvss_info(self, data):
        metrics = data.get("impact", {}).get("baseMetricV3", {})
        if not metrics:
            return ""
        cvss = metrics.get("cvssV3", {})
        lines = [
            f"Base Score: {cvss.get('baseScore')}",
            f"Severity: {cvss.get('baseSeverity')}",
            f"Vector: {cvss.get('vectorString')}",
            f"Attack Vector: {cvss.get('attackVector')}",
            f"Privileges Required: {cvss.get('privilegesRequired')}",
            f"User Interaction: {cvss.get('userInteraction')}",
            f"Scope: {cvss.get('scope')}"
        ]
        return "\n".join(lines)

    def extract_cwe(self, data):
        cwe_data = data.get("cve", {}).get("problemtype", {}).get("problemtype_data", [])
        for item in cwe_data:
            for cwe in item.get("description", []):
                return cwe.get("value")
        return None

    def extract_urls(self, data):
        refs = data.get("cve", {}).get("references", {}).get("reference_data", [])
        return [r.get("url") for r in refs[:2]]  # первые 2 ссылки

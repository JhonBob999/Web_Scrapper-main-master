# dialogs/params_cheatsheet_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QTableWidget,
    QHeaderView, QPushButton, QLabel, QTableWidgetItem
)
import json
import os

class ParamsCheatsheetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Params Cheatsheet")
        self.resize(800, 900)

        # Список для хранения всех записей из JSON
        self.params_list = []

        # Загрузка данных и инициализация UI пойдут здесь
        self._load_all_json()
        self._init_ui()
        
    def _load_all_json(self):
        """
        Load entries from three JSON files and store them in self.params_list,
        adding an "xss_type" field to each entry. Handles both dict-and-list top-level structures.
        """
        base_path = os.path.join(os.path.dirname(__file__), "..", "assets", "cheatsheet")
        file_map = {
            "xss_params_reflected.json": "Reflected",
            "xss_params_stored.json":    "Stored",
            "xss_params_dom.json":       "DOM"
        }

        for filename, xss_type in file_map.items():
            full_path = os.path.join(base_path, filename)
            if not os.path.isfile(full_path):
                continue

            with open(full_path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            # В raw может быть либо список записей, либо dict {"key": [ ... ]}
            if isinstance(raw, dict):
                # Найти первое значение-список внутри словаря
                entries = next((v for v in raw.values() if isinstance(v, list)), [])
            elif isinstance(raw, list):
                entries = raw
            else:
                # Нечего парсить
                continue

            for item in entries:
                # Убедимся, что это словарь с нужными полями
                if not isinstance(item, dict):
                    continue
                item["xss_type"] = xss_type
                self.params_list.append(item)

    def _populate_table(self, data):
        """
        Заполняет QTableWidget списком словарей data.
        Каждый словарь должен содержать ключи: param, context, example, xss_type.
        """
        self.table.setRowCount(0)
        for row_idx, item in enumerate(data):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(item.get("param", "")))
            self.table.setItem(row_idx, 1, QTableWidgetItem(item.get("context", "")))
            self.table.setItem(row_idx, 2, QTableWidgetItem(item.get("example", "")))
            self.table.setItem(row_idx, 3, QTableWidgetItem(item.get("xss_type", "")))

    def _filter_table(self, text):
        """
        Фильтрует self.params_list по вхождению text (case-insensitive)
        в поля param, context, example или xss_type,
        и обновляет таблицу через _populate_table.
        """
        text_lower = text.lower()
        filtered = [
            item for item in self.params_list
            if (text_lower in item.get("param", "").lower() or
                text_lower in item.get("context", "").lower() or
                text_lower in item.get("example", "").lower() or
                text_lower in item.get("xss_type", "").lower())
        ]
        self._populate_table(filtered)

                    
    def _init_ui(self):
        """
        Set up the UI: search bar, explanatory label, table, and Close button.
        """
        layout = QVBoxLayout(self)

        # 1) Search input
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search params...")
        self.search_input.textChanged.connect(self._filter_table)
        layout.addWidget(self.search_input)

        # 2) Explanatory label
        label = QLabel("Filter by Param Name, Context, Example, or XSS Type:", self)
        layout.addWidget(label)

        # 3) Table setup
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Param Name", "Context", "Example", "XSS Type"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        # 4) Close button
        btn_close = QPushButton("Close", self)
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

        # 5) Populate table with all entries
        self._populate_table(self.params_list)

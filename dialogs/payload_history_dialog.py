from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, 
    QListWidgetItem, QPushButton, QLabel, QHBoxLayout
)
import json
import os

class PayloadHistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Payload History")
        self.resize(500, 300)

        # Список истории
        self.history = []
        self._load_history()
        self._init_ui()

    def _load_history(self):
        """Считывает data/payload_history.json → self.history (list of strings)."""
        path = os.path.join(os.path.dirname(__file__), "..", "data", "payload_history.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
                self.history = obj.get("history", [])
        except (FileNotFoundError, json.JSONDecodeError):
            self.history = []

    def _save_history(self):
        """Сохраняет текущий self.history (обрезает до 10) в JSON."""
        path = os.path.join(os.path.dirname(__file__), "..", "data", "payload_history.json")
        data = {"history": self.history[:10]}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 1) Поисковая строка
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Search history…")
        self.search.textChanged.connect(self._filter_list)
        layout.addWidget(self.search)

        # 2) Список payload-ов
        self.list_widget = QListWidget(self)
        layout.addWidget(self.list_widget)

        # 3) Кнопки Clear / Close
        btn_layout = QHBoxLayout()
        self.btn_clear = QPushButton("Clear All", self)
        self.btn_clear.clicked.connect(self._on_clear)
        btn_layout.addWidget(self.btn_clear)

        self.btn_close = QPushButton("Close", self)
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

        # заполнить список
        self._populate_list(self.history)

    def _populate_list(self, items):
        """Заполняет QListWidget строками из items."""
        self.list_widget.clear()
        for payload in items:
            QListWidgetItem(payload, self.list_widget)

    def _filter_list(self, text):
        """Фильтрует self.history по вхождению text."""
        text = text.lower()
        filtered = [p for p in self.history if text in p.lower()]
        self._populate_list(filtered)

    def _on_clear(self):
        """Очищает историю и обновляет JSON + UI."""
        self.history = []
        self._save_history()
        self._populate_list([])

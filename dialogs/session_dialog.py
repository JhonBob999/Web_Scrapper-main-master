from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox
from core import session_service

class SessionHistoryDialog(QDialog):
    def __init__(self, parent=None, load_callback=None):
        super().__init__(parent)
        self.setWindowTitle("Sessions History")
        self.resize(600, 400)
        self.load_callback = load_callback

        layout = QVBoxLayout(self)

        # Таблица сессий
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Session", "Date", "Task"])
        layout.addWidget(self.table)

        # Кнопки
        btn_layout = QHBoxLayout()

        self.load_button = QPushButton("📂 Load")
        self.load_button.clicked.connect(self.load_selected_session)
        btn_layout.addWidget(self.load_button)

        self.delete_button = QPushButton("🗑 Delete")
        self.delete_button.clicked.connect(self.delete_selected_session)
        btn_layout.addWidget(self.delete_button)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        btn_layout.addWidget(self.close_button)

        layout.addLayout(btn_layout)

        self.refresh_table()

    def refresh_table(self):
        sessions = session_service.list_sessions()
        self.table.setRowCount(len(sessions))

        for i, session in enumerate(sessions):
            self.table.setItem(i, 0, QTableWidgetItem(session["session_name"]))
            self.table.setItem(i, 1, QTableWidgetItem(session["datetime"]))
            self.table.setItem(i, 2, QTableWidgetItem(str(session["task_count"])))
            self.table.setRowHeight(i, 30)

        self.table.resizeColumnsToContents()

    def get_selected_path(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        file_name = self.table.item(row, 0).text()
        full_path = f"sessions/{file_name}.json"
        return full_path

    def load_selected_session(self):
        path = self.get_selected_path()
        if not path:
            QMessageBox.warning(self, "Error", "Choose session to load")
            return

        session = session_service.load_session(path)
        if self.load_callback:
            self.load_callback(session)
        self.accept()

    def delete_selected_session(self):
        path = self.get_selected_path()
        if not path:
            QMessageBox.warning(self, "Error", "Choose session to delete")
            return

        confirm = QMessageBox.question(self, "Accepting", "Delete choosen session?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            session_service.delete_session(path)
            self.refresh_table()
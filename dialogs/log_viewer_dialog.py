from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPlainTextEdit, QPushButton
from threads.log_tail_thread import LogTailThread

class LogViewerDialog(QDialog):
    def __init__(self, bot_id, log_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Log Viewer — {bot_id}")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout()
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)

        self.stop_btn = QPushButton("Stop Watching")
        self.stop_btn.clicked.connect(self.close)

        layout.addWidget(self.log_output)
        layout.addWidget(self.stop_btn)
        self.setLayout(layout)

        self.tail_thread = LogTailThread(log_path)
        self.tail_thread.new_line.connect(self._append_line)
        self.tail_thread.start()

    def _append_line(self, line: str):
        self.log_output.appendPlainText(line)

    def closeEvent(self, event):
        self.tail_thread.stop()
        self.tail_thread.wait()
        super().closeEvent(event)

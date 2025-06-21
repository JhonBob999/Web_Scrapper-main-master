from PyQt5.QtCore import QThread, pyqtSignal
import time
import os

class LogTailThread(QThread):
    new_line = pyqtSignal(str)

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._running = True
        self._last_position = 0

    def run(self):
        if not os.path.exists(self.file_path):
            return

        with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, os.SEEK_END)  # читаем только новые строки
            self._last_position = f.tell()

            while self._running:
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                self.new_line.emit(line)

    def stop(self):
        self._running = False

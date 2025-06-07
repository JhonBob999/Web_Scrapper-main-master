from PyQt5.QtCore import QThread, pyqtSignal

class XssRunAllThread(QThread):
    """
    QThread for running all XSS payloads without blocking the UI.
    Emits detailed logs and final results.

    Signals:
        log_entry (int, int, str, str, int, float, bool):
            idx, total, payload, url, status_code, elapsed_ms, success
        finished (list):
            list of result dicts {payload, success, status, time_ms}
    """
    # Signal with parameters: index, total, payload, url, status, elapsed_ms, success
    log_entry = pyqtSignal(int, int, str, str, int, float, bool)
    # Signal emitted when run() completes, with full results list
    finished = pyqtSignal(list)

    def __init__(self, payloads, build_url_callback, test_payload_callback, parent=None):
        """
        Initialize the thread.

        Args:
            payloads (List[str]): List of payload strings to test.
            build_url_callback (callable): Function(payload) -> url string.
            test_payload_callback (callable): Function(payload) -> (success, status_code, elapsed_ms).
            parent (QObject, optional): Parent QObject.
        """
        super().__init__(parent)
        self.payloads = payloads
        self.build_url = build_url_callback
        self.test_payload = test_payload_callback

    def run(self):
        """
        Execute the payload testing loop.
        Emits log_entry for each payload and finished at the end.
        """
        results = []
        total = len(self.payloads)

        for idx, payload in enumerate(self.payloads, start=1):
            # Build the URL for this payload
            url = self.build_url(payload)

            # Test the payload and measure success, status code, and elapsed time
            success, status, elapsed = self.test_payload(payload)

            # Store result dict
            result = {
                "payload": payload,
                "success": success,
                "status": status,
                "time_ms": elapsed
            }
            results.append(result)

            # Emit detailed log for UI
            # Note: arguments must match the pyqtSignal signature
            status_code = status if status is not None else 0
            elapsed_ms = elapsed
            self.log_entry.emit(idx, total, payload, url, status_code, elapsed_ms, success)

        # Emit final results
        self.finished.emit(results)

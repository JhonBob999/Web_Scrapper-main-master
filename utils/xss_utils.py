import os
import json
import time
import urllib.parse
import requests
from typing import List, Tuple
from PyQt5.QtWidgets import QListWidget, QTextEdit


def build_test_url(payload: str, target: str, param: str = "q") -> str:
    """
    Строит URL вида http://<target>?<param>=<encoded_payload>
    """
    encoded = urllib.parse.quote(payload)
    return f"http://{target}?{param}={encoded}"


def get_listwidget_payloads(list_widget: QListWidget) -> List[str]:
    """
    Извлекает все payload-ы из QListWidget в виде списка строк.
    """
    return [list_widget.item(i).text() for i in range(list_widget.count())]


def log_response(edit_widget: QTextEdit, idx: int, total: int,
                 payload: str, url: str, status: int,
                 elapsed: float, success: bool):
    """
    Записывает одну строку лога в QTextEdit.
    """
    edit_widget.insertPlainText(
        f"[{idx}/{total}] Payload: {payload}\n"
        f"    URL: {url}\n"
        f"    Status: {status}  Elapsed: {elapsed:.1f}ms  Success: {success}\n"
    )


def test_payload(payload: str, target: str, param: str = "q") -> Tuple[bool, int, float]:
    """
    Синхронное тестирование одного payload-а через requests.
    Возвращает (success: bool, status: int, elapsed_ms: float)
    """
    url = build_test_url(payload, target, param)
    start = time.time()
    try:
        resp = requests.get(url, timeout=10)
        elapsed = (time.time() - start) * 1000
        success = (resp.status_code == 200 and payload in resp.text)
        return success, resp.status_code, elapsed
    except Exception:
        return False, None, (time.time() - start) * 1000


def get_history_path() -> str:
    """
    Возвращает путь до файла с историей payload-ов.
    """
    return os.path.join(os.path.dirname(__file__), "..", "data", "payload_history.json")


def load_payload_history() -> List[str]:
    """
    Загружает историю payload-ов из JSON.
    """
    try:
        with open(get_history_path(), "r", encoding="utf-8") as f:
            return json.load(f).get("history", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_payload_history(history: List[str]):
    """
    Сохраняет историю (макс. 10 записей) в JSON.
    """
    data = {"history": history[:10]}
    with open(get_history_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_to_payload_history(payload: str):
    """
    Добавляет новый payload в историю (без дубликатов).
    """
    history = load_payload_history()
    if payload in history:
        history.remove(payload)
    history.insert(0, payload)
    save_payload_history(history)

import json
from pathlib import Path

# Сопоставление контекста с файлом
CONTEXT_FILES = {
    "html_body": "assets/cheatsheet/xss_htmlbody.json",
    "attribute": "assets/cheatsheet/xss_attribute.json",
    "js": "assets/cheatsheet/xss_js.json",
    "url_param": "assets/cheatsheet/xss_urlparam.json",
    "dom": "assets/cheatsheet/xss_dom.json"
}

def load_xss_payloads(context):
    """
    Загружает XSS payload-ы для выбранного контекста.
    :param context: Один из html_body, attribute, js, url_param, dom
    :return: Список словарей с payload и desc, либо пустой список
    """
    file_path = CONTEXT_FILES.get(context)
    if not file_path or not Path(file_path).exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            payloads = json.load(f)
        except Exception as e:
            print(f"[XSS] Failed to load {file_path}: {e}")
            return []
    return payloads

# Пример использования (можно удалить или оставить для дебага)
if __name__ == "__main__":
    test_payloads = load_xss_payloads("html_body")
    for p in test_payloads:
        print(p["payload"], "-", p["desc"])

import os, re
import hashlib
import requests
from urllib.parse import urlparse, urljoin

def download_js_file(js_url, save_dir, base_url):
    try:
        full_url = urljoin(base_url, js_url)
        response = requests.get(full_url, timeout=10)

        if not response.ok:
            print(f"[Download Error] {js_url} → {response.status_code}")
            return None

        # Определяем домен
        domain = urlparse(base_url).netloc or "unknown_domain"

        # Создаём поддиректорию для домена
        domain_dir = os.path.join(save_dir, domain)
        os.makedirs(domain_dir, exist_ok=True)

        # Оригинальное имя файла
        file_name = os.path.basename(js_url)
        if not file_name.endswith(".js"):
            file_name += ".js"

        # Добавим уникальный префикс по хешу URL
        url_hash = hashlib.md5(js_url.encode("utf-8")).hexdigest()[:8]
        unique_name = f"{url_hash}__{file_name}"

        save_path = os.path.join(domain_dir, unique_name)

        with open(save_path, "wb") as f:
            f.write(response.content)

        print(f"[Downloaded] {file_name} → {save_path}")
        return save_path

    except Exception as e:
        print(f"[Download Error] {js_url} → {e}")
        return None

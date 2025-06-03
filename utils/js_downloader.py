import os, re
import requests
from urllib.parse import urlparse, urljoin

def download_js_file(js_url, save_dir, base_url):
    try:
        full_url = urljoin(base_url, js_url)
        response = requests.get(full_url, timeout=10)

        if not response.ok:
            print(f"[Download Error] {js_url} → {response.status_code}")
            return None

        file_name = os.path.basename(js_url)
        if not file_name.endswith(".js"):
            file_name += ".js"

        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, file_name)

        with open(save_path, "wb") as f:
            f.write(response.content)

        return save_path

    except Exception as e:
        print(f"[Download Error] {js_url} → {e}")
        return None

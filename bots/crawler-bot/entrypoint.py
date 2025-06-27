import os
import json
import time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from datetime import datetime

visited = set()
crawl_result = {}

def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def log(msg: str):
    with open("logs.txt", "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{timestamp} {msg}\n")

def is_internal(link, base_netloc):
    parsed = urlparse(link)
    return parsed.netloc == "" or parsed.netloc == base_netloc

def save_crawl_result():
    try:
        with open("crawl_result.json", "w", encoding="utf-8") as f:
            json.dump(crawl_result, f, indent=2)
        log("[INFO] Intermediate result saved.")
    except Exception as e:
        log(f"[ERROR] Failed to save crawl result: {e}")

def crawl(url, base_url, base_netloc, depth, config):
    if depth < 0 or url in visited:
        return

    visited.add(url)

    if config.get("log_options", {}).get("requests", False):
        log(f"[REQ] GET {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        log(f"[ERROR] Failed to fetch {url}: {e}")
        return

    if config.get("log_options", {}).get("responses", False):
        log(f"[RESP] {response.status_code} {url}")

    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        link = urljoin(url, a["href"])
        if is_internal(link, base_netloc):
            links.append(link)

    page_key = url.replace(base_url, "") or "/"
    crawl_result.setdefault(base_url, {}).setdefault(page_key, [])

    for link in links:
        path = link.replace(base_url, "")
        if path not in crawl_result[base_url][page_key]:
            crawl_result[base_url][page_key].append(path)

    save_crawl_result()

    for link in links:
        crawl(link, base_url, base_netloc, depth - 1, config)

def main():
    config = load_config()
    target = config.get("target")
    depth = config.get("depth", 2)
    if not target:
        log("[ERROR] No target URL specified in config.json")
        return

    parsed_url = urlparse(target)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    base_netloc = parsed_url.netloc

    log(f"[INFO] Starting crawl at {target} with depth={depth}")
    crawl(target, base_url, base_netloc, depth, config)
    log("[INFO] Crawl finished. Final result already saved.")

if __name__ == "__main__":
    main()

# bots/crawler-bot/entrypoint.py

import os
import json
import time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

visited = set()
crawl_result = {}

def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def is_internal(link, base_netloc):
    parsed = urlparse(link)
    return parsed.netloc == "" or parsed.netloc == base_netloc

def crawl(url, base_url, base_netloc, depth):
    if depth < 0 or url in visited:
        return

    visited.add(url)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url} — {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        link = urljoin(url, a["href"])
        if is_internal(link, base_netloc):
            links.append(link)

    crawl_result.setdefault(base_url, {}).setdefault(url.replace(base_url, "") or "/", [])
    for link in links:
        path = link.replace(base_url, "")
        if path not in crawl_result[base_url][url.replace(base_url, "") or "/"]:
            crawl_result[base_url][url.replace(base_url, "") or "/"].append(path)

    for link in links:
        crawl(link, base_url, base_netloc, depth - 1)

def main():
    config = load_config()
    target = config.get("target")
    depth = config.get("depth", 2)
    if not target:
        print("[ERROR] No target URL specified in config.json")
        return

    parsed_url = urlparse(target)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    base_netloc = parsed_url.netloc

    print(f"[INFO] Starting crawl at {target} with depth={depth}")
    crawl(target, base_url, base_netloc, depth)

    with open("crawl_result.json", "w", encoding="utf-8") as f:
        json.dump(crawl_result, f, indent=2)
    print("[INFO] Crawl finished. Result saved to crawl_result.json")

if __name__ == "__main__":
    main()

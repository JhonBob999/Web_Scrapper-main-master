import requests, json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

import os

# ⬇️ Укажи здесь свой ключ (можно в .env позже)
NVD_API_KEY = os.getenv("NVD_API_KEY")
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cve/1.0/"
CACHE_DIR = os.path.join("data", "cve_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def get_cve_details(cve_id):
    # Проверка кеша
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"{cve_id}.json")

    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # Запрос к NVD API
    headers = {
        "apiKey": NVD_API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    }

    url = f"{NVD_API_URL}{cve_id}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data
    else:
        print(f"[NVD] Error {response.status_code}: {response.text}")
        return None
    
def get_cve_from_github_graphql(cve_id):
    # 1. Попытка загрузить из кэша
    cached = load_github_cache(cve_id)
    if cached:
        return transform_graphql_data(cached)

    # 2. Если нет — делаем запрос
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    query = """
    query($cveId: String!) {
      securityAdvisories(first: 1, identifier: {type: CVE, value: $cveId}) {
        nodes {
          ghsaId
          summary
          severity
          publishedAt
          references {
            url
          }
          identifiers {
            type
            value
          }
        }
      }
    }
    """

    variables = {"cveId": cve_id}
    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)

    if response.status_code == 200:
        json_data = response.json()
        advisories = json_data.get("data", {}).get("securityAdvisories", {}).get("nodes", [])
        if advisories:
            # 3. Сохраняем оригинальный JSON в кэш
            save_github_cache(cve_id, advisories[0])
            return transform_graphql_data(advisories[0])
        else:
            print(f"[GitHub GraphQL] No data found for {cve_id}")
    else:
        print(f"[GitHub GraphQL] Error {response.status_code}: {response.text}")
    return None


def transform_graphql_data(entry):
    return {
        "cve": {
            "CVE_data_meta": {
                "ID": next((id["value"] for id in entry["identifiers"] if id["type"] == "CVE"), "Unknown")
            },
            "description": {
                "description_data": [
                    {
                        "lang": "en",
                        "value": entry.get("summary", "No description")
                    }
                ]
            },
            "references": {
                "reference_data": [
                    {"url": ref.get("url")} for ref in entry.get("references", [])
                ]
            },
            "problemtype": {
                "problemtype_data": [
                    {
                        "description": [
                            {"lang": "en", "value": entry.get("ghsaId", "GHSA-???")}
                        ]
                    }
                ]
            }
        },
        "impact": {
            "baseMetricV3": {
                "cvssV3": {
                    "baseScore": None,
                    "baseSeverity": entry.get("severity", "UNKNOWN").capitalize(),
                    "vectorString": None,
                    "attackVector": None,
                    "privilegesRequired": None,
                    "userInteraction": None,
                    "scope": None
                }
            }
        }
    }
    
def save_github_cache(cve_id, data):
    path = os.path.join(CACHE_DIR, f"{cve_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_github_cache(cve_id):
    path = os.path.join(CACHE_DIR, f"{cve_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

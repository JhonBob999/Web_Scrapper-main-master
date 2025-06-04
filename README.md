# 🛡️ Web_Scrapper — Universal Web Scraper & Security Scanner (PyQt5)

**Web_Scrapper** is a powerful all-in-one desktop tool for web data extraction and basic security assessment.  
Built with **PyQt5**, it combines a flexible scraping task manager, subdomain and DNS scanner, JavaScript and CVE analysis — all within a modern, interactive GUI.

---

## 🚀 Key Features

- **Task Table Interface:**  
  Visual task manager with bulk execution, status tracking, and custom parameters for each job.
- **Flexible Scraping:**  
  Supports CSS/XPath selectors, editable headers, proxy, user-agent, cookies, and request scheduling.
- **Session Management:**  
  Save and load scraper sessions for quick project restarts.
- **Export Options:**  
  Export results to CSV, JSON, Excel. Preview and analyze results before exporting.
- **Subdomain & DNS Scanning:**  
  Integrated scanners for subdomains, DNS records, SSL certificates, and HTTP headers.
- **JavaScript Analysis:**  
  Extract and analyze JS files for known vulnerabilities (Retire.js integration).
- **CVE Lookup Module:**  
  View details about discovered CVEs via NVD and GitHub APIs, with local caching.
- **XSS Cheatsheet:**  
  Built-in, interactive reference for XSS payloads and testing techniques.
- **Data Visualization:**  
  Built-in charts, vulnerability maps, and task calendar (bar, pie, line, calendar view).
- **Modern PyQt5 GUI:**  
  Tabbed interface: Scraper | Scanner | CVE Analysis | Exploits | Settings
- **Extensible Architecture:**  
  Designed for future expansion: exploits, plugin system, CLI mode, and integrations.

---

## 📁 Project Structure

core/ # Scraping, scanning, exporting, session & task logic
ui/ # PyQt5 UI logic and table management
dialogs/ # Modal dialogs: params, timer, CVE, XSS, results, etc.
utils/ # Utilities: context menu, file helpers, logics
assets/ # Cheat sheets, sample data
data/ # All scan, export and cache data (auto-created)
main.py # Main app entry point
scraper_app.py # Main window & app logic

---

## 🖥️ How to Run

```bash
pip install -r requirements.txt
python main.py


📝 Roadmap
 Unified table-based scraping & scanning

 Subdomain, DNS, certificate, and HTTP scanning

 JavaScript & CVE analysis modules

 Data export and reporting

 Exploit/test modules (in progress)

 Plugin system and API integrations (planned)

 CLI mode (planned)
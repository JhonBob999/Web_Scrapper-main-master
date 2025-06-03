import json
import aiohttp, asyncio
import threading
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QTreeWidgetItem,QFileDialog
from PyQt5.QtGui import QColor
from utils.scanner_utils.async_worker import AsyncWorker

CRT_SH_SEARCH_URL = "https://crt.sh/?q=%.{domain}"
CRT_SH_CERT_URL = "https://crt.sh/?id={cert_id}"

stop_event = threading.Event()

###### PARSER FOR GETTING CERTIFICATES ID FROM DOMAIN/SUBDOMAIN CRT.SH  #############
###### PARSER FOR GETTING CERTIFICATES ID FROM DOMAIN/SUBDOMAIN CRT.SH  #############

async def fetch_certificate_ids(domain, log_callback=None):
    """Асинхронная функция для получения ID сертификатов."""
    try:
        if not isinstance(domain, str):
            raise ValueError("Expected a string but got a different data type")

        domain = domain.split(" ")[0]  # Удаляем IP-адреса и оставляем только домен

        url = CRT_SH_SEARCH_URL.format(domain=domain)
        if log_callback:
            log_callback(f"URL to request certificates: {url}", "blue")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    raise Exception(f"Failed to request crt.sh: {response.status}")

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Находим вторую таблицу, содержащую вложенную третью таблицу
                certificates_table = None
                tables = soup.find_all("table")
                if len(tables) >= 2:
                    certificates_table = tables[1].find("table")

                if not certificates_table:
                    if log_callback:
                        log_callback(f"Unable to find certificate table for domain {domain}", "red")
                    return {}

                cert_ids = []
                rows = certificates_table.find_all("tr")
                if not rows or len(rows) <= 1:
                    if log_callback:
                        log_callback(f"Certificate table is empty or missing for domain {domain}", "red")
                    return {}

                for row in rows[1:]:  # Пропускаем заголовок таблицы
                    cert_td = row.find("td", style="text-align:center")
                    if cert_td:
                        cert_link = cert_td.find("a")
                        if cert_link:
                            cert_ids.append(cert_link.text.strip())

                if log_callback:
                    log_callback(f"Finded {len(cert_ids)} certificates for domains {domain}", "green")

                return {domain: cert_ids if cert_ids else []}

    except Exception as e:
        if log_callback:
            log_callback(f"Error getting certificates for domain {domain}: {e}", "red")
        return {}

##### PARSING CERTIFICATE FULL INFO FROM JSON FILE TO TREEWIDGET ###########
##### PARSING CERTIFICATE FULL INFO FROM JSON FILE TO TREEWIDGET ###########

async def fetch_certificate_details(cert_id, log_callback=None):
    """Асинхронная функция для получения деталей сертификата."""
    try:
        if not isinstance(cert_id, str):
            raise ValueError("Expected a string but got a different data type")

        url = CRT_SH_CERT_URL.format(cert_id=cert_id)
        if log_callback:
            log_callback(f"URL to request certificate details: {url}", "blue")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    raise Exception(f"Error getting certificates {response.status}")

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                cert_data = soup.find("td", class_="text")

                if not cert_data:
                    if log_callback:
                        log_callback(f"Unable to find certificate {cert_id}", "red")
                    return {}

                certificate_details = cert_data.text.strip()
                if log_callback:
                    log_callback(f"Data for certificates {cert_id} successfully received.", "green")

                return {"id": cert_id, "details": certificate_details}

    except Exception as e:
        if log_callback:
            log_callback(f"Error getting certificates {cert_id}: {e}", "red")
        return None # Вместо return {}

###### FUNCTION RESPONSIBLE FOR ANALYZE CERTIFICATE ID #############
###### FUNCTION RESPONSIBLE FOR ANALYZE CERTIFICATE ID #############

async def analyze_certificates_via_crtsh_async(active_subdomains, log_callback=None, progress_callback=None):
    """Асинхронная функция для анализа сертификатов."""
    if not isinstance(active_subdomains, dict):
        raise ValueError("Expected a subdomain dictionary but got a different data type")
    
    all_certificates = {}

    total_domains = sum(len(subdomains) for subdomains in active_subdomains.values())
    processed_domains = 0

    for domain, subdomains in active_subdomains.items():
        if not isinstance(subdomains, list):
            if log_callback:
                log_callback(f"Invalid data format missing for domain {domain}", "orange")
            continue

        for subdomain in subdomains:
            if stop_event.is_set():
                if log_callback:
                    log_callback("Scanning stopped by user.", "orange")
                return all_certificates

            if not isinstance(subdomain, str):
                if log_callback:
                    log_callback(f"Invalid subdomain missing: {subdomain}", "orange")
                continue

            subdomain = subdomain.split(" ")[0]  # Удаляем IP-адреса
            cert_ids = await fetch_certificate_ids(subdomain, log_callback=log_callback)
            if cert_ids:
                all_certificates[subdomain] = cert_ids.get(subdomain, [])
            # Обновление прогресса
            processed_domains += 1
            if progress_callback:
                progress = int((processed_domains / total_domains) * 100)
                progress_callback(progress)

    return all_certificates

###### START ASYNCRON SCAN IN SERTIFICATES #######
###### START ASYNCRON SCAN IN SERTIFICATES #######


def analyze_certificates_via_crtsh(active_subdomains, log_callback=None, progress_callback=None):
    """Запускает асинхронное сканирование сертификатов."""
    async def _analyze():
        return await analyze_certificates_via_crtsh_async(active_subdomains, log_callback, progress_callback)

    worker = AsyncWorker(_analyze())
    worker.finished.connect(lambda result: print(result))  # Обработка результата
    worker.error.connect(lambda e: print(f"ERROR: {e}"))  # Обработка ошибок
    worker.start()


###### LOAD JSON CERTIFICATE FILE FROM pushButtonAllCert TO TREEWIDGETFILES #############
###### LOAD JSON CERTIFICATE FILE FROM pushButtonAllCert TO TREEWIDGETFILES #############

def load_certificate_file(file_path, log_callback=None):
    """Загружает файл сертификатов в формате JSON."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            if not isinstance(data, dict):
                raise ValueError("The file must contain a data dictionary.")

            if log_callback:
                log_callback(f"File {file_path} successfully loaded. Data type: Dictionary", "green")

            return data

    except Exception as e:
        if log_callback:
            log_callback(f"File download error {file_path}: {e}", "red")
        raise
    

        
##### CHECK IF JSON FILE IS VALID TO SHOW IN TREEWIDGETDOMAIN #######
##### CHECK IF JSON FILE IS VALID TO SHOW IN TREEWIDGETDOMAIN #######
        
def load_and_validate_json(file_path):
    """Загружает и проверяет структуру JSON-файла."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Проверяем структуру JSON
        required_keys = ["active_subdomains", "inactive_subdomains", "domains"]
        if not isinstance(data.get("active_subdomains"), list) or \
        not isinstance(data.get("inactive_subdomains"), list) or \
        not isinstance(data.get("domains"), list):
            raise ValueError("The structure of the JSON file is incorrect!")

        return data
    except Exception as e:
        raise ValueError(f"Error while processing JSON: {e}")
    
##### FILL TREEWIDGETDOMAIN WITH DATA FROM JSON #######
##### FILL TREEWIDGETDOMAIN WITH DATA FROM JSON #######

def populate_tree_with_json(data, tree_widget):
    """Заполняет TreeWidget данными из JSON."""
    tree_widget.clear()

    # Обрабатываем активные поддомены
    active_item = QTreeWidgetItem(tree_widget)
    active_item.setText(0, "Active Subdomains")
    active_item.setForeground(0, QColor("green"))

    for sub in data.get("active_subdomains", []):
        sub_item = QTreeWidgetItem(active_item)
        sub_item.setText(0, sub["subdomain"])
        sub_item.setForeground(0, QColor("purple"))

        ip_item = QTreeWidgetItem(sub_item)
        ip_item.setText(0, f"IP: {sub['ip']}")
        ip_item.setForeground(0, QColor("blue"))

        status_item = QTreeWidgetItem(sub_item)
        status_item.setText(0, f"Status Code: {sub['status_code']}")
        status_item.setForeground(0, QColor("darkblue"))

    # Обрабатываем неактивные поддомены
    inactive_item = QTreeWidgetItem(tree_widget)
    inactive_item.setText(0, "Inactive Subdomains")
    inactive_item.setForeground(0, QColor("red"))

    for sub in data.get("inactive_subdomains", []):
        sub_item = QTreeWidgetItem(inactive_item)
        sub_item.setText(0, sub)
        sub_item.setForeground(0, QColor("darkred"))

    # Обрабатываем домены
    domains_item = QTreeWidgetItem(tree_widget)
    domains_item.setText(0, "Domains")
    domains_item.setForeground(0, QColor("purple"))

    for domain in data.get("domains", []):
        domain_item = QTreeWidgetItem(domains_item)
        domain_item.setText(0, domain)
        
        
##### SAVING PARSED CERTIFICATES ID FROM DOMAIN/SUBDOMAIN FOR TREEWIDGETDOMAIN #######
##### SAVING PARSED CERTIFICATES ID FROM DOMAIN/SUBDOMAIN FOR TREEWIDGETDOMAIN #######

def save_certificates_to_treewidget_domain(data, log_callback=None):
    """
    Сохраняет сертификаты в JSON-файл в определённом формате:
    """
    try:
        # Открыть диалог для выбора файла сохранения
        file_path, _ = QFileDialog.getSaveFileName(
            None, "Save Certificate", "", "JSON Files (*.json)"
        )
        if not file_path:
            if log_callback:
                log_callback("Saving cancaled by user.", "orange")
            return

        # Проверка формата данных
        if not isinstance(data, dict) or not all(isinstance(v, list) and all(isinstance(i, str) for i in v) for v in data.values()):
            raise ValueError("Incorrect data format. Expected a dictionary with domains and certificate ID lists.")

        # Сохранение данных в файл
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        if log_callback:
            log_callback(f"Certificates successfully saved to file: {file_path}", "green")
    except Exception as e:
        if log_callback:
            log_callback(f"Error saving certificates: {e}", "red")
        raise
    
    
###### SET UP COLOR FOR TREEWIDGET #############
###### SET UP COLOR FOR TREEWIDGET #############
   
def set_tree_item_color(item, color):
    """Изменяет цвет текста элемента QTreeWidget и всех его дочерних элементов."""
    item.setForeground(0, color)
    for i in range(item.childCount()):
        child = item.child(i)
        set_tree_item_color(child, color)
    if item is None:
        return
        
          
#### STOP SCAN #######
#### STOP SCAN #######

def stop_scanning():
    """Устанавливает флаг остановки сканирования."""
    stop_event.set()


#### CLEAR LOGS #######
#### CLEAR LOGS #######

def clear_logs(log_widget):
    """Очищает содержимое логов."""
    log_widget.clear()
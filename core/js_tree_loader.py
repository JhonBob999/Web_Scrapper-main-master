import json
from PyQt5.QtWidgets import QTreeWidgetItem, QApplication
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt

def load_domain_tree(tree_widget, json_path):
    """
    Загружает структуру поддоменов и JS-файлов из JSON и отображает в QTreeWidget.
    """
    tree_widget.clear()

    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except Exception as e:
        print(f"[ERROR] Failed to load JSON: {e}")
        return

    for sub in data.get("subdomains", []):
        sub_item = QTreeWidgetItem([sub.get("name", "unknown-subdomain")])
        for script in sub.get("scripts", []):
            script_item = QTreeWidgetItem([script.get("filename", "unnamed.js")])

            # Добавляем базовую информацию как дочерние элементы
            if "version" in script:
                script_item.addChild(QTreeWidgetItem([f"version: {script['version']}"]))
            if "library" in script:
                script_item.addChild(QTreeWidgetItem([f"library: {script['library']}"]))
            if "dangerous_functions" in script:
                for func in script["dangerous_functions"]:
                    script_item.addChild(QTreeWidgetItem([f"danger: {func}"]))
            if "cves" in script:
                for cve in script["cves"]:
                    script_item.addChild(QTreeWidgetItem([f"CVE: {cve}"]))

            sub_item.addChild(script_item)

        tree_widget.addTopLevelItem(sub_item)
        
def load_js_tree_from_bot(js_data: list, config: dict, controller):
    """
    Если js_data — это просто список JS-файлов (list), то показываем их под общим доменом
    """
    controller.ui.tree_domain.clear()

    domain_item = QTreeWidgetItem(["Collected JS Files"])
    for js_url in js_data:
        js_item = QTreeWidgetItem([js_url])
        domain_item.addChild(js_item)

    controller.ui.tree_domain.addTopLevelItem(domain_item)
    controller.ui.tree_domain.expandAll()

    # Установим target
    target = config.get("target", "")
    controller.ui.lineEditXssTarget.setText(target)

    # Установим headers
    headers = config.get("headers", {})
    if hasattr(controller, "session_headers"):
        controller.session_headers = headers
    elif hasattr(controller, "set_headers"):
        controller.set_headers(headers)




import os
import json
from PyQt5.QtWidgets import QMessageBox
from dialogs.js_selection_dialog import JsSelectionDialog
from core.js_tree_loader import load_js_tree_from_bot


def analyze_js_from_bot(item, parent_widget):
    bot_id = item.text(1)
    bot_path = os.path.join("data", "bots", bot_id)
    js_path = os.path.join(bot_path, "extra_data", "js_list.json")
    config_path = os.path.join(bot_path, "config.json")

    if not os.path.exists(js_path):
        QMessageBox.warning(parent_widget, "JS List Not Found", f"No js_list.json found for bot {bot_id}.")
        return

    try:
        with open(js_path, "r", encoding="utf-8") as f:
            js_data = json.load(f)
    except Exception as e:
        QMessageBox.warning(parent_widget, "Error", f"Failed to read js_list.json:\n{e}")
        return

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
    except Exception:
        config_data = {}

    target = config_data.get("target", "unknown.local")
    base_url = target if target.startswith("http") else f"http://{target}"

    if isinstance(js_data, list):
        domain = target.replace("http://", "").replace("https://", "").split("/")[0]
        js_urls = js_data
    elif isinstance(js_data, dict):
        domain, js_urls = next(iter(js_data.items()))
    else:
        QMessageBox.warning(parent_widget, "JS Format Error", "Invalid format in js_list.json")
        return

    dialog = JsSelectionDialog(domain=domain, js_urls=js_urls, base_url=base_url, parent=parent_widget)
    dialog.exec_()


def send_to_js_analyzer(item, xss_controller, parent_widget):
    bot_id = item.text(1)
    bot_path = os.path.join("data", "bots", bot_id)

    config_path = os.path.join(bot_path, "config.json")
    js_list_path = os.path.join(bot_path, "extra_data", "js_list.json")

    if not os.path.exists(js_list_path):
        QMessageBox.warning(parent_widget, "JS List Not Found", f"No js_list.json found for bot {bot_id}.")
        return

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
    except Exception as e:
        QMessageBox.warning(parent_widget, "Config Load Error", f"Failed to load config.json: {e}")
        return

    try:
        with open(js_list_path, "r", encoding="utf-8") as f:
            js_list = json.load(f)
    except Exception as e:
        QMessageBox.warning(parent_widget, "JS List Load Error", f"Failed to load js_list.json: {e}")
        return

    load_js_tree_from_bot(js_list, config_data, xss_controller)

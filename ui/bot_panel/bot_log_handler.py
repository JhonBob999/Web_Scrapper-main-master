import os
import json
import html
import re
from PyQt5.QtWidgets import QMessageBox


def handle_pause_logs(timer):
    timer.stop()
    print("[LOG] Log updates paused.")
    
def handle_load_log_interface(ui, bot_id, start_log_monitoring_callback):
    if not bot_id:
        QMessageBox.warning(ui, "No Selection", "Please select a bot.")
        return

    load_log_options(ui, bot_id)
    start_log_monitoring_callback(bot_id)



def handle_resume_logs(timer, current_log_path, parent):
    if current_log_path and os.path.exists(current_log_path):
        timer.start()
        print("[LOG] Log updates resumed.")
    else:
        QMessageBox.warning(parent, "Log File Missing", "No log file is currently selected or it was deleted.")


def load_log_options(ui, bot_id: str):
    config_path = f"data/bots/{bot_id}/config.json"
    if not os.path.exists(config_path):
        return

    with open(config_path, "r") as f:
        config = json.load(f)
        log_opts = config.get("log_options", {})

    ui.chkLogRequests.setChecked(log_opts.get("requests", True))
    ui.chkLogResponses.setChecked(log_opts.get("responses", True))
    ui.chkLogConsole.setChecked(log_opts.get("console", False))
    ui.chkLogDockerEvents.setChecked(log_opts.get("docker", False))


def save_log_options(ui, bot_id: str):
    config_path = f"data/bots/{bot_id}/config.json"
    if not os.path.exists(config_path):
        return

    with open(config_path, "r") as f:
        config = json.load(f)

    config["log_options"] = {
        "requests": ui.chkLogRequests.isChecked(),
        "responses": ui.chkLogResponses.isChecked(),
        "console": ui.chkLogConsole.isChecked(),
        "docker": ui.chkLogDockerEvents.isChecked()
    }

    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)


def handle_log_checkbox_changed(ui, get_selected_bot_id):
    bot_id = get_selected_bot_id()
    if not bot_id:
        return

    save_log_options(ui, bot_id)
    print(f"[LOG] log_options updated for {bot_id}")


def handle_log_search(ui, current_log_path, search_text):
    if not current_log_path or not os.path.exists(current_log_path):
        return

    try:
        with open(current_log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        search_text = search_text.strip().lower()
        ui.plainText_botLogs.clear()

        match_count = 0

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            if "[REQ]" in line_clean and not ui.chkLogRequests.isChecked():
                continue
            if "[RESP]" in line_clean and not ui.chkLogResponses.isChecked():
                continue
            if "[JS]" in line_clean and not ui.chkLogConsole.isChecked():
                continue
            if "[DOCKER]" in line_clean and not ui.chkLogDockerEvents.isChecked():
                continue

            if search_text and search_text not in line_clean.lower():
                continue

            match_count += 1

            # Цветовая подсветка
            if "[REQ]" in line_clean:
                color = "#3498db"
            elif "[RESP]" in line_clean:
                color = "#2ecc71"
            elif "[JS]" in line_clean:
                color = "#f1c40f"
            elif "[DOCKER]" in line_clean:
                color = "#e67e22"
            else:
                color = "#bdc3c7"

            highlighted = highlight_search_text(line_clean, search_text)
            html_line = f'<div style="color:{color}; margin-bottom:2px;">{highlighted}</div>'
            ui.plainText_botLogs.appendHtml(html_line)

        ui.lcdMatchesFound.display(match_count)

    except Exception as e:
        print(f"[SEARCH ERROR] Failed to filter logs: {e}")
        ui.lcdMatchesFound.display(0)


def highlight_search_text(text, keyword):
    if not keyword:
        return html.escape(text)

    pattern = re.escape(keyword)
    matches = list(re.finditer(pattern, text.lower()))
    last_idx = 0
    result = ""

    for match in matches:
        start, end = match.span()
        result += html.escape(text[last_idx:start])
        result += f'<span style="background-color: yellow;">{html.escape(text[start:end])}</span>'
        last_idx = end

    result += html.escape(text[last_idx:])
    return result


def update_bot_logs(ui, current_log_path):
    if not current_log_path or not os.path.exists(current_log_path):
        return

    try:
        with open(current_log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        ui.lcdTotalLines.display(len(lines))
        ui.plainText_botLogs.clear()

        req_count = 0
        resp_count = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if "[REQ]" in line:
                req_count += 1
            if "[RESP]" in line:
                resp_count += 1

            if "[REQ]" in line and not ui.chkLogRequests.isChecked():
                continue
            if "[RESP]" in line and not ui.chkLogResponses.isChecked():
                continue
            if "[JS]" in line and not ui.chkLogConsole.isChecked():
                continue
            if "[DOCKER]" in line and not ui.chkLogDockerEvents.isChecked():
                continue

            color = "#3498db" if "[REQ]" in line else \
                    "#2ecc71" if "[RESP]" in line else \
                    "#f1c40f" if "[JS]" in line else \
                    "#e67e22" if "[DOCKER]" in line else "#bdc3c7"

            html_line = f'<div style="color:{color}; margin-bottom:2px;">{html.escape(line)}</div>'
            ui.plainText_botLogs.appendHtml(html_line)

        ui.lcdReqCount.display(req_count)
        ui.lcdRespCount.display(resp_count)

    except Exception as e:
        print(f"[LOG ERROR] Failed to read logs.txt: {e}")

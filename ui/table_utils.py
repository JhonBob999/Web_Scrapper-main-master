from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QTableWidgetItem, QPushButton


# === LCD + ЦВЕТ ===

def update_lcd_counters(table, lcds):
    total = table.rowCount()
    running = count_status(table, "⏳ In progress")
    success = count_status(table, "✅ Successfully")
    error = count_status(table, "❌ Error")
    stopped = count_status(table, "⏸️ Stopped")

    lcds['total'].display(total)
    lcds['running'].display(running)
    lcds['success'].display(success)
    lcds['error'].display(error)
    lcds['stopped'].display(stopped)
    
    # 🔥 Добавляем окраску строк
    for row in range(table.rowCount()):
        colorize_row_by_status(table, row)

def count_status(table, status_text):
    count = 0
    for row in range(table.rowCount()):
        item = table.item(row, 4)
        if item and item.text() == status_text:
            count += 1
    return count

def colorize_row_by_status(table, row):
    status_item = table.item(row, 4)
    if not status_item:
        return

    status = status_item.text().strip()
    color = QColor("white")  # Default

    if "✅" in status:
        color = QColor("lightgreen")
    elif "❌" in status:
        color = QColor("lightcoral")
    elif "⏳" in status:
        color = QColor("lightyellow")
    elif "⏸" in status:
        color = QColor("lightgray")

    for col in range(table.columnCount()):
        item = table.item(row, col)
        if item:
            item.setBackground(color)
            
# === ДОБАВЛЕНИЕ / УДАЛЕНИЕ ===
            
def add_task_row(table, url, selector, method, status):
    row_position = table.rowCount()
    table.insertRow(row_position)

    table.setItem(row_position, 0, QTableWidgetItem(str(row_position + 1)))  # №
    table.setItem(row_position, 1, QTableWidgetItem(url))                   # URL
    table.setItem(row_position, 2, QTableWidgetItem(selector))             # Selector
    table.setItem(row_position, 3, QTableWidgetItem(method))               # Method
    table.setItem(row_position, 4, QTableWidgetItem(status))               # Status
    table.setItem(row_position, 5, QTableWidgetItem("..."))                # Action placeholder
    table.setItem(row_position, 8, QTableWidgetItem("🛠 Tune"))

    # ❗ Важно: Кнопку сохранения добавляет ScraperApp
    # через table.setCellWidget(row, 6, create_save_button())
     # 🔄 Автоматическая ширина колонок по содержимому
    for col in range(table.columnCount()):
        table.resizeColumnToContents(col)

def delete_selected_row(table):
    selected = table.currentRow()
    if selected >= 0:
        table.removeRow(selected)
        renumber_tasks(table)

def renumber_tasks(table):
    for i in range(table.rowCount()):
        table.setItem(i, 0, QTableWidgetItem(str(i + 1)))

def create_save_button():
    return QPushButton("💾 Save")

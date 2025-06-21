from PyQt5.QtWidgets import QMenu, QAction

def open_bot_context_menu(parent, tree_widget, position, callbacks: dict):
    
    item = tree_widget.itemAt(position)
    if not item:
        return

    menu = QMenu(parent)

    action_start = QAction("Start Bot", parent)
    action_stop = QAction("Stop Bot", parent)
    action_config = QAction("Configure Bot", parent)
    action_save = QAction("Save as Profile", parent)
    action_load = QAction("Load Profile", parent)
    action_rename = QAction("Rename Bot", parent)
    action_log = QAction("View Logs", parent)

    # Привязываем действия
    action_start.triggered.connect(lambda: callbacks["launch"](item))
    action_stop.triggered.connect(lambda: callbacks["stop"](item))
    action_config.triggered.connect(lambda: callbacks["configure"](item))
    action_save.triggered.connect(lambda: callbacks["save_profile"](item))
    action_load.triggered.connect(lambda: callbacks["load_profile"](item))
    action_rename.triggered.connect(lambda: callbacks["rename"](item))
    action_log.triggered.connect(lambda: callbacks["view_logs"](item))

    # Добавляем в меню
    menu.addAction(action_start)
    menu.addAction(action_stop)
    menu.addSeparator()
    menu.addAction(action_config)
    menu.addAction(action_save)
    menu.addAction(action_load)
    menu.addAction(action_rename)
    menu.addAction(action_log)

    # Показываем меню
    menu.exec_(tree_widget.viewport().mapToGlobal(position))

from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtCore import Qt

def setup_crawler_context_menu(tree_widget):
    def show_context_menu(position):
        menu = QMenu()

        expand_action = QAction("Expand All", tree_widget)
        collapse_action = QAction("Collapse All", tree_widget)

        expand_action.triggered.connect(tree_widget.expandAll)
        collapse_action.triggered.connect(tree_widget.collapseAll)

        menu.addAction(expand_action)
        menu.addAction(collapse_action)

        menu.exec_(tree_widget.viewport().mapToGlobal(position))

    tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
    tree_widget.customContextMenuRequested.connect(show_context_menu)

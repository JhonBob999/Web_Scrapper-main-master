# core/crawler_view_loader.py

import os
import json
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtGui import QBrush, QColor

def load_crawl_result(bot_id, tree_widget):
    tree_widget.clear()
    
    path = f"data/bots/{bot_id}/crawl_result.json"
    if not os.path.exists(path):
        return False

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for base_url, paths in data.items():
        root_item = QTreeWidgetItem([base_url])
        tree_widget.addTopLevelItem(root_item)

        if isinstance(paths, dict):
            for sub_path, sub_links in paths.items():
                sub_item = QTreeWidgetItem([sub_path])
                root_item.addChild(sub_item)
                for link in sub_links:
                    link_item = QTreeWidgetItem([link])
                    sub_item.addChild(link_item)
        elif isinstance(paths, list):
            for link in paths:
                link_item = QTreeWidgetItem([link])
                root_item.addChild(link_item)
    tree_widget.expandAll()
    return True


def search_in_tree(tree_widget, query):
    query = query.strip().lower()
    if not query:
        clear_filter(tree_widget)
        return

    def recursive_search(item):
        matched = False
        # Проверка самого item
        if query in item.text(0).lower():
            matched = True
            item.setHidden(False)
            item.setBackground(0, QBrush(QColor("yellow")))
        else:
            item.setBackground(0, QBrush())  # очистка цвета

        # Рекурсивная проверка детей
        child_match = False
        for i in range(item.childCount()):
            child = item.child(i)
            if recursive_search(child):
                child_match = True
                matched = True

        # Раскрываем родителя, если внутри есть совпадения
        if matched or child_match:
            item.setHidden(False)
            item.setExpanded(True)
        else:
            item.setHidden(True)
            item.setExpanded(False)

        return matched

    for i in range(tree_widget.topLevelItemCount()):
        recursive_search(tree_widget.topLevelItem(i))


def clear_filter(tree_widget):
    def recursive_show(item):
        item.setHidden(False)
        item.setBackground(0, QBrush())  # очистка подсветки
        for i in range(item.childCount()):
            recursive_show(item.child(i))

    for i in range(tree_widget.topLevelItemCount()):
        recursive_show(tree_widget.topLevelItem(i))


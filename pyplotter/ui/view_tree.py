# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtCore
from typing import Any

class ViewTree(QtWidgets.QTreeWidget):


    def __init__(self, value:dict) -> None:
        """
        TreeWidget which accept python dictionnary and diaply it as nicely
        organized tree.
        Code from:
        https://stackoverflow.com/questions/21805047/qtreewidget-to-mirror-python-dictionary

        Args:
            value (dict): Python dict to be displayed.
        """

        super().__init__()

        self.setHeaderHidden(True)
        self.setSizeAdjustPolicy(self.AdjustToContents)

        # We save the items marked to easily unmarke them
        self.treeWidgetItemsMarked = None


    def addSnapshot(self, snapshot: dict) -> None:
        self.fillItem(self.invisibleRootItem(), snapshot)



    def fillItem(self, item: QtWidgets.QTreeWidgetItem, value: Any) -> None:

        def new_item(parent, text, val=None):
            child = QtWidgets.QTreeWidgetItem([text])
            self.fillItem(child, val)
            parent.addChild(child)
            child.setExpanded(True)
        if value is None: return
        elif isinstance(value, dict):
            for key, val in sorted(value.items()):
                new_item(item, str(key), val)
        elif isinstance(value, (list, tuple)):
            for val in value:
                text = (str(val) if not isinstance(val, (dict, list, tuple))
                        else '[%s]' % type(val).__name__)
                new_item(item, text, val)
        else:
            new_item(item, str(value))


    def searchItem(self, text: str) -> None:
        """
        Search inside the Tree for the string "text".
        If found, expand recursively all treeWidgetItems from the found items
        to the top level.
        If not found, collapse all items up to the depth 0

        Args:
            text (str): text to be looked for.
        """

        if self.treeWidgetItemsMarked is not None:
            for treeWidgetItem in self.treeWidgetItemsMarked:
                treeWidgetItem.setForeground(0, self.treeWidgetItemForeground)
            self.treeWidgetItemsMarked = None

            self.collapseAll()
            self.expandToDepth(0)

        if len(text)!=0:
            treeWidgetItems = self.findItems(text, QtCore.Qt.MatchContains|QtCore.Qt.MatchRecursive)
            if len(treeWidgetItems)>0:
                self.treeWidgetItemForeground = treeWidgetItems[0].foreground(0)
                for treeWidgetItem in treeWidgetItems:
                    treeWidgetItem.setExpanded(True)
                    treeWidgetItem.setForeground(0, QtCore.Qt.red)
                    parent = treeWidgetItem.parent()
                    while parent is not None:
                        parent.setExpanded(True)
                        parent = parent.parent()

                self.treeWidgetItemsMarked = treeWidgetItems

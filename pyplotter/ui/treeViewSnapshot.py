# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtCore
from typing import Any


class TreeViewSnapshot(QtWidgets.QTreeWidget):

    signalLineEditSnapshotClean = QtCore.pyqtSignal()

    def __init__(self, parent=None) -> None:
        """
        TreeWidget which accept python dictionnary and diaply it as nicely
        organized tree.
        Code from:
        https://stackoverflow.com/questions/21805047/qtreewidget-to-mirror-python-dictionary
        """

        super(TreeViewSnapshot, self).__init__(parent)

        self.setHeaderHidden(True)
        self.setSizeAdjustPolicy(self.AdjustToContents)

        # We save the items marked to easily unmarke them
        self.treeWidgetItemsMarked = None



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



    @QtCore.pyqtSlot(str)
    def searchItem(self, text: str) -> None:
        """
        Call from the SnapshotQLineEdit object, see snapshot_view_tree file.
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



    ############################################################################
    #
    #
    #                           Called from other widgets
    #
    #
    ############################################################################



    @QtCore.pyqtSlot()
    def cleanSnapshot(self) -> None:
        """
        Clean the snapshot.
        """

        current_item = self.invisibleRootItem()
        children = []
        for child in range(current_item.childCount()):
            children.append(current_item.child(child))
        for child in children:
            current_item.removeChild(child)

        self.signalLineEditSnapshotClean.emit()



    @QtCore.pyqtSlot(dict)
    def addSnapshot(self, snapshot: dict) -> None:
        """
        Add the snapshot to the treeView.
        """
        self.fillItem(self.invisibleRootItem(), snapshot)
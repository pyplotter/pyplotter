    # This Python file uses the following encoding: utf-8
from PyQt5 import QtGui, QtWidgets

from ..sources.functions import getDatabaseNameFromAbsPath


class MenuDb(QtWidgets.QMenu):
    """
    Menu called when user right-click on tableWidgetFolder db or plot title.
    Display a QMenu with possibilities to copy the db path
    """


    def __init__(self, databaseAbsPath    : str) -> None:

        super(MenuDb, self).__init__()

        self.databaseAbsPath = databaseAbsPath

        self.menu = QtWidgets.QMenu()

        copyDb = QtWidgets.QAction('Copy dataBase name', self)
        copyDb.triggered.connect(self.clickTitleCopyDb)
        self.menu.addAction(copyDb)

        copyDbAbsPath = QtWidgets.QAction('Copy dataBase absolute path', self)
        copyDbAbsPath.triggered.connect(self.clickTitleCopyDbAbsPath)
        self.menu.addAction(copyDbAbsPath)

        copyDbRePath = QtWidgets.QAction('Copy dataBase relative path', self)
        copyDbRePath.triggered.connect(self.clickTitleCopyDbRePath)
        self.menu.addAction(copyDbRePath)

        self.menu.exec(QtGui.QCursor.pos())



    def clickTitleCopyDb(self, q:QtWidgets.QAction) -> None:

        cb = QtWidgets.QApplication.clipboard()
        cb.setText(getDatabaseNameFromAbsPath(self.databaseAbsPath), mode=cb.Clipboard)



    def clickTitleCopyDbAbsPath(self, q:QtWidgets.QAction) -> None:

        cb = QtWidgets.QApplication.clipboard()
        cb.setText(self.databaseAbsPath, mode=cb.Clipboard)



    def clickTitleCopyDbRePath(self, q:QtWidgets.QAction) -> None:

        cb = QtWidgets.QApplication.clipboard()
        cb.setText('../data/{}'.format(getDatabaseNameFromAbsPath(self.databaseAbsPath)), mode=cb.Clipboard)

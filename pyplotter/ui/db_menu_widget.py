# This Python file uses the following encoding: utf-8
from PyQt5 import QtGui, QtWidgets
import os

class dbMenuWidget:

    def clickDb(self, dataBaseAbsPath: str) -> None:

        self.dataBaseAbsPath = dataBaseAbsPath
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
        cb.setText(self.getDatabaseNameFromPath(self.dataBaseAbsPath), mode=cb.Clipboard)


    def clickTitleCopyDbAbsPath(self, q:QtWidgets.QAction) -> None:

        cb = QtWidgets.QApplication.clipboard()
        cb.setText(self.dataBaseAbsPath, mode=cb.Clipboard)

    def clickTitleCopyDbRePath(self, q:QtWidgets.QAction) -> None:

        cb = QtWidgets.QApplication.clipboard()
        cb.setText('../data/{}'.format(self.getDatabaseNameFromPath(self.dataBaseAbsPath)), mode=cb.Clipboard)

    @staticmethod
    def getDatabaseNameFromPath(dataBaseAbsPath: str) -> str:
        return os.path.basename(dataBaseAbsPath)[:-3]
# This Python file uses the following encoding: utf-8
from PyQt5 import QtGui, QtCore, QtWidgets

class ClickDbMenu:

    def clickDb(self, dataBaseName: str,
                      dataBaseAbsPath: str) -> None:

        self.dataBaseName = dataBaseName
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
        cb.setText(self.dataBaseName, mode=cb.Clipboard)


    def clickTitleCopyDbAbsPath(self, q:QtWidgets.QAction) -> None:

        cb = QtWidgets.QApplication.clipboard()
        cb.setText(self.dataBaseAbsPath, mode=cb.Clipboard)

    def clickTitleCopyDbRePath(self, q:QtWidgets.QAction) -> None:

        cb = QtWidgets.QApplication.clipboard()
        cb.setText('../data/{}'.format(self.dataBaseName), mode=cb.Clipboard)
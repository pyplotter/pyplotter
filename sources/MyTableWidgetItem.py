# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets



class MyTableWidgetItem(QtWidgets.QTableWidgetItem):
    """
    Custom class to be able to sort numerical table column
    """

    def __lt__(self, other):
        if isinstance(other, QtWidgets.QTableWidgetItem):

            return int(self.data(QtCore.Qt.EditRole)) < int(other.data(QtCore.Qt.EditRole))

        return super(MyTableWidgetItem, self).__lt__(other)
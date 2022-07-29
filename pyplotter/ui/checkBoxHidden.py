# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets
from typing import Optional, Any
import os
import uuid

from ..sources.config import loadConfigCurrent, updateUserConfig
config = loadConfigCurrent()


class CheckBoxHidden(QtWidgets.QCheckBox):

    signalcheckBoxHiddenClick = QtCore.pyqtSignal(int)
    signalcheckBoxHiddenState = QtCore.pyqtSignal(int, bool)

    def __init__(self, parent: Optional[Any]=None) -> None:
        super(CheckBoxHidden, self).__init__(parent)

        self.stateChanged.connect(self.signalcheckBoxHiddenClick)



    ############################################################################
    #
    #
    #                           Called from other widgets
    #
    #
    ############################################################################



    @QtCore.pyqtSlot(int)
    def hideRow(self, row: int):

        self.signalcheckBoxHiddenState.emit(row, not self.isChecked())



    @QtCore.pyqtSlot()
    def databaseClick(self):
        # Disable interactivity
        self.setChecked(False)
        self.setEnabled(False)



    @QtCore.pyqtSlot()
    def databaseClickDone(self):
        # Enable database interaction
        self.setEnabled(True)

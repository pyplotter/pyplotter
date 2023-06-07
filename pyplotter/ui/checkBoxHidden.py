# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets
from typing import Optional, Any

class CheckBoxHidden(QtWidgets.QCheckBox):

    signalcheckBoxHiddenClick = QtCore.pyqtSignal(int)

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



    @QtCore.pyqtSlot(bool)
    def checkBoxStaredChecked(self, checked: bool ) -> None:
        """
        Called from tableWidgetDatabase.
        When user check the "show only stared run" checkbox, we disable the
        "Show hidden" checkbox and vice-versa.

        Args:
            checked : If the "show only stared run" checkbox is checked.
        """

        if checked:
            # Disable interactivity
            self.setChecked(False)
            self.setEnabled(False)
        else:
            # Enable database interaction
            self.setEnabled(True)



    @QtCore.pyqtSlot()
    def hideRow(self):
        """
        Called by tableWidgetDatabase when user wants to hide a run
        """

        self.signalcheckBoxHiddenClick.emit(self.checkState())



    @QtCore.pyqtSlot()
    def databaseClick(self):
        # Disable interactivity
        self.setChecked(False)
        self.setEnabled(False)



    @QtCore.pyqtSlot(str)
    def databaseClickDone(self, databaseAbsPath: str):
        # Enable database interaction
        self.setEnabled(True)

from PyQt5 import QtCore, QtWidgets
from typing import Optional, Any


class CheckBoxStared(QtWidgets.QCheckBox):

    signalCheckBoxStaredClick = QtCore.pyqtSignal(int)

    def __init__(self, parent: Optional[Any]=None) -> None:
        super(CheckBoxStared, self).__init__(parent)

        self.stateChanged.connect(self.signalCheckBoxStaredClick)



    ############################################################################
    #
    #
    #                           Called from other widgets
    #
    #
    ############################################################################



    @QtCore.pyqtSlot(bool)
    def checkBoxHiddenChecked(self, checked: bool ) -> None:
        """
        Called from tableWidgetDatabase.
        When user check the "Show hidden" checkbox, we disable the "show only
        stared run" checkbox and vice-versa.

        Args:
            checked : If the "Show hidden" checkbox is checked.
        """

        if checked:
            # Disable interactivity
            self.setChecked(False)
            self.setEnabled(False)
        else:
            # Enable database interaction
            self.setEnabled(True)



    @QtCore.pyqtSlot()
    def databaseClick(self) -> None:
        # Disable interactivity
        self.setChecked(False)
        self.setEnabled(False)



    @QtCore.pyqtSlot(str)
    def databaseClickDone(self, databaseAbsPath: str) -> None:
        # Enable database interaction
        self.setEnabled(True)

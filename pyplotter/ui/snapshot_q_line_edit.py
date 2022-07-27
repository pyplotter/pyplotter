# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtCore

class SnapshotQLineEdit(QtWidgets.QLineEdit):
    """
    Widget to allow user to enter word to be searched for in the
    SnapshotViewTree.
    """

    signalSnapshotLineEditFilterTextEdited = QtCore.pyqtSignal(str)


    def __init__(self, parent=None) -> None:

        super(SnapshotQLineEdit, self).__init__(parent)

        self.textChanged.connect(self.snapshotLineEditFilterTextEdited)


    @QtCore.pyqtSlot()
    def snapshotLineEditFilterTextEdited(self) -> None:
        """
        Called when user types text in the filter lineEdit widget.
        Looked for the all keys which contains the entered string

        Parameters
        ----------
        text : str
            Text to be found in the run snapshot
        """
        self.signalSnapshotLineEditFilterTextEdited.emit(self.text())

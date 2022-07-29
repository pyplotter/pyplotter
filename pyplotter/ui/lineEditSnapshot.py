# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtCore

class LineEditSnapshot(QtWidgets.QLineEdit):
    """
    Widget to allow user to enter word to be searched for in the
    SnapshottreeView.
    """

    signallineEditFilterSnapshotTextEdited = QtCore.pyqtSignal(str)


    def __init__(self, parent=None) -> None:

        super(LineEditSnapshot, self).__init__(parent)

        self.textChanged.connect(self.lineEditFilterSnapshotTextEdited)


    @QtCore.pyqtSlot()
    def lineEditFilterSnapshotTextEdited(self) -> None:
        """
        Called when user types text in the filter lineEdit widget.
        Looked for the all keys which contains the entered string

        Parameters
        ----------
        text : str
            Text to be found in the run snapshot
        """
        self.signallineEditFilterSnapshotTextEdited.emit(self.text())


    @QtCore.pyqtSlot()
    def clean(self) -> None:
        """
        Call from when the treeViewSnapshot is clean,
        """
        self.setText('')


    @QtCore.pyqtSlot(bool)
    def enabled(self, enabled: bool) -> None:
        """
        Call from tableWidgetParameter in runClick
        """
        self.setEnabled(enabled)
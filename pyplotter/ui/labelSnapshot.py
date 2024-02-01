from PyQt5 import QtWidgets, QtCore

class LabelSnapshot(QtWidgets.QLabel):
    """
    Widget to allow user to enter word to be searched for in the
    SnapshottreeView.
    """

    def __init__(self, parent=None) -> None:
        super(LabelSnapshot, self).__init__(parent)


    @QtCore.pyqtSlot(bool)
    def enabled(self, enabled: bool) -> None:
        """
        Call from tableWidgetParameter in runClick
        """
        self.setEnabled(enabled)
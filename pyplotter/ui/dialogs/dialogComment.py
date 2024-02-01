from PyQt5 import QtCore, QtWidgets, QtGui

class DialogComment(QtWidgets.QDialog):
    """
    Dialog shown when user want to add a comment to a run
    """


    signalCloseDialogComment  = QtCore.pyqtSignal()
    signalUpdateDialogComment = QtCore.pyqtSignal(int, str)


    def __init__(self, runId: int,
                       comment: str) -> None:

        QtWidgets.QDialog.__init__(self, None)

        self.runId = runId
        self._allowClosing = False

        self.setWindowModality(QtCore.Qt.NonModal)
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint|
                            QtCore.Qt.WindowMaximizeButtonHint|
                            QtCore.Qt.WindowCloseButtonHint)

        self.setMinimumSize(200, 200)

        layout = QtWidgets.QVBoxLayout()

        self.textEdit = QtWidgets.QTextEdit()
        self.textEdit.setPlaceholderText('Add a comment to the run')
        self.textEdit.setPlainText(comment)
        self.textEdit.setAcceptRichText(False)
        self.textEdit.textChanged.connect(self.textEditTextChanged)
        layout.addWidget(self.textEdit)
        self.setLayout(layout)

        self.setWindowTitle('Comment run {}'.format(self.runId))

        self.show()



    def textEditTextChanged(self) -> None:

        self.signalUpdateDialogComment.emit(self.runId,
                                            self.textEdit.toPlainText())



    def closeEvent(self, evnt: QtGui.QCloseEvent) -> None:

        # # We catch the close event and ignore it
        if not self._allowClosing:
            evnt.ignore()

        # All the closing procedure of the plot is handle in the tableWidgetDatabase
        self.signalCloseDialogComment.emit()

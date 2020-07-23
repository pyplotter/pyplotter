# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtCore, QtGui

class QTableWidgetKey(QtWidgets.QTableWidget):
    """
    Custom class used in QtDesigner.
    Catch a key pressed event
    """
    keyPressed = QtCore.pyqtSignal(str, int)

    def keyPressEvent(self, event):
        super(QTableWidgetKey, self).keyPressEvent(event)

        # Emit the pressed key in hum readable format in lower case
        self.keyPressed.emit(QtGui.QKeySequence(event.key()).toString().lower(), self.currentRow())
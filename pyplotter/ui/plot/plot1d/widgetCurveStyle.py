from PyQt5 import QtCore, QtGui, QtWidgets


class WidgetCurveStyle(QtWidgets.QWidget):

    # Send to widgetPlot1d when user click on the comboBox
    signalCurveStyleChanged = QtCore.pyqtSignal(str)


    def __init__(self, parent: QtWidgets.QGroupBox) -> None:
        """
        Widget handling the style of the curves in a 1d plot.
        Display a label and a comboBox.
        User may interact with the comboBox to change the curve style.
        When the user change the style, a signal is sent to the
        widgetplot1d.

        Args:
            parent: Parent of the widget.
                Should be groupBoxDisplay
        """

        super(WidgetCurveStyle, self).__init__(parent)

        self.setToolTip("Sets the curve style.\n"
                        " -: solide line.\n"
                        "o-: solide line with symbol.\n"
                        " o: symbol (scatter plot).")

        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)

        self.hLayout = QtWidgets.QHBoxLayout(self)
        self.hLayout.setContentsMargins(0, 0, 0, 0)

        self.label = QtWidgets.QLabel(self)
        self.label.setFont(font)
        self.label.setText('line style: ')

        self.comboBox = QtWidgets.QComboBox(self)
        self.comboBox.setFont(font)
        self.comboBox.addItem(' -')
        self.comboBox.addItem('o-')
        self.comboBox.addItem(' o')
        self.comboBox.setCurrentIndex(0)
        self.comboBox.currentIndexChanged.connect(self.currentIndexChanged)

        spacerItem = QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        self.hLayout.addWidget(self.label)
        self.hLayout.addWidget(self.comboBox)
        self.hLayout.addItem(spacerItem)

        self.setLayout(self.hLayout)
        parent.layout().addWidget(self)


    @QtCore.pyqtSlot(int)
    def currentIndexChanged(self, value: int) -> None:
        self.signalCurveStyleChanged.emit(self.comboBox.currentText())

from PyQt5 import QtCore, QtGui, QtWidgets


class WidgetDownsampling(QtWidgets.QWidget):

    # Send to widgetPlot1d when user click on the spinbox
    signalDownsamplingChanged = QtCore.pyqtSignal(int)


    def __init__(self, parent: QtWidgets.QGroupBox) -> None:
        """
        Widget handling the downsampling in a 1d plot.
        Display a spinBox and a label.
        User may interact with the spinBox to change the downsampling value.
        When the user change the downsampling value, a signal is sent to the
        widgetplot1d which will use the pyqtgraph downsampling method of all
        plotDataItem.

        Args:
            parent: Parent of the widget.
                Should be groupBoxDisplay
        """

        super(WidgetDownsampling, self).__init__(parent)

        self.setToolTip("Sets the downsampling value of all displayed curves.\n"
                        "Downsampling reduces the number of points drawn and increase performance.")

        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)

        self.hLayout = QtWidgets.QHBoxLayout(self)
        self.hLayout.setContentsMargins(0, 0, 0, 0)

        self.label = QtWidgets.QLabel(self)
        self.label.setFont(font)
        self.label.setText(': downsampling')

        self.sbox = QtWidgets.QSpinBox(self)
        self.sbox.setFont(font)
        self.sbox.setValue(1)
        self.sbox.setMinimum(1)
        self.sbox.setMaximum(1000000)
        self.sbox.valueChanged.connect(self.sboxValueChanged)

        spacerItem = QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        self.hLayout.addWidget(self.sbox)
        self.hLayout.addWidget(self.label)
        self.hLayout.addItem(spacerItem)

        self.setLayout(self.hLayout)
        parent.layout().addWidget(self)


    @QtCore.pyqtSlot(int)
    def sboxValueChanged(self, value: int) -> None:

        self.signalDownsamplingChanged.emit(value)

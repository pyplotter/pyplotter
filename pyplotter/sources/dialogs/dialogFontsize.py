# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets
from ...ui.dialogFontsize import Ui_DialogFontsize
from ..config import updateUserConfig


class MenuDialogFontSize(QtWidgets.QDialog, Ui_DialogFontsize):


    signalUpdateStyle = QtCore.pyqtSignal(dict)


    def __init__(self, parent: QtWidgets.QMainWindow,
                       config: dict) -> None:

        QtWidgets.QDialog.__init__(self, parent)
        self.setupUi(self)

        self.config = config

        self.spinBoxFontSize.setValue(config['axisLabelFontSize'])
        self.spinBoxFontSize.valueChanged.connect(self.spinBoxFontSizeChanged)

        self.show()


    def spinBoxFontSizeChanged(self, value: int) -> None:

        for label in ('axisLabelFontSize',
                      'tickLabelFontSize'):
            self.config[label] = value
            updateUserConfig(label, value)

        self.signalUpdateStyle.emit(self.config)

# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets
from ...ui.dialog_fontsize import Ui_DialogFontsize
from ..config import updateUserConfig


class MenuDialogFontSize(QtWidgets.QDialog, Ui_DialogFontsize):



    def __init__(self, config,
                       updatePlotsStyle) -> None:

        super(MenuDialogFontSize, self).__init__()
        self.setupUi(self)

        self.config           = config
        self.updatePlotsStyle = updatePlotsStyle

        self.spinBoxFontSize.setValue(config['axisLabelFontSize'])
        self.spinBoxFontSize.valueChanged.connect(self.spinBoxFontSizeChanged)

        self.show()


    def spinBoxFontSizeChanged(self, value: int) -> None:

        for label in ('axisLabelFontSize',
                      'tickLabelFontSize'):
            self.config[label] = value
            updateUserConfig(label, value)

        self.updatePlotsStyle(self.config)

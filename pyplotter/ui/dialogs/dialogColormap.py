from PyQt5 import QtCore, QtWidgets
from .dialogColormapUi import Ui_DialogColormap
from ...sources.config import updateUserConfig
from ...sources import palettes # File copy from bokeh: https://github.com/bokeh/bokeh/blob/7cc500601cdb688c4b6b2153704097f3345dd91c/bokeh/palettes.py


class DialogMenuColormap(QtWidgets.QDialog, Ui_DialogColormap):


    signalUpdateStyle = QtCore.pyqtSignal(dict)


    def __init__(self, parent: QtWidgets.QMainWindow,
                       config: dict) -> None:

        QtWidgets.QDialog.__init__(self, parent)
        self.setupUi(self)

        self.config = config

        # Build the colormap comboBox, the default one being from the config file
        index = 0
        indexViridis = 0
        for cm in [i for i in palettes.all_palettes.keys() if i[-2:] !='_r']:
            self.comboBoxColormap.addItem(cm)
            if cm==self.config['plot2dcm']:
                indexViridis = index

        # self.setColorMap(self.config['plot2dcm'])
        self.comboBoxColormap.setCurrentIndex(indexViridis)
        self.comboBoxColormap.currentIndexChanged.connect(self.comboBoxcolormapChanged)

        self.show()


    def comboBoxcolormapChanged(self, index: int) -> None:


        cm = self.comboBoxColormap.currentText()

        self.config['plot2dcm'] = cm
        updateUserConfig('plot2dcm', cm)

        self.signalUpdateStyle.emit(self.config)

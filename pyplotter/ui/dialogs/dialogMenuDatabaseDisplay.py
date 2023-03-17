# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets, QtCore

from .dialogMenuDatabaseDisplayUi import Ui_MenuDataBaseDisplay
from ...sources.config import updateUserConfig


class DialogMenuDatabaseDisplay(QtWidgets.QDialog, Ui_MenuDataBaseDisplay):


    signalUpdateTableWidgetDatabase = QtCore.pyqtSignal(dict)


    def __init__(self, parent: QtWidgets.QMainWindow,
                       config: dict) -> None:

        QtWidgets.QDialog.__init__(self, parent)
        self.setupUi(self)

        self.config = config

        # Add one checkbox per column
        for val in config['DatabaseDisplayColumn'].values():

            if val['name']!='':
                cb = QtWidgets.QCheckBox(val['name'])
                cb.setChecked(val['visible'])
                cb.toggled.connect(lambda : self.checkBoxClicked())
                self.verticalLayoutColumnDisplay.addWidget(cb)

        self.show()


    def checkBoxClicked(self) -> None:
        """
        When the checkbox is clicked we:
            1. Update the current config dictionnary
            2. Update the current user config file
            3. Send a signal to tabelWidgetDatabase to update what column is
                shown
        """

        for w in (self.verticalLayoutColumnDisplay.itemAt(i).widget() for i in range(self.verticalLayoutColumnDisplay.count())):
            if isinstance(w, QtWidgets.QCheckBox):
                if w.isChecked():
                    for k, v in self.config['DatabaseDisplayColumn'].items():
                        if w.text()==v['name']:
                            self.config['DatabaseDisplayColumn'][k]['visible'] = True
                            updateUserConfig(['DatabaseDisplayColumn', k, 'visible'], True)
                else:
                    for k, v in self.config['DatabaseDisplayColumn'].items():
                        if w.text()==v['name']:
                            self.config['DatabaseDisplayColumn'][k]['visible'] = False
                            updateUserConfig(['DatabaseDisplayColumn', k, 'visible'], False)


        self.signalUpdateTableWidgetDatabase.emit(self.config)




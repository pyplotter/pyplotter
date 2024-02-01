from PyQt5 import QtCore, QtWidgets
from typing import Optional, Any
import os

from ..sources.config import loadConfigCurrent
config = loadConfigCurrent()


class pushButtonOpenFolder(QtWidgets.QPushButton):

    signalFolderOpened = QtCore.pyqtSignal(str)

    def __init__(self, parent: Optional[Any]=None) -> None:
        super(pushButtonOpenFolder, self).__init__(parent)

        self.clicked.connect(self.openFolderClicked)



    def openFolderClicked(self) -> None:
        """
        Call when user click on the 'Open folder' button.
        Allow user to chose any available folder in his computer.
        """

        # Ask user to chose a path
        path = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                          caption='Open folder',
                                                          directory=os.getcwd(),
                                                          options=QtWidgets.QFileDialog.ReadOnly|QtWidgets.QFileDialog.ShowDirsOnly)
        if path != '':
            # Set config parameter accordingly
            config['path'] = os.path.abspath(path)
            config['root'] = os.path.splitdrive(path)[0]

            self.signalFolderOpened.emit(path)
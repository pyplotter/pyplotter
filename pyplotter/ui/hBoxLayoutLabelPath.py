# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets
from typing import Optional, Any
import os
import uuid

from ..sources.config import loadConfigCurrent, updateUserConfig
config = loadConfigCurrent()
from..sources.functions import clearLayout


class HBoxLayoutLabelPath(QtWidgets.QHBoxLayout):


    signalButtonClick = QtCore.pyqtSignal(str)


    def __init__(self, parent: Optional[Any]=None) -> None:
        super(HBoxLayoutLabelPath, self).__init__(parent)


    @QtCore.pyqtSlot(str)
    def updateLabelPath(self, directory: str) -> None:
        """
        Update the label path by creating a horizontal list of buttons to
        quickly browse back the folder arborescence.
        """

        clearLayout(self)

        path = os.path.normpath(directory).split(os.sep)
        root = os.path.normpath(config['root']).split(os.sep)

        # Display path until root
        for i, text in enumerate(path):

            # Build button text depending of where we are
            bu_text: Optional[str] = None
            if text==root[0]:
                bu_text = 'root'
            else:
                bu_text = text

            # Create, append and connect buttons
            if bu_text is not None:
                bu = QtWidgets.QPushButton(bu_text)
                bu.setStyleSheet("font-weight: normal;")
                width = bu.fontMetrics().boundingRect(bu_text).width() + 15
                bu.setMaximumWidth(width)
                d = os.path.join(path[0], os.sep, *path[1:i+1])
                bu.clicked.connect(lambda bu, directory=d : self.signalButtonClick.emit(directory))
                self.addWidget(bu)

        self.setAlignment(QtCore.Qt.AlignLeft)
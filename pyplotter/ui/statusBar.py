# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets
from typing import Optional, Any
import os
import uuid

from ..sources.config import loadConfigCurrent, updateUserConfig
config = loadConfigCurrent()


class StatusBar(QtWidgets.QStatusBar):

    signalUpdateStyle        = QtCore.pyqtSignal(dict)
    signalOpenDialogLivePlot = QtCore.pyqtSignal()
    signalDatabaseClick      = QtCore.pyqtSignal(str, QtWidgets.QProgressBar)
    signalParameterClick     = QtCore.pyqtSignal(str, str, str, str, str, int, str, QtWidgets.QProgressBar)

    def __init__(self, parent: Optional[Any]=None) -> None:
        super(StatusBar, self).__init__(parent)


    @QtCore.pyqtSlot(str, str)
    def setStatusBarMessage(self, text: str,
                                  color: Optional[str]='') -> None:
        """
        Display message in the status bar.

        Parameters
        ----------
        text : Text to be displayed.
        color : Text color.
            Default is ""
        """

        if color=='':
            self.setStyleSheet('color: {};'.format(config['styles'][config['style']]['dialogTextColor']))
        else:
            self.setStyleSheet('color: {};'.format(color))

        self.showMessage(text)


    @QtCore.pyqtSlot(str)
    def databaseClick(self, databaseAbsPath:str) -> None:

        progressBar = self.addProgressBar()
        self.signalDatabaseClick.emit(databaseAbsPath,
                                      progressBar)


    @QtCore.pyqtSlot(str, str, str, str, str, int, str)
    def parameterClick(self, curveId: str,
                             databaseAbsPath: str,
                             dependentParamName: str,
                             plotRef: str,
                             plotTitle: str,
                             runId: int,
                             windowTitle: str) -> None:

        progressBar = self.addProgressBar()
        self.signalParameterClick.emit(curveId,
                                       databaseAbsPath,
                                       dependentParamName,
                                       plotRef,
                                       plotTitle,
                                       runId,
                                       windowTitle,
                                       progressBar)

    ###########################################################################
    #
    #
    #                           Progress bar
    #
    #
    ###########################################################################



    @QtCore.pyqtSlot()
    def addProgressBar(self) -> QtWidgets.QProgressBar:
        """
        Add a progress bar in the status bar.

        Return
        ------
        progressBarKey : str
            An unique key coming from uuid.uuid4().
        """

        # Add a progress bar in the statusbar
        progressBarKey = str(uuid.uuid4())
        progressBar = QtWidgets.QProgressBar()
        progressBar.key = progressBarKey
        progressBar.decimal = 100
        progressBar.setAlignment(QtCore.Qt.AlignCenter)
        progressBar.setValue(0)
        # setting maximum value for 2 decimal points
        progressBar.setMaximum(100*progressBar.decimal)
        progressBar.setTextVisible(True)
        self.setSizeGripEnabled(False)
        self.addPermanentWidget(progressBar)

        return progressBar



    @QtCore.pyqtSlot(QtWidgets.QProgressBar)
    def removeProgressBar(self, progressBar: QtWidgets.QProgressBar) -> None:
        """
        Remove the progress bar in the status bar.
        Usually called after a thread has loaded something.
        """
        self.removeWidget(progressBar)
        del(progressBar)



    def updateProgressBar(self, progressBar: QtWidgets.QProgressBar,
                                val: int,
                                text: Optional[str]=None) -> None:
        """
        Update the progress bar in the status bar

        Parameters
        ----------
        progressBar : str
            progressBar from addProgressBar.
        val : int
            Value of the progress.
            Must be an int between 0 and 100.
        text : str
            Text to be shown on the progress bar.
        """
        if text is not None:
            progressBar.setFormat(text)
        progressBar.setValue(int(val*progressBar.decimal))

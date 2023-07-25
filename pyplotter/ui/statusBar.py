# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets, QtGui
from typing import Optional, Any
import uuid

from ..sources.config import loadConfigCurrent
config = loadConfigCurrent()


class StatusBar(QtWidgets.QStatusBar):

    signalUpdateStyle         = QtCore.pyqtSignal(dict)
    signalOpenDialogLivePlot  = QtCore.pyqtSignal()
    signalDatabaseLoadingStop = QtCore.pyqtSignal()
    signalDatabaseLoad        = QtCore.pyqtSignal(str, QtWidgets.QProgressBar)
    signalCsvLoad             = QtCore.pyqtSignal(str, bool, QtWidgets.QProgressBar)
    signalBlueForsLoad        = QtCore.pyqtSignal(str, bool, QtWidgets.QProgressBar)
    signalAddCurve            = QtCore.pyqtSignal(str, str, str, str, str, str, int, str, QtWidgets.QCheckBox, QtWidgets.QProgressBar)

    def __init__(self, parent: Optional[Any]=None) -> None:
        super(StatusBar, self).__init__(parent)

        self.labelMessage = QtWidgets.QLabel()
        self.addPermanentWidget(self.labelMessage)

        self.labelMessage2 = QtWidgets.QLabel()
        self.addPermanentWidget(self.labelMessage2)

        # Add spacer
        w = QtWidgets.QWidget()
        hbox = QtWidgets.QHBoxLayout()
        hbox.addSpacerItem(QtWidgets.QSpacerItem(40, 1))
        w.setLayout(hbox)
        self.addPermanentWidget(w, 1)


    @QtCore.pyqtSlot(str, str)
    def addStatusBarMessage(self, text: str,
                                  color: Optional[str]='') -> None:
        """
        Display message in the status bar.

        Parameters
        ----------
        text : Text to be displayed.
        color : Text color.
            Default is ""
        """

        self.labelMessage2.setText('<span style="color: {};">{}</span>'.format(color, text))
        self.labelMessage2.adjustSize()



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

        self.labelMessage.setText('<span style="color: {};">{}</span>'.format(color, text))
        self.labelMessage.adjustSize()



    @QtCore.pyqtSlot(str, bool)
    def csvLoad(self, databaseAbsPath: str,
                      doubleClick: bool) -> None:

        self.progressBarDatabaseLoad = self.addProgressBar()
        self.signalCsvLoad.emit(databaseAbsPath,
                                doubleClick,
                                self.progressBarDatabaseLoad)



    @QtCore.pyqtSlot(str, bool)
    def blueForsLoad(self, databaseAbsPath: str,
                           doubleClick: bool) -> None:

        self.progressBarDatabaseLoad = self.addProgressBar()
        self.signalBlueForsLoad.emit(databaseAbsPath,
                                     doubleClick,
                                     self.progressBarDatabaseLoad)



    @QtCore.pyqtSlot()
    def databaseLoadingStop(self) -> None:
        """
        Called from tableWidgetFolder to interupt the loading of a database.
        Remove the progress bar of the database loading and propagate the
        event to tableWidgetDatabase.
        """

        self.removeProgressBar(self.progressBarDatabaseLoad)
        self.signalDatabaseLoadingStop.emit()



    @QtCore.pyqtSlot(str)
    def databaseLoad(self, databaseAbsPath: str) -> None:

        self.progressBarDatabaseLoad = self.addProgressBar()
        self.signalDatabaseLoad.emit(databaseAbsPath,
                                     self.progressBarDatabaseLoad)


    @QtCore.pyqtSlot(str, str, str, str, str, str, int, str, QtWidgets.QCheckBox)
    def addCurve(self, curveId: str,
                       databaseAbsPath: str,
                       dataType: str,
                       dependentParamName: str,
                       plotRef: str,
                       plotTitle: str,
                       runId: int,
                       windowTitle: str,
                       cb: QtWidgets.QCheckBox) -> None:

        progressBar = self.addProgressBar()
        self.signalAddCurve.emit(curveId,
                                 databaseAbsPath,
                                 dataType,
                                 dependentParamName,
                                 plotRef,
                                 plotTitle,
                                 runId,
                                 windowTitle,
                                 cb,
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
        Add a progress bar in the status bar and return it
        """

        # Add a progress bar in the statusbar
        progressBar = QtWidgets.QProgressBar()
        progressBar.setMinimumWidth(400)
        progressBar.setAlignment(QtCore.Qt.AlignCenter)
        progressBar.setValue(0)
        progressBar.setMaximum(100*config['progressBarDecimal'])
        progressBar.setTextVisible(True)

        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor(255, 165, 0)) # text, not highlight
        palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(255, 165, 0)) # text, not highlight
        progressBar.setPalette(palette)

        self.setSizeGripEnabled(False)
        self.addPermanentWidget(progressBar)
        self.progressBarLabel = QtWidgets.QLabel('   ')
        self.addPermanentWidget(progressBar)
        self.addPermanentWidget(self.progressBarLabel)

        return progressBar



    @QtCore.pyqtSlot(QtWidgets.QProgressBar)
    def removeProgressBar(self, progressBar: QtWidgets.QProgressBar) -> None:
        """
        Remove the progress bar in the status bar.
        Usually called after a thread has loaded something.
        """
        self.removeWidget(progressBar)
        del(progressBar)

        if hasattr(self, 'progressBarLabel'):
            self.removeWidget(self.progressBarLabel)
            del(self.progressBarLabel)



    @QtCore.pyqtSlot(QtWidgets.QProgressBar, float, str)
    def updateProgressBar(self, progressBar: QtWidgets.QProgressBar,
                                val: float,
                                text: str) -> None:
        """
        Update the progress bar in the status bar

        Parameters
        ----------
        progressBar : str
            progressBar from addProgressBar.
        val : float
            Value of the progress.
            Must be an float between 0 and 100.
        text : str
            Text to be shown on the progress bar.
        """
        progressBar.setValue(int(val*config['progressBarDecimal']))
        progressBar.setFormat(text)


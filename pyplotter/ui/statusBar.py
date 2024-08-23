from PyQt5 import QtCore, QtWidgets, QtGui
from typing import Any, Dict, Optional

from ..sources.config import loadConfigCurrent
config = loadConfigCurrent()


class StatusBar(QtWidgets.QStatusBar):

    signalUpdateStyle         = QtCore.pyqtSignal(dict)
    signalOpenDialogLivePlot  = QtCore.pyqtSignal()
    signalDatabaseLoadingStop = QtCore.pyqtSignal()
    signalDatabaseLoad        = QtCore.pyqtSignal(str, int)
    signalCsvLoad             = QtCore.pyqtSignal(str, bool, int)
    signalNpzLoad             = QtCore.pyqtSignal(str, bool, int)
    signalExportRunLoad       = QtCore.pyqtSignal(str, str, int, int)
    signalBlueForsLoad        = QtCore.pyqtSignal(str, bool, int)
    signalAddCurve            = QtCore.pyqtSignal(str, str, str, str, str, str, int, str, QtWidgets.QCheckBox, int)

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


        # Keep track of all progressBars being displayed in the status bar
        self.progressBars: Dict[int, QtWidgets.QProgressBar] = {}


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
        """
        Signal sent from tableWidgetFolder when user click on a CSV file to
        display its info in the tableWidgetParameter.
        Add a progressBar to the statusBar and propagate the signal to the
        tableWidgetParameter with progressBar id.

        Args:
            databaseAbsPath: Absolute path of the file
            doubleClick: if the user double click on the file.
        """

        progressBarId = self.addProgressBar()
        self.signalCsvLoad.emit(databaseAbsPath,
                                doubleClick,
                                progressBarId)



    @QtCore.pyqtSlot(str, bool)
    def npzLoad(self, databaseAbsPath: str,
                      doubleClick: bool) -> None:
        """
        Signal sent from tableWidgetFolder when user click on a NPZ file to
        display its info in the tableWidgetParameter.
        Add a progressBar to the statusBar and propagate the signal to the
        tableWidgetParameter with progressBar id.

        Args:
            databaseAbsPath: Absolute path of the file
            doubleClick: if the user double click on the file.
        """

        progressBarId = self.addProgressBar()
        self.signalNpzLoad.emit(databaseAbsPath,
                                doubleClick,
                                progressBarId)



    @QtCore.pyqtSlot(str, bool)
    def blueForsLoad(self, databaseAbsPath: str,
                           doubleClick: bool) -> None:
        """
        Signal sent from tableWidgetFolder when user click on a BlueFors file to
        display its info in the tableWidgetParameter.
        Add a progressBar to the statusBar and propagate the signal to the
        tableWidgetParameter with progressBar id.

        Args:
            databaseAbsPath: Absolute path of the file
            doubleClick: if the user double click on the file.
        """
        progressBarId = self.addProgressBar()
        self.signalBlueForsLoad.emit(databaseAbsPath,
                                     doubleClick,
                                     progressBarId)



    @QtCore.pyqtSlot(str, str, int)
    def exportRunAddProgressBar(self, source_db_path: str,
                                      target_db_path: str,
                                      runId: int) -> None:
        """
        Called from menuExportRun

        Args:
            source_db_path:  Path to the source DB file
            target_db_path: Path to the target DB file.
                The target DB file will be created if it does not exist.
            runId: The run_id of the runs to copy into the target DB file
        """

        progressBarId = self.addProgressBar()
        self.signalExportRunLoad.emit(source_db_path,
                                      target_db_path,
                                      runId,
                                      progressBarId)



    @QtCore.pyqtSlot(str)
    def databaseLoad(self, databaseAbsPath: str) -> None:

        progressBarId = self.addProgressBar()
        self.signalDatabaseLoad.emit(databaseAbsPath,
                                     progressBarId)


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

        progressBarId = self.addProgressBar()
        self.signalAddCurve.emit(curveId,
                                 databaseAbsPath,
                                 dataType,
                                 dependentParamName,
                                 plotRef,
                                 plotTitle,
                                 runId,
                                 windowTitle,
                                 cb,
                                 progressBarId)



    ###########################################################################
    #
    #
    #                           Progress bar
    #
    #
    ###########################################################################



    @QtCore.pyqtSlot()
    def addProgressBar(self) -> int:
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
        if len(self.progressBars.keys()) < config['progressBarMaxNb']:
            self.addPermanentWidget(progressBar)

        # Determine the progress bar id
        if len(self.progressBars.keys())>0:
            id = max(self.progressBars.keys())+1
        else:
            id = 0

        # Store it
        self.progressBars[id] = progressBar

        return id



    @QtCore.pyqtSlot(int)
    def removeProgressBar(self, progressBarId: int) -> None:
        """
        Remove the progress bar in the status bar.
        Usually called after a thread has loaded something.
        """
        self.removeWidget(self.progressBars[progressBarId])
        self.progressBars.pop(progressBarId)



    @QtCore.pyqtSlot(int, float, str)
    def updateProgressBar(self, progressBarId: int,
                                val: float,
                                text: str) -> None:
        """
        Update the progress bar in the status bar

        Parameters
        ----------
        progressBarId : int
            Id of the progress bar.
        val : float
            Value of the progress.
            Must be an float between 0 and 100.
        text : str
            Text to be shown on the progress bar.
        """

        self.progressBars[progressBarId].setValue(int(val*config['progressBarDecimal']))
        self.progressBars[progressBarId].setFormat(text)


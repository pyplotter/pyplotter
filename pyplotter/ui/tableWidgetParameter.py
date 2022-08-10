# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets, QtTest
import os


from ..sources.config import loadConfigCurrent
config = loadConfigCurrent()
from ..sources.workers.loadDataFromRun import LoadDataFromRunThread
from ..sources.functions import (clearTableWidget,
                                 getCurveId,
                                 getPlotRef,
                                 getPlotTitle,
                                 getWindowTitle)
from ..sources.widgetPlot import WidgetPlot

# Get the folder path for pictures
PICTURESPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pictures')

class TableWidgetParameter(QtWidgets.QTableWidget):
    """
    Custom class to be able to sort numerical table column
    """

    signalSendStatusBarMessage       = QtCore.pyqtSignal(str, str)
    signalUpdateProgressBar          = QtCore.pyqtSignal(QtWidgets.QProgressBar, int, str)
    signalRemoveProgressBar          = QtCore.pyqtSignal(QtWidgets.QProgressBar)
    signalAddCurve                   = QtCore.pyqtSignal(str, str, str, str, str, str, int, str, QtWidgets.QCheckBox)
    signalRemoveCurve                = QtCore.pyqtSignal(str, str)
    signalCleanSnapshot              = QtCore.pyqtSignal()
    signalAddSnapshot                = QtCore.pyqtSignal(dict)
    signalLineEditSnapshotEnabled    = QtCore.pyqtSignal(bool)
    signalLabelSnapshotEnabled       = QtCore.pyqtSignal(bool)
    signalUpdateLabelCurrentSnapshot = QtCore.pyqtSignal(str)
    signalUpdateLabelCurrentRun      = QtCore.pyqtSignal(str)
    signaladdRow                     = QtCore.pyqtSignal(int, dict, str, str, str, str, str, str, str, int)

    signalLoadedDataEmpty  = QtCore.pyqtSignal(QtWidgets.QCheckBox, QtWidgets.QProgressBar)
    signalLoadedDataFull   = QtCore.pyqtSignal(int, str, str, str, str, str, QtWidgets.QCheckBox, QtWidgets.QProgressBar, tuple, str, str, str, str, str, str, bool)
    signalCSVLoadData      = QtCore.pyqtSignal(str, str, str, str, str, int, str, QtWidgets.QCheckBox, QtWidgets.QProgressBar)
    signalBlueForsLoadData = QtCore.pyqtSignal(str, str, str, str, str, int, str, QtWidgets.QCheckBox, QtWidgets.QProgressBar)



    def __init__(self, parent=None) -> None:
        super(TableWidgetParameter, self).__init__(parent)

        self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        self.cellClicked.connect(self.parameterCellClicked)

        self.threadpool = QtCore.QThreadPool()

        # Flag
        self._dataDowloadingFlag = False


    def first_call(self):
        ## Only used to propagate information
        # runId
        self.setColumnHidden(0, True)
        # experimentName
        self.setColumnHidden(1, True)
        # parameterName
        self.setColumnHidden(2, True)
        # databaseAbsPath
        self.setColumnHidden(3, True)
        # dataType
        self.setColumnHidden(4, True)

        # Should be last column above + 1
        self.cbColumn = 5



    def parameterCellClicked(self, row: int,
                                   column: int) -> None:
        """
        Handle event when user click on the cell containing the checkbox.
        Basically toggle the checkbox and launch the event associated to the
        checkbox

        Parameters
        ----------
            row, column : int, int
            Row and column where the user clicked
        """

        # If user clicks on the cell containing the checkbox
        if column==self.cbColumn:
            cb = self.cellWidget(row, self.cbColumn)
            cb.toggle()



    def parameterClicked(self,
                         state              : bool,
                         cb                 : QtWidgets.QCheckBox,
                         dependentParamName : str,
                         runId              : int,
                         curveId            : str,
                         plotTitle          : str,
                         windowTitle        : str,
                         paramDependent     : dict,
                         plotRef            : str,
                         databaseAbsPath    : str,
                         dataType           : str) -> None:
        """
        Handle event when user clicked on data line.
        Either get data and display them or remove the data depending on state.

        Parameters
        ----------
        state : bool
            State of the checkbox
        dependentParamName : str
            Name of the dependent parameter from which data will be downloaded.
        runId : int
            Data run id in the current database
        curveId : str
            Id of the curve, see getCurveId.
        plotTitle : str
            Plot title, see getPlotTitle.
        windowTitle : str
            Window title, see getWindowTitle.
        paramDependent : dict
            Dependent parameter the user wants to see the data.
            This should be a qcodes dependent parameter dict.
        plotRef : str
            Reference to a plot window, see getPlotRef.
        """

        if state:

            if len(paramDependent['depends_on'])>2:

                self.signalSendStatusBarMessage.emit('Plotter does not handle data whose dim>2', 'red')
                return
            else:
                self.signalAddCurve.emit(curveId,
                                         databaseAbsPath,
                                         dataType,
                                         dependentParamName,
                                         plotRef,
                                         plotTitle,
                                         runId,
                                         windowTitle,
                                         cb)
        # If the checkbox is unchecked, we remove the plotted data
        else:

            self.signalRemoveCurve.emit(plotRef, curveId)



    @QtCore.pyqtSlot(str, str, str, str, str, str, int, str, QtWidgets.QCheckBox, QtWidgets.QProgressBar)
    def getData(self, curveId: str,
                      databaseAbsPath: str,
                      dataType: str,
                      dependentParamName: str,
                      plotRef: str,
                      plotTitle: str,
                      runId: int,
                      windowTitle: str,
                      cb: QtWidgets.QCheckBox,
                      progressBar: QtWidgets.QProgressBar) -> None:
        """
        Called when user wants to plot qcodes data.
        Create a progress bar in the status bar.
        Launched a thread which will download the data, display the progress in
        the progress bar and call addPlot when the data are downloaded.

        Parameters
        ----------
        runId : int
            Data run id in the current database
        curveId : str
            Id of the curve, see getCurveId.
        plotTitle : str
            Plot title, see getPlotTitle.
        windowTitle : str
            Window title, see getWindowTitle.
        plotRef : str
            Reference of the plot window.
        dependentParamName : str
            Name of the dependent parameter from which data will be downloaded.
        """

        # Flag
        self._dataDowloadingFlag = True

        cb.setEnabled(False)
        QtTest.QTest.qWait(100)

        if dataType=='qcodes':
            worker = LoadDataFromRunThread(curveId,
                                           databaseAbsPath,
                                           dependentParamName,
                                           plotRef,
                                           plotTitle,
                                           runId,
                                           windowTitle,
                                           cb,
                                           progressBar)
            # Connect signals
            # To update the status bar
            worker.signal.sendStatusBarMessage.connect(self.signalSendStatusBarMessage)
            # To update the progress bar
            worker.signal.updateProgressBar.connect(self.signalUpdateProgressBar)
            # If data download failed
            worker.signal.loadedDataEmpty.connect(self.signalLoadedDataEmpty)
            # When data download is done
            worker.signal.loadedDataFull.connect(self.signalLoadedDataFull)

            # Execute the thread
            self.threadpool.start(worker)
        elif dataType=='csv':

            self.signalCSVLoadData.emit(curveId,
                                        databaseAbsPath,
                                        dependentParamName,
                                        plotRef,
                                        plotTitle,
                                        runId,
                                        windowTitle,
                                        cb,
                                        progressBar)
        elif dataType=='bluefors':

            self.signalBlueForsLoadData.emit(curveId,
                                             databaseAbsPath,
                                             dependentParamName,
                                             plotRef,
                                             plotTitle,
                                             runId,
                                             windowTitle,
                                             cb,
                                             progressBar)



    ############################################################################
    #
    #
    #                           Called from thread
    #
    #
    ############################################################################



    @QtCore.pyqtSlot(QtWidgets.QCheckBox)
    def enableCheck(self, cb: QtWidgets.QCheckBox) -> None:

        cb.setEnabled(True)



    ############################################################################
    #
    #
    #                           Called from other widgets
    #
    #
    ############################################################################



    @QtCore.pyqtSlot(int, list, dict, str, str, str, str, bool)
    def slotFillTableWidgetParameter(self, runId: int,
                                           paramDependentList: list,
                                           snapshotDict: dict,
                                           experimentName: str,
                                           runName: str,
                                           databaseAbsPath: str,
                                           dataType: str,
                                           doubleClick: bool) -> None:

        ## Fill the tableWidgetParameters with the run parameters
        clearTableWidget(self)
        self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.Fixed)
        self.verticalHeader().setResizeMode(QtWidgets.QHeaderView.Fixed)


        plotTitle       = getPlotTitle(databaseAbsPath=databaseAbsPath,
                                       runId=runId,
                                       experimentName=experimentName)
        windowTitle     = getWindowTitle(databaseAbsPath=databaseAbsPath,
                                         runId=runId,
                                         runName=runName)

        for paramDependent in paramDependentList:

            curveId         = getCurveId(databaseAbsPath=databaseAbsPath,
                                        name=paramDependent['name'],
                                        runId=runId)
            plotRef         = getPlotRef(databaseAbsPath=databaseAbsPath,
                                        paramDependent=paramDependent,
                                        runId=runId)

            rowPosition = self.rowCount()
            self.insertRow(rowPosition)
            self.signaladdRow.emit(runId,
                                   paramDependent,
                                   experimentName,
                                   curveId,
                                   plotRef,
                                   plotTitle,
                                   windowTitle,
                                   databaseAbsPath,
                                   dataType,
                                   rowPosition)


        self.setSortingEnabled(True)
        self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.verticalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        ## Fill the listWidgetMetada with the station snapshot
        self.signalLineEditSnapshotEnabled.emit(True)
        self.signalLabelSnapshotEnabled.emit(True)

        # Update the run snapshot
        self.signalCleanSnapshot.emit()
        self.signalAddSnapshot.emit(snapshotDict)
        self.signalUpdateLabelCurrentSnapshot.emit(str(runId))
        self.signalUpdateLabelCurrentRun.emit(str(runId))


        ## Update label
        self.signalSendStatusBarMessage.emit('Ready', 'green')

        # If a double click is detected, we launch a plot of the first parameter
        if doubleClick:
            self.parameterCellClicked(0, self.cbColumn)



    @QtCore.pyqtSlot(int, dict, str, str, str, str, str, str, str, int, bool)
    def slotAddRow(self, runId: int,
                         paramDependent: dict,
                         experimentName: str,
                         curveId: str,
                         plotRef: str,
                         plotTitle: str,
                         windowTitle: str,
                         databaseAbsPath: str,
                         dataType: str,
                         rowPosition: int,
                         isParameterPlotted: bool) -> None:
        """
        """

        runIdStr = str(runId)

        cb = QtWidgets.QCheckBox()

        if isParameterPlotted:
            cb.setChecked(True)

        self.setItem(rowPosition, 0, QtWidgets.QTableWidgetItem(runIdStr))
        self.setItem(rowPosition, 1, QtWidgets.QTableWidgetItem(experimentName))
        self.setItem(rowPosition, 2, QtWidgets.QTableWidgetItem(paramDependent['name']))
        self.setItem(rowPosition, 3, QtWidgets.QTableWidgetItem(databaseAbsPath))
        self.setItem(rowPosition, 4, QtWidgets.QTableWidgetItem(dataType))
        self.setCellWidget(rowPosition, 5, cb)
        self.setItem(rowPosition, 6, QtWidgets.QTableWidgetItem(paramDependent['label']))
        self.setItem(rowPosition, 7, QtWidgets.QTableWidgetItem(paramDependent['unit']))


        independentString = config['sweptParameterSeparator'].join(paramDependent['depends_on'])
        self.setCellWidget(rowPosition, 8, QtWidgets.QLabel(independentString))

        # Each checkbox at its own event attached to it
        cb.toggled.connect(lambda state,
                                  cb                    = cb,
                                  dependentParamName    = paramDependent['name'],
                                  runId                 = runId,
                                  curveId               = curveId,
                                  plotTitle             = plotTitle,
                                  windowTitle           = windowTitle,
                                  dependent             = paramDependent,
                                  plotRef               = plotRef,
                                  databaseAbsPath       = databaseAbsPath,
                                  dataType              = dataType: self.parameterClicked(state,
                                                                                          cb,
                                                                                          dependentParamName,
                                                                                          runId,
                                                                                          curveId,
                                                                                          plotTitle,
                                                                                          windowTitle,
                                                                                          dependent,
                                                                                          plotRef,
                                                                                          databaseAbsPath,
                                                                                          dataType))



    @QtCore.pyqtSlot(int)
    def slotUncheck(self, curveId: int) -> None:
        """
        Called by plot when a plot is closed.
        Check if the curve display on the plot is currently check.
        Uncheck it if it is the case.
        """

        for row in range(self.rowCount()):

            runId = int(self.item(row, 0).text())
            parameterName = self.item(row, 2).text()
            databaseAbsPath = self.item(row, 3).text()

            rowCurveId = getCurveId(databaseAbsPath=databaseAbsPath,
                                    name=parameterName,
                                    runId=runId)

            if rowCurveId==curveId:
                # Uncheck the checkBox without triggering an event
                self.cellWidget(row, self.cbColumn).setCheckable(False)
                self.cellWidget(row, self.cbColumn).setChecked(False)
                self.cellWidget(row, self.cbColumn).setCheckable(True)



    @QtCore.pyqtSlot()
    def slotClearTable(self) -> None:

        clearTableWidget(self)
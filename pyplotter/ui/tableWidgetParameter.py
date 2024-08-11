from PyQt5 import QtCore, QtGui, QtWidgets
import os
import numpy as np

from ..sources.config import loadConfigCurrent
config = loadConfigCurrent()
from ..sources.workers.loadDataFromRun import LoadDataFromRunThread
from ..sources.workers.loadLabradDataFromRun import LoadDataFromRunThread as LoadLabradDataFromRunThread
from ..sources.labradDatavault import LabradDataset
from ..sources.functions import (clearTableWidget,
                                 getCurveId,
                                 getPlotRef,
                                 getPlotTitle,
                                 getWindowTitle,
                                 isLabradFolder,
                                 isQcodesData
                                 )


# Get the folder path for pictures
PICTURESPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pictures')

class TableWidgetParameter(QtWidgets.QTableWidget):
    """
    Custom class to be able to sort numerical table column
    """

    signalSendStatusBarMessage       = QtCore.pyqtSignal(str, str)
    signalUpdateProgressBar          = QtCore.pyqtSignal(int, float, str)
    signalRemoveProgressBar          = QtCore.pyqtSignal(int)
    signalAddPlot                    = QtCore.pyqtSignal(int, str, str, str, str, str, tuple, str, str, str, str, str, str, int, int, int, int)
    # Update a 1d plotDataItem
    signalUpdate1d                   = QtCore.pyqtSignal(str, str, str, np.ndarray, np.ndarray, bool, bool)
    # Update a 2d ImageView
    signalUpdate2d                   = QtCore.pyqtSignal(str, np.ndarray, np.ndarray, np.ndarray)

    signalAddCurve                   = QtCore.pyqtSignal(str, str, str, str, str, str, int, str, QtWidgets.QCheckBox)
    signalRemoveCurve                = QtCore.pyqtSignal(str, str)
    signalCleanSnapshot              = QtCore.pyqtSignal()
    signalAddSnapshot                = QtCore.pyqtSignal(dict)
    signalLineEditSnapshotEnabled    = QtCore.pyqtSignal(bool)
    signalLabelSnapshotEnabled       = QtCore.pyqtSignal(bool)
    signalUpdateLabelCurrentSnapshot = QtCore.pyqtSignal(str)
    signalUpdateLabelCurrentRun      = QtCore.pyqtSignal(str)
    signaladdRow                     = QtCore.pyqtSignal(int, dict, str, str, str, str, str, str, str, str, int)

    signalLoadedDataEmpty  = QtCore.pyqtSignal(QtWidgets.QCheckBox, int)
    signalLoadedDataFull   = QtCore.pyqtSignal(int, str, str, str, str, str, QtWidgets.QCheckBox, int, tuple, str, str, str, str, str, str, bool)
    signalCSVLoadData      = QtCore.pyqtSignal(str, str, str, str, str, int, str, QtWidgets.QCheckBox, int)
    signalNpzLoadData      = QtCore.pyqtSignal(str, str, str, str, str, int, str, QtWidgets.QCheckBox, int)
    signalBlueForsLoadData = QtCore.pyqtSignal(str, str, str, str, str, int, str, QtWidgets.QCheckBox, int)



    def __init__(self, parent=None) -> None:
        super(TableWidgetParameter, self).__init__(parent)

        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        self.cellClicked.connect(self.parameterCellClicked)

        self.threadpool = QtCore.QThreadPool()

        # Flag
        self._dataDowloadingFlag = False


    def first_call(self):

        self._columnIndexes = {'runId' : 0,
                               'experimentName' : 1,
                               'parameterName' : 2,
                               'databaseAbsPath' : 3,
                               'dataType' : 4,
                               'plotted' : 5,
                               'axis' : 6,
                               'unit' : 7,
                               'shape' : 8,
                               'sweptParameters' : 9,
                               }
        self.setColumnCount(len(self._columnIndexes))

        ## Only used to propagate information
        # runId
        item = QtWidgets.QTableWidgetItem()
        item.setText('runId')
        self.setHorizontalHeaderItem(self._columnIndexes['runId'], item)
        self.setColumnHidden(self._columnIndexes['runId'], True)
        # experimentName
        item = QtWidgets.QTableWidgetItem()
        item.setText('experimentName')
        self.setHorizontalHeaderItem(self._columnIndexes['experimentName'], item)
        self.setColumnHidden(self._columnIndexes['experimentName'], True)
        # parameterName
        item = QtWidgets.QTableWidgetItem()
        item.setText('parameterName')
        self.setHorizontalHeaderItem(self._columnIndexes['parameterName'], item)
        self.setColumnHidden(self._columnIndexes['parameterName'], True)
        # databaseAbsPath
        item = QtWidgets.QTableWidgetItem()
        item.setText('databaseAbsPath')
        self.setHorizontalHeaderItem(self._columnIndexes['databaseAbsPath'], item)
        self.setColumnHidden(self._columnIndexes['databaseAbsPath'], True)
        # dataType
        item = QtWidgets.QTableWidgetItem()
        item.setText('dataType')
        self.setHorizontalHeaderItem(self._columnIndexes['dataType'], item)
        self.setColumnHidden(self._columnIndexes['dataType'], True)

        ## Column display
        # plotted
        item = QtWidgets.QTableWidgetItem()
        item.setText('plotted')
        self.setHorizontalHeaderItem(self._columnIndexes['plotted'], item)
        # axis
        item = QtWidgets.QTableWidgetItem()
        item.setText('axis')
        self.setHorizontalHeaderItem(self._columnIndexes['axis'], item)
        # unit
        item = QtWidgets.QTableWidgetItem()
        item.setText('unit')
        self.setHorizontalHeaderItem(self._columnIndexes['unit'], item)
        # shaoe
        item = QtWidgets.QTableWidgetItem()
        item.setText('shape')
        self.setHorizontalHeaderItem(self._columnIndexes['shape'], item)
        # swept parameters
        item = QtWidgets.QTableWidgetItem()
        item.setText('swept parameters')
        self.setHorizontalHeaderItem(self._columnIndexes['sweptParameters'], item)



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
        if column==self._columnIndexes['plotted']:
            cb = self.cellWidget(row, self._columnIndexes['plotted'])
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
        dataType : str
            either "qcodes", "csv", "bluefors"
        """

        if state:

            if len(paramDependent['depends_on'])>2:

                self.signalSendStatusBarMessage.emit('Plotter does not handle data whose dim>2', 'red')
                cb.toggle()
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



    @QtCore.pyqtSlot(str, str, str, str, str, str, int, str, QtWidgets.QCheckBox, int)
    def getData(self, curveId: str,
                      databaseAbsPath: str,
                      dataType: str,
                      dependentParamName: str,
                      plotRef: str,
                      plotTitle: str,
                      runId: int,
                      windowTitle: str,
                      cb: QtWidgets.QCheckBox,
                      progressBarId: int) -> None:
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
        dataType : str
            either "qcodes", "csv", "bluefors"
        """

        # Flag
        self._dataDowloadingFlag = True

        cb.setEnabled(False)
        QtCore.QThread.msleep(100)

        if dataType == 'qcodes':
            worker = LoadDataFromRunThread(curveId,
                                           databaseAbsPath,
                                           dependentParamName,
                                           plotRef,
                                           plotTitle,
                                           runId,
                                           windowTitle,
                                           cb,
                                           progressBarId)
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

        # Labrad data loading will take a while when huge data/parameters are stored in HDF5 files
        # We use threading just like what is for qcodes data to avoid frozen windows.
        elif dataType == 'Labrad':
            worker = LoadLabradDataFromRunThread(curveId,
                                           databaseAbsPath,
                                           dependentParamName,
                                           plotRef,
                                           plotTitle,
                                           runId,
                                           windowTitle,
                                           cb,
                                           progressBarId)
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
                                        progressBarId)
        elif dataType=='npz':

            self.signalNpzLoadData.emit(curveId,
                                        databaseAbsPath,
                                        dependentParamName,
                                        plotRef,
                                        plotTitle,
                                        runId,
                                        windowTitle,
                                        cb,
                                        progressBarId)
        elif dataType=='bluefors':

            self.signalBlueForsLoadData.emit(curveId,
                                             databaseAbsPath,
                                             dependentParamName,
                                             plotRef,
                                             plotTitle,
                                             runId,
                                             windowTitle,
                                             cb,
                                             progressBarId)



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


    @QtCore.pyqtSlot(int, list, dict, dict, str, str, str, str, bool)
    def slotFillTableWidgetParameter(self, runId: int,
                                           paramDependentList: list,
                                           snapshotDict: dict,
                                           shapesDict: dict,
                                           experimentName: str,
                                           runName: str,
                                           databaseAbsPath: str,
                                           dataType: str,
                                           doubleClick: bool) -> None:

        ## Fill the tableWidgetParameters with the run parameters
        clearTableWidget(self)
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

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
                                   str(shapesDict[paramDependent['name']]).replace('[', '').replace(']', ''),
                                   experimentName,
                                   curveId,
                                   plotRef,
                                   plotTitle,
                                   windowTitle,
                                   databaseAbsPath,
                                   dataType,
                                   rowPosition)

        self.setSortingEnabled(True)
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

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

        if doubleClick:
            if isQcodesData(databaseAbsPath):
            # launch the first dependent plot
                self.parameterCellClicked(0, self._columnIndexes['plotted'])
            elif isLabradFolder(databaseAbsPath):
            # launch a default plot of the Labrad Data (defined in "plot_dependents" parameter)
            # To avoid displaying too many progress bar, user config['progressBarMaxNb'] default to 3
            # See config.py for details -lxiang
                self.dataset = LabradDataset(databaseAbsPath)
                self.dataset.loadDataset(runId)
                dep_indexes, _ = self.dataset.getPlotDependents()
                for dep_i in dep_indexes:
                    self.parameterCellClicked(dep_i, self._columnIndexes['plotted'])

    @QtCore.pyqtSlot(int, dict, str, str, str, str, str, str, str, str, int, bool)
    def slotAddRow(self, runId: int,
                         paramDependent: dict,
                         shape: str,
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
        dataType : str
            either "qcodes", "csv", "bluefors"
        """

        runIdStr = str(runId)

        cb = QtWidgets.QCheckBox()

        if isParameterPlotted:
            cb.setChecked(True)

        self.setItem(rowPosition, self._columnIndexes['runId'], QtWidgets.QTableWidgetItem(runIdStr))
        self.setItem(rowPosition, self._columnIndexes['experimentName'], QtWidgets.QTableWidgetItem(experimentName))
        self.setItem(rowPosition, self._columnIndexes['parameterName'], QtWidgets.QTableWidgetItem(paramDependent['name']))
        self.setItem(rowPosition, self._columnIndexes['databaseAbsPath'], QtWidgets.QTableWidgetItem(databaseAbsPath))
        self.setItem(rowPosition, self._columnIndexes['dataType'], QtWidgets.QTableWidgetItem(dataType))
        self.setCellWidget(rowPosition, self._columnIndexes['plotted'], cb)
        self.setItem(rowPosition, self._columnIndexes['axis'], QtWidgets.QTableWidgetItem(paramDependent['label']))
        self.setItem(rowPosition, self._columnIndexes['unit'], QtWidgets.QTableWidgetItem(paramDependent['unit']))
        self.setItem(rowPosition, self._columnIndexes['shape'], QtWidgets.QTableWidgetItem(shape))

        independentString = config['sweptParameterSeparator'].join(paramDependent['depends_on'])
        self.setCellWidget(rowPosition, self._columnIndexes['sweptParameters'], QtWidgets.QLabel(independentString))

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
                self.cellWidget(row, self._columnIndexes['plotted']).setCheckable(False)
                self.cellWidget(row, self._columnIndexes['plotted']).setChecked(False)
                self.cellWidget(row, self._columnIndexes['plotted']).setCheckable(True)



    @QtCore.pyqtSlot()
    def slotClearTable(self) -> None:
        clearTableWidget(self)


    @QtCore.pyqtSlot(str)
    def slotNpzIncorrectSize(self, dependentParamName: str) -> None:
        """
        Signal from the widgetNpz.
        Is sent when the npz y parameter can't be displayed as function of the x
        one since they do not share the same size.

        We change the display of the dependent parameter row that can't be
        plotted.

        Args:
            dependentParamName: the dependent parameter the user tried to plot
        """

        # Find the row from which the parameter was clicked on
        targetRow = 0
        for row in range(self.rowCount()):
            item = self.item(row, self._columnIndexes['axis'])
            if dependentParamName==item.text():
                targetRow = row
                break

        # Modify the displayed items
        cols = [self._columnIndexes['axis'],
                self._columnIndexes['unit'],
                self._columnIndexes['shape']]
        for col in cols:
            item = self.item(targetRow, col)
            item.setBackground(QtGui.QBrush(QtCore.Qt.black))
            item.setForeground(QtGui.QBrush(QtCore.Qt.red))

        # Modify the displayed label
        label = self.cellWidget(targetRow, self._columnIndexes['sweptParameters'])
        label.setStyleSheet("QLabel { background-color: black;color: red;}")

        # Clear the user selection
        self.clearSelection()



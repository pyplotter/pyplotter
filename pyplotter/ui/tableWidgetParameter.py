# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets, QtGui
from typing import List, Callable, Union, Optional
import os
import numpy as np

from pyplotter.sources.plot_app import PlotApp

from ..sources.config import loadConfigCurrent
config = loadConfigCurrent()
from ..sources.runpropertiesextra import RunPropertiesExtra
from .tableWidgetItemNumOrdered import TableWidgetItemNumOrdered
from ..sources.workers.loadDataBase import LoadDataBaseThread
from ..sources.workers.loadDataFromRun import LoadDataFromRunThread
from ..sources.functions import (clearTableWidget,
                                 getCurveId,
                                 getPlotRef,
                                 getPlotTitle,
                                 getWindowTitle)
from ..sources.plot_app import PlotApp
from ..sources.plot_1d_app import Plot1dApp
from ..sources.plot_2d_app import Plot2dApp
from ..sources.pyqtgraph import pg

# Get the folder path for pictures
PICTURESPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pictures')

class TableWidgetParameter(QtWidgets.QTableWidget):
    """
    Custom class to be able to sort numerical table column
    """

    signalSendStatusBarMessage       = QtCore.pyqtSignal(str, str)
    signalUpdateProgressBar          = QtCore.pyqtSignal(QtWidgets.QProgressBar, int, str)
    signalRemoveProgressBar          = QtCore.pyqtSignal(QtWidgets.QProgressBar)
    signalParameterClick             = QtCore.pyqtSignal(str, str, str, str, str, int, str)
    signalAddPlotToRefs              = QtCore.pyqtSignal(str, Plot1dApp)
    signalCleanSnapshot              = QtCore.pyqtSignal()
    signalAddSnapshot                = QtCore.pyqtSignal(dict)
    signalLineEditSnapshotEnabled    = QtCore.pyqtSignal(bool)
    signalLabelSnapshotEnabled       = QtCore.pyqtSignal(bool)
    signalUpdateLabelCurrentSnapshot = QtCore.pyqtSignal(str)
    signalUpdateLabelCurrentRun      = QtCore.pyqtSignal(str)
    signalAddCheckbox                = QtCore.pyqtSignal(int, dict, str, str, str, str, str, str, int)

    # Propagation of the plot signals to the main app
    # signalClosePlot           = QtCore.pyqtSignal(str, Plot1dApp)
    # signalAddCurveToRefs           = QtCore.pyqtSignal(str, pg.PlotDataItem)
    signalLoadedDataFull = QtCore.pyqtSignal(int, str, str, str, str, str, QtWidgets.QProgressBar, tuple, str, str, str, str, str, str)



    def __init__(self, parent=None) -> None:
        super(TableWidgetParameter, self).__init__(parent)

        self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        self.cellClicked.connect(self.parameterCellClicked)

        self.threadpool = QtCore.QThreadPool()

        # {plotRef : plotApp}
        self._plotRefs = {}

        # Flag
        self._dataDowloadingFlag = False


    def first_call(self):
        ## Only used to propagate information
        # runId
        self.setColumnHidden(0, True)
        # experimentName
        self.setColumnHidden(1, True)



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
        if column==2:
            cb = self.cellWidget(row, 2)
            cb.toggle()



    def parameterClicked(self,
                         state              : bool,
                         dependentParamName : str,
                         runId              : int,
                         curveId            : str,
                         plotTitle          : str,
                         windowTitle        : str,
                         paramDependent     : dict,
                         plotRef            : str,
                         databaseAbsPath    : str) -> None:
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

        # If the checkbutton is checked, we downlad and plot the data
        if state:

            if len(paramDependent['depends_on'])>2:

                self.signalSendStatusBarMessage.emit('Plotter does not handle data whose dim>2', 'red')
                return
            else:
                self.signalParameterClick.emit(curveId,
                                               databaseAbsPath,
                                               dependentParamName,
                                               plotRef,
                                               plotTitle,
                                               runId,
                                               windowTitle)

                # self.getData(runId              = runId,
                #              curveId            = curveId,
                #              plotTitle          = plotTitle,
                #              windowTitle        = windowTitle,
                #              plotRef            = plotRef,
                #              databaseAbsPath    = databaseAbsPath,
                #              dependentParamName = dependentParamName)

        # If the checkbox is unchecked, we remove the plotted data
        else:

            self.removePlot(plotRef = plotRef,
                            curveId = curveId)




    def getData(self, curveId: str,
                      databaseAbsPath: str,
                      dependentParamName: str,
                      plotRef: str,
                      plotTitle: str,
                      runId: int,
                      windowTitle: str,
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

        worker = LoadDataFromRunThread(curveId,
                                       databaseAbsPath,
                                       dependentParamName,
                                       plotRef,
                                       plotTitle,
                                       runId,
                                       windowTitle,
                                       progressBar)
        # Connect signals
        # To update the status bar
        worker.signal.sendStatusBarMessage.connect(self.signalSendStatusBarMessage)
        # To update the progress bar
        worker.signal.updateProgressBar.connect(self.signalUpdateProgressBar)
        # If data download failed
        worker.signal.loadedDataEmpty.connect(self.loadedDataEmpty)
        # When data download is done
        worker.signal.loadedDataFull.connect(self.signalLoadedDataFull)

        # Execute the thread
        self.threadpool.start(worker)



    # def addPlot(self, plotRef            : str,
    #                   databaseAbsPath    : str,
    #                   data               : List[np.ndarray],
    #                   xLabelText         : str,
    #                   xLabelUnits        : str,
    #                   yLabelText         : str,
    #                   yLabelUnits        : str,
    #                   runId              : int,
    #                   curveId            : str,
    #                   plotTitle          : str,
    #                   windowTitle        : str,
    #                   linkedTo2dPlot     : bool=False,
    #                   curveLegend        : Optional[str]=None,
    #                   hidden             : bool=False,
    #                   curveLabel         : Optional[str]=None,
    #                   curveUnits         : Optional[str]=None,
    #                   timestampXAxis     : Optional[bool]=None,
    #                   livePlot           : bool=False,
    #                   progressBar        : Optional[QtWidgets.QProgressBar]=None,
    #                   zLabelText         : Optional[str]=None,
    #                   zLabelUnits        : Optional[str]=None,
    #                   histogram          : Optional[bool]=False) -> None:
    #     """
    #     Methods called once the data are downloaded to add a plot of the data.
    #     Discriminate between 1d and 2d plot through the length of data list.
    #     For 1d plot, data having the sample plotRef do not launch a new plot
    #     window but instead are plotted in the window sharing the same plotRef.
    #     Once the data are plotted, run updateList1dCurvesLabels.

    #     Parameters
    #     ----------
    #     plotRef : str
    #         Reference of the plot.
    #     progressBar : str
    #         Key to the progress bar in the dict progressBars.
    #     data : list
    #         For 1d plot: [xData, yData]
    #         For 2d plot: [xData, yData, zData]
    #     xLabelText : str
    #         Label text for the xAxix.
    #     xLabelUnits : str
    #         Label units for the xAxix.
    #     yLabelText : str
    #         Label text for the yAxix.
    #     yLabelUnits : str
    #         Label units for the yAxix.
    #     runId : int
    #         Data run id in the current database
    #     curveId : str
    #         Id of the curve, see getCurveId.
    #     plotTitle : str
    #         Plot title, see getPlotTitle.
    #     windowTitle : str
    #         Window title, see getWindowTitle.
    #     zLabelText : str, default None
    #         Only for 2d data.
    #         Label text for the zAxis.
    #     zLabelUnits : str, default None
    #         Only for 2d data.
    #         Label units for the zAxis.
    #     """

    #     # If the method is called from a thread with a progress bar, we remove
    #     # it
    #     if progressBar is not None:
    #         self.signalRemoveProgressBar.emit(progressBar)

    #     # If data is None it means the data download encounter an error.
    #     # We do not add plot
    #     if data is None:
    #         return

    #     self.signalSendStatusBarMessage.emit('Launching '+str(len(data)-1)+'d plot', 'orange')


    #     # If some parameters are not given, we find then from the GUI
    #     # if cleanCheckBox is None:
    #     #     cleanCheckBox = self.cleanCheckBox


    #     # 1D plot
    #     if len(data)==2:

    #         # Specific 1d optional parameter
    #         # print(timestampXAxis)
    #         # if timestampXAxis is None:
    #         #     timestampXAxis = self.LoadBlueFors.isBlueForsFolder(self._currentDatabase)
    #         # print(self.LoadBlueFors.isBlueForsFolder(self._currentDatabase))
    #         # print(timestampXAxis)
    #         # If the plotRef is not stored we launched a new window
    #         # Otherwise we add a new PlotDataItem on an existing plot1dApp
    #         if plotRef not in self._plotRefs:


    #             p = Plot1dApp(x                  = data[0],
    #                           y                  = data[1],
    #                           title              = plotTitle,
    #                           xLabelText         = xLabelText,
    #                           xLabelUnits        = xLabelUnits,
    #                           yLabelText         = yLabelText,
    #                           yLabelUnits        = yLabelUnits,
    #                           windowTitle        = windowTitle,
    #                           runId              = runId,
    #                           plotRef            = plotRef,
    #                           databaseAbsPath    = databaseAbsPath,
    #                           curveId            = curveId,
    #                           curveLegend        = curveLegend,
    #                           linkedTo2dPlot     = linkedTo2dPlot,
    #                           livePlot           = livePlot,
    #                           timestampXAxis     = timestampXAxis,
    #                           histogram          = histogram)

    #             self.signalAddPlotToRefs.emit(plotRef, p)
    #             self._plotRefs[plotRef] = p
    #             self._plotRefs[plotRef].show()
    #         else:

    #             self._plotRefs[plotRef].addPlotDataItem(x                  = data[0],
    #                                                     y                  = data[1],
    #                                                     curveId            = curveId,
    #                                                     curveXLabel        = xLabelText,
    #                                                     curveXUnits        = xLabelUnits,
    #                                                     curveYLabel        = yLabelText,
    #                                                     curveYUnits        = yLabelUnits,
    #                                                     curveLegend        = yLabelText,
    #                                                     hidden             = hidden)


    #     # 2D plot
    #     elif len(data)==3:

    #         # Determine if we should open a new Plot2dApp
    #         if plotRef not in self._plotRefs:
    #             p = Plot2dApp(x               = data[0],
    #                           y               = data[1],
    #                           z               = data[2],
    #                           title           = plotTitle,
    #                           xLabelText      = xLabelText,
    #                           xLabelUnits     = xLabelUnits,
    #                           yLabelText      = yLabelText,
    #                           yLabelUnits     = yLabelUnits,
    #                           zLabelText      = zLabelText,
    #                           zLabelUnits     = zLabelUnits,
    #                           windowTitle     = windowTitle,
    #                           runId           = runId,
    #                           plotRef         = plotRef,
    #                           databaseAbsPath = databaseAbsPath,
    #                           livePlot        = livePlot)

    #             self._plotRefs[plotRef] = p
    #             self._plotRefs[plotRef].show()

    #     self.signalSendStatusBarMessage.emit('Ready', 'green')

    #     # p.signalClosePlot.connect(self.signalClosePlot)
    #     # self.signalAddCurveToRefs.emit(plotRef, self._plotRefs[plotRef].curves[curveId])
    #     # self.updateList1dCurvesLabels()

    #     # Flag
    #     self._dataDowloadingFlag = False



    def removePlot(self, plotRef: str,
                         curveId: str) -> None:
        """
        Method call when data are remove from the GUI.
        If the data plot window is open, close it.
        Then remove the reference of the plot window from self._plotRefs.

        Once the data are closed, run updateList1dCurvesLabels.

        Parameters
        ----------
        plotRef : str
            Reference of the plot, see getPlotRef.
        curveId : str
            reference of the curve, see getCurveId
        """

        if self._plotRefs[plotRef].plotType=='1d':
            # If there is more than one curve, we remove one curve
            if self._plotRefs[plotRef].nbPlotDataItemFromData()>1:
                self._plotRefs[plotRef].removePlotDataItem(curveId=curveId)
            # If there is one curve we close the plot window
            else:
                self._plotRefs[plotRef].o()
                del(self._plotRefs[plotRef])

            # Update the list of currently plotted dependent parametered on all
            # the plotted window
            self.updateList1dCurvesLabels()
        elif self._plotRefs[plotRef].plotType=='2d':
            self._plotRefs[plotRef].o()
            del(self._plotRefs[plotRef])




    def cleanCheckBox(self, plotRef     : str,
                            windowTitle : str,
                            runId       : int,
                            label       : str) -> None:
        """
        Method called by the plot1d or plot2d plot when the user close the plot
        window. We propagate that event to the mainWindow to uncheck the
        checkbox and clean the reference, see self._plotRefs.

        Parameters:
        plotRef : str
            Reference of the plot, see getplotRef.
        windowTitle : str
            Window title, see getWindowTitle.
        runId : int
            Data run id of the database.
        label : str
            Label of the dependent parameter.
            Will be empty for signal from Plot1dApp since this parameter is only
            usefull for Plot2dApp.
        """

        # If the close plot window is a liveplot one
        if plotRef in self.getLivePlotRef():
            # if hasattr(self, '_livePlotDataSet'):
            if self._plotRefs[plotRef].plotType=='1d':
                curveIds = list(self._plotRefs[plotRef].curves.keys())
                [self.removePlot(plotRef, curveId) for curveId in curveIds]
            else:
                self.removePlot(plotRef, '')
            # del(self._livePlotDataSet)
        else:
            if self.getWindowTitle(runId=runId, runName=self.getRunName())==windowTitle and self.getRunId()==runId:

                # If 1d plot
                if self._plotRefs[plotRef].plotType=='1d':

                    # If the current displayed parameters correspond to the one which has
                    # been closed, we uncheck all the checkbox listed in the table
                    for row in range(self.tableWidgetParameters.rowCount()):
                        widget = self.tableWidgetParameters.cellWidget(row, 2)
                        widget.setChecked(False)
                # If 2d plot
                else:
                    # We uncheck only the plotted parameter
                    for row in range(self.tableWidgetParameters.rowCount()):
                        if label==self.tableWidgetParameters.item(row, 3).text():
                            widget = self.tableWidgetParameters.cellWidget(row, 2)
                            widget.setChecked(False)

    ############################################################################
    #
    #
    #                           Called from thread
    #
    #
    ############################################################################


    @QtCore.pyqtSlot()
    def loadedDataEmpty(self) -> None:
        """
        Method called by LoadDataFromRunThread when the data download is done but the
        database is empty.
        We signal the data downloading being done by setting the flag False.
        This will allow the next live plot iteration to try downloading the data
        again.
        """

        self._dataDowloadingFlag = False



    @QtCore.pyqtSlot(int, str, str, str, str, str, QtWidgets.QProgressBar, tuple, str, str, str, str, str, str)
    def loadedDataFull(self, runId          : int,
                      curveId        : str,
                      plotTitle      : str,
                      windowTitle    : str,
                      plotRef        : str,
                      databaseAbsPath: str,
                      progressBar    : QtWidgets.QProgressBar,
                      data           : List[np.ndarray],
                      xLabelText     : str,
                      xLabelUnits    : str,
                      yLabelText     : str,
                      yLabelUnits    : str,
                      zLabelText     : str,
                      zLabelUnits    : str) -> None:
        """
        Call from loaddata thread.
        Just past the argument to the addPlot method.
        Usefull because progressBar is an optional parameter
        """

        self.addPlot(plotRef        = plotRef,
                     databaseAbsPath= databaseAbsPath,
                     data           = data,
                     xLabelText     = xLabelText,
                     xLabelUnits    = xLabelUnits,
                     yLabelText     = yLabelText,
                     yLabelUnits    = yLabelUnits,
                     zLabelText     = zLabelText,
                     zLabelUnits    = zLabelUnits,
                     runId          = runId,
                     curveId        = curveId,
                     plotTitle      = plotTitle,
                     windowTitle    = windowTitle,
                     progressBar    = progressBar)




    ############################################################################
    #
    #
    #                           Called from other widgets
    #
    #
    ############################################################################



    @QtCore.pyqtSlot(int, list, dict, str, str, str, bool)
    def runClick(self, runId: int,
                       paramDependentList: list,
                       snapshotDict: dict,
                       experimentName: str,
                       runName: str,
                       databaseAbsPath: str,
                       doubleClicked: bool) -> None:

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
            self.signalAddCheckbox.emit(runId,
                                        paramDependent,
                                        experimentName,
                                        curveId,
                                        plotRef,
                                        plotTitle,
                                        windowTitle,
                                        databaseAbsPath,
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
        self.signalUpdateLabelCurrentRun     .emit(str(runId))
        self.signalUpdateLabelCurrentRun.emit(str(runId))


        ## Update label

        self.signalSendStatusBarMessage.emit('Ready', 'green')

        # If a double click is detected, we launch a plot of the first parameter
        if doubleClicked:
            self.parameterCellClicked(0, 2)



    @QtCore.pyqtSlot(int, dict, str, str, str, str, str, str, int, bool)
    def addCheckbox(self, runId: int,
                          paramDependent: dict,
                          experimentName: str,
                          curveId: str,
                          plotRef: str,
                          plotTitle: str,
                          windowTitle: str,
                          databaseAbsPath: str,
                          rowPosition: int,
                          isParameterPlotted: bool) -> None:
        """
        Called from main.
        """

        runIdStr = str(runId)

        cb = QtWidgets.QCheckBox()

        if isParameterPlotted:
            cb.setChecked(True)

        self.setItem(rowPosition, 0, QtWidgets.QTableWidgetItem(runIdStr))
        self.setItem(rowPosition, 1, QtWidgets.QTableWidgetItem(experimentName))
        self.setCellWidget(rowPosition, 2, cb)
        self.setItem(rowPosition, 3, QtWidgets.QTableWidgetItem(paramDependent['label']))
        self.setItem(rowPosition, 4, QtWidgets.QTableWidgetItem(paramDependent['unit']))


        independentString = config['sweptParameterSeparator'].join(paramDependent['depends_on'])
        self.setCellWidget(rowPosition, 5, QtWidgets.QLabel(independentString))

        # Each checkbox at its own event attached to it
        cb.toggled.connect(lambda state,
                                  dependentParamName    = paramDependent['name'],
                                  runId                 = runId,
                                  curveId               = curveId,
                                  plotTitle             = plotTitle,
                                  windowTitle           = windowTitle,
                                  dependent             = paramDependent,
                                  plotRef               = plotRef,
                                  databaseAbsPath       = databaseAbsPath: self.parameterClicked(state,
                                                                                                 dependentParamName,
                                                                                                 runId,
                                                                                                 curveId,
                                                                                                 plotTitle,
                                                                                                 windowTitle,
                                                                                                 dependent,
                                                                                                 plotRef,
                                                                                                 databaseAbsPath))


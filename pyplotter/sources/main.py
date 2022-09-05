# This Python file uses the following encoding: utf-8
import os
import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets
from typing import Tuple


from .config import loadConfigCurrent
config = loadConfigCurrent()
from .widgetPlot1d import WidgetPlot1d
from .widgetPlot2d import WidgetPlot2d
from ..ui import mainWindow
from ..ui.hBoxLayoutLabelPath import HBoxLayoutLabelPath
from ..sources.widgetCSV import WidgetCSV
from ..sources.widgetBlueFors import WidgetBlueFors


# Get the folder path for pictures
PICTURESPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../ui/pictures/')


class MainApp(QtWidgets.QMainWindow, mainWindow.Ui_MainWindow):

    signalSendStatusBarMessage = QtCore.pyqtSignal(str, str)
    signalRemoveProgressBar    = QtCore.pyqtSignal(QtWidgets.QProgressBar)
    signalEnableCheck          = QtCore.pyqtSignal(QtWidgets.QCheckBox)
    signalAddRow               = QtCore.pyqtSignal(int, dict, str, str, str, str, str, str, str, int, bool)

    signalRunClickDone = QtCore.pyqtSignal()


    def __init__(self, QApplication,
                       parent=None):

        super(MainApp, self).__init__(parent)
        self.setupUi(self)

        self.qapp = QApplication
        self.widgetCSV = WidgetCSV(None)
        self.widgetBlueFors = WidgetBlueFors(None)


        # Can't promote layout on qtdesigner...
        self.hBoxLayoutPath = HBoxLayoutLabelPath()
        self.verticalLayout_12.addLayout(self.hBoxLayoutPath)


        self.signalRemoveProgressBar.connect(self.statusBarMain.removeProgressBar)
        self.signalEnableCheck.connect(self.tableWidgetParameter.enableCheck)
        self.signalSendStatusBarMessage.connect(self.statusBarMain.setStatusBarMessage)
        self.signalAddRow.connect(self.tableWidgetParameter.slotAddRow)
        self.signalRunClickDone.connect(self.tableWidgetDataBase.slotRunClickDone)




        self.lineEditFilterSnapshot.signallineEditFilterSnapshotTextEdited.connect(self.treeViewSnapshot.searchItem)


        # Connect menuBar signal
        self.menuBarMain.signalUpdateStyle.connect(self.updateStyle)
        self.menuBarMain.signal2MainWindowAddPlot.connect(self.slotFromPlotAddPlot)
        self.menuBarMain.signalUpdateCurve.connect(self.slotUpdateCurve)
        self.menuBarMain.signalUpdate2d.connect(self.slotUpdate2d)
        self.menuBarMain.signalSendStatusBarMessage.connect(self.statusBarMain.setStatusBarMessage)
        self.menuBarMain.signalUpdatePlotProperty.connect(self.slotUpdatePlotProperty)



        self.hBoxLayoutPath.signalButtonClick.connect(self.tableWidgetFolder.folderOpened)

        self.treeViewSnapshot.signalLineEditSnapshotClean.connect(self.lineEditFilterSnapshot.clean)
        self.checkBoxHidden.signalcheckBoxHiddenClick.connect(self.tableWidgetDataBase.slotFromCheckBoxHiddenCheckBoxHiddenClick)

        self.pushButtonOpenFolder.signalFolderOpened.connect(self.tableWidgetFolder.folderOpened)

        self.widgetCSV.signalClearTableWidgetDatabase.connect(self.tableWidgetDataBase.slotClearTable)
        self.widgetCSV.signalClearTableWidgetParameter.connect(self.tableWidgetParameter.slotClearTable)
        self.widgetCSV.signalClearSnapshot.connect(self.treeViewSnapshot.cleanSnapshot)
        self.widgetCSV.signalUpdateLabelCurrentSnapshot.connect(self.labelCurrentSnapshot.setText)
        self.widgetCSV.signalUpdateLabelCurrentRun.connect(self.labelCurrentRun.setText)
        self.widgetCSV.signalLineEditSnapshotEnabled.connect(self.lineEditFilterSnapshot.enabled)
        self.widgetCSV.signalAddSnapshot.connect(self.treeViewSnapshot.addSnapshot)
        self.widgetCSV.signalLabelSnapshotEnabled.connect(self.labelSnapshot.enabled)
        self.widgetCSV.signalSendStatusBarMessage.connect(self.statusBarMain.setStatusBarMessage)
        self.widgetCSV.signalFillTableWidgetParameter.connect(self.tableWidgetParameter.slotFillTableWidgetParameter)
        self.widgetCSV.signalUpdateProgressBar.connect(self.statusBarMain.updateProgressBar)
        self.widgetCSV.signalRemoveProgressBar.connect(self.statusBarMain.removeProgressBar)
        self.widgetCSV.signalLoadedDataFull.connect(self.loadedDataFull)

        self.widgetBlueFors.signalClearTableWidgetDatabase.connect(self.tableWidgetDataBase.slotClearTable)
        self.widgetBlueFors.signalClearTableWidgetParameter.connect(self.tableWidgetParameter.slotClearTable)
        self.widgetBlueFors.signalClearSnapshot.connect(self.treeViewSnapshot.cleanSnapshot)
        self.widgetBlueFors.signalUpdateLabelCurrentSnapshot.connect(self.labelCurrentSnapshot.setText)
        self.widgetBlueFors.signalUpdateLabelCurrentRun.connect(self.labelCurrentRun.setText)
        self.widgetBlueFors.signalLineEditSnapshotEnabled.connect(self.lineEditFilterSnapshot.enabled)
        self.widgetBlueFors.signalLabelSnapshotEnabled.connect(self.labelSnapshot.enabled)
        self.widgetBlueFors.signalSendStatusBarMessage.connect(self.statusBarMain.setStatusBarMessage)
        self.widgetBlueFors.signalFillTableWidgetParameter.connect(self.tableWidgetParameter.slotFillTableWidgetParameter)
        self.widgetBlueFors.signalUpdateProgressBar.connect(self.statusBarMain.updateProgressBar)
        self.widgetBlueFors.signalRemoveProgressBar.connect(self.statusBarMain.removeProgressBar)
        self.widgetBlueFors.signalLoadedDataFull.connect(self.loadedDataFull)

        self.statusBarMain.signalCsvLoad.connect(self.widgetCSV.csvLoad)
        self.statusBarMain.signalBlueForsLoad.connect(self.widgetBlueFors.blueForsLoad)
        self.statusBarMain.signalDatabaseLoad.connect(self.tableWidgetDataBase.databaseClick)
        self.statusBarMain.signalAddCurve.connect(self.tableWidgetParameter.getData)

        self.tableWidgetFolder.signalSendStatusBarMessage.connect(self.statusBarMain.setStatusBarMessage)
        self.tableWidgetFolder.signalBlueForsClick.connect(self.statusBarMain.blueForsLoad)
        self.tableWidgetFolder.signalCSVClick.connect(self.statusBarMain.csvLoad)
        self.tableWidgetFolder.signalDatabaseClick.connect(self.statusBarMain.databaseLoad)
        self.tableWidgetFolder.signalDatabaseClick.connect(self.checkBoxHidden.databaseClick)
        self.tableWidgetFolder.signalUpdateLabelPath.connect(self.hBoxLayoutPath.updateLabelPath)
        self.tableWidgetFolder.signalDatabasePathUpdate.connect(self.tableWidgetDataBase.updateDatabasePath)
        self.tableWidgetFolder.first_call()

        self.tableWidgetDataBase.signalRemoveProgressBar.connect(self.statusBarMain.removeProgressBar)
        self.tableWidgetDataBase.signalSendStatusBarMessage.connect(self.statusBarMain.setStatusBarMessage)
        self.tableWidgetDataBase.signalAddStatusBarMessage.connect(self.statusBarMain.addStatusBarMessage)
        self.tableWidgetDataBase.signalUpdateProgressBar.connect(self.statusBarMain.updateProgressBar)
        self.tableWidgetDataBase.signalDatabaseClickDone.connect(self.tableWidgetFolder.databaseClickDone)
        self.tableWidgetDataBase.signalDatabaseClickDone.connect(self.checkBoxHidden.databaseClickDone)
        self.tableWidgetDataBase.signalUpdateCurrentDatabase.connect(self.labelCurrentDataBase.setText)
        self.tableWidgetDataBase.signalRunClick.connect(self.tableWidgetParameter.slotFillTableWidgetParameter)
        self.tableWidgetDataBase.signalDatabaseStars.connect(self.tableWidgetFolder.slotFromTableWidgetDataBaseDatabaseStars)
        self.tableWidgetDataBase.signalDatabaseUnstars.connect(self.tableWidgetFolder.slotFromTableWidgetDataBaseDatabaseUnstars)
        self.tableWidgetDataBase.signalCheckBoxHiddenHideRow.connect(self.checkBoxHidden.hideRow)
        self.tableWidgetDataBase.signal2StatusBarDatabaseUpdate.connect(self.statusBarMain.databaseLoad)
        self.tableWidgetDataBase.first_call()

        self.tableWidgetParameter.signalSendStatusBarMessage.connect(self.statusBarMain.setStatusBarMessage)
        self.tableWidgetParameter.signalRemoveProgressBar.connect(self.statusBarMain.removeProgressBar)
        self.tableWidgetParameter.signalUpdateProgressBar.connect(self.statusBarMain.updateProgressBar)
        self.tableWidgetParameter.signalAddCurve.connect(self.statusBarMain.addCurve)
        self.tableWidgetParameter.signalCleanSnapshot.connect(self.treeViewSnapshot.cleanSnapshot)
        self.tableWidgetParameter.signalAddSnapshot.connect(self.treeViewSnapshot.addSnapshot)
        self.tableWidgetParameter.signalLineEditSnapshotEnabled.connect(self.lineEditFilterSnapshot.enabled)
        self.tableWidgetParameter.signalLabelSnapshotEnabled.connect(self.labelSnapshot.enabled)
        self.tableWidgetParameter.signalUpdateLabelCurrentSnapshot.connect(self.labelCurrentSnapshot.setText)
        self.tableWidgetParameter.signalUpdateLabelCurrentRun.connect(self.labelCurrentRun.setText)
        self.tableWidgetParameter.signalLoadedDataFull.connect(self.loadedDataFull)
        self.tableWidgetParameter.signalLoadedDataEmpty.connect(self.loadedDataEmpty)
        self.tableWidgetParameter.signalCSVLoadData.connect(self.widgetCSV.loadData)
        self.tableWidgetParameter.signalBlueForsLoadData.connect(self.widgetBlueFors.loadData)
        self.tableWidgetParameter.signaladdRow.connect(self.addRow)
        self.tableWidgetParameter.first_call()

        # References of all opened plot window.
        # Structure:
        # {plotRef : WidgetPlot}
        self._plotRefs = {}

        self.threadpool = QtCore.QThreadPool()

        self.signalSendStatusBarMessage.emit('Ready', 'green')



    ###########################################################################
    #
    #
    #                           GUI
    #
    #
    ###########################################################################



    @QtCore.pyqtSlot(int, dict, str, str, str, str, str, str, str, int)
    def addRow(self, runId: int,
                     paramDependent: dict,
                     experimentName: str,
                     curveId: str,
                     plotRef: str,
                     plotTitle: str,
                     windowTitle: str,
                     databaseAbsPath: str,
                     dataType: str,
                     rowPosition: int) -> None:
        """
        Return True when the displayed parameter is currently plotted.
        """

        parameterPlotted = False
        if len(self._plotRefs) > 0:

            # We iterate over all plotWindow
            for plot in self._plotRefs.values():

                if plot.plotType=='1d':
                    if plotRef in plot.plotRef:
                        if paramDependent['label'] in [curve.curveYLabel for curve in plot.curves.values()]:
                            parameterPlotted = True
                if plot.plotType=='2d':
                    if plotRef in plot.plotRef:
                        if plot.zLabelText==paramDependent['label']:
                            parameterPlotted = True

        self.signalAddRow.emit(runId,
                               paramDependent,
                               experimentName,
                               curveId,
                               plotRef,
                               plotTitle,
                               windowTitle,
                               databaseAbsPath,
                               dataType,
                               rowPosition,
                               parameterPlotted)



    @QtCore.pyqtSlot(dict)
    def updateStyle(self, newConfig: dict) -> None:
        """
        Update the style of the full app.

        Args:
            newConfig: New configuration dict containing the style to be applied.
        """

        if newConfig['style']=='qdarkstyle':
            import qdarkstyle
            self.qapp.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        elif newConfig['style']=='qbstyles':
            import qdarkstyle
            self.qapp.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        elif newConfig['style']=='white':
            self.qapp.setStyleSheet(self.qapp.setStyle('Oxygen'))

        if len(self._plotRefs) > 0:

            for plot in self._plotRefs.values():
                plot.config = newConfig
                plot.updateStyle()



    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Method called when closing the main app.
        Close every 1d and 2d plot opened.
        """

        if hasattr(self.menuBarMain, 'DialogLiveplot'):
            self.menuBarMain.DialogLiveplot.close()

        plotRefs = [plot for plot in self._plotRefs.keys()]
        # plot1d window open from a plo1d window are taken care by the plot1d itself
        # we so remove them from the selection
        # plotRefs = [plotRef for plotRef in plotRefs if 'fft' not in plotRef]
        # plotRefs = [plotRef for plotRef in plotRefs if 'fftnodc' not in plotRef]
        # plotRefs = [plotRef for plotRef in plotRefs if 'ifft' not in plotRef]
        # plotRefs = [plotRef for plotRef in plotRefs if 'unwrap' not in plotRef]
        # plotRefs = [plotRef for plotRef in plotRefs if 'unslop' not in plotRef]
        # plotRefs = [plotRef for plotRef in plotRefs if 'derivative' not in plotRef]
        # plotRefs = [plotRef for plotRef in plotRefs if 'primitive' not in plotRef]
        # plotRefs = [plotRef for plotRef in plotRefs if 'histogram' not in plotRef]

        # Close everything
        for plotRef in plotRefs:
            try:
                self._plotRefs[plotRef]._allowClosing = True
                self._plotRefs[plotRef].deleteLater()
                # Delete its associated reference
                del(self._plotRefs[plotRef])
            except:
                pass



    ###########################################################################
    #
    #
    #                           Plotting
    #
    #
    ###########################################################################



    @QtCore.pyqtSlot(QtWidgets.QCheckBox, QtWidgets.QProgressBar)
    def loadedDataEmpty(self, cb: QtWidgets.QCheckBox,
                              progressBar    : QtWidgets.QProgressBar) -> None:
        """
        Method called by LoadDataFromRunThread when the data download is done but the
        database is empty.
        We signal the data downloading being done by setting the flag False.
        This will allow the next live plot iteration to try downloading the data
        again.
        """

        # Since the data download failed, we uncheck the checkbox
        cb.setChecked(False)

        self.signalEnableCheck.emit(cb)
        self.signalRemoveProgressBar.emit(progressBar)
        self.signalRunClickDone.emit()



    @QtCore.pyqtSlot(int, str, str, str, str, str, QtWidgets.QCheckBox, QtWidgets.QProgressBar, tuple, str, str, str, str, str, str, bool)
    def loadedDataFull(self, runId          : int,
                             curveId        : str,
                             plotTitle      : str,
                             windowTitle    : str,
                             plotRef        : str,
                             databaseAbsPath: str,
                             cb             : QtWidgets.QCheckBox,
                             progressBar    : QtWidgets.QProgressBar,
                             data           : Tuple[np.ndarray],
                             xLabelText     : str,
                             xLabelUnits    : str,
                             yLabelText     : str,
                             yLabelUnits    : str,
                             zLabelText     : str,
                             zLabelUnits    : str,
                             dateTimeAxis   : bool) -> None:
        """
        Call from loaddata thread.
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
                     dateTimeAxis   = dateTimeAxis,
                     curveLegend    = yLabelText)

        self.signalRemoveProgressBar.emit(progressBar)
        self.signalEnableCheck.emit(cb)

        self.signalRunClickDone.emit()



    @QtCore.pyqtSlot(int, str, str, str, str, str, tuple, str, str, str, str, str, str)
    def slotFromPlotAddPlot(self, runId          : int,
                                  curveId        : str,
                                  plotTitle      : str,
                                  windowTitle    : str,
                                  plotRef        : str,
                                  databaseAbsPath: str,
                                  data           : Tuple[np.ndarray, ...],
                                  xLabelText     : str,
                                  xLabelUnits    : str,
                                  yLabelText     : str,
                                  yLabelUnits    : str,
                                  zLabelText     : str,
                                  zLabelUnits    : str) -> None:
        """
        Call from plot.
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
                     dateTimeAxis   = False,
                     curveLegend    = yLabelText)



    def addPlot(self, plotRef            : str,
                      databaseAbsPath    : str,
                      data               : Tuple[np.ndarray, ...],
                      xLabelText         : str,
                      xLabelUnits        : str,
                      yLabelText         : str,
                      yLabelUnits        : str,
                      zLabelText         : str,
                      zLabelUnits        : str,
                      runId              : int,
                      curveId            : str,
                      plotTitle          : str,
                      windowTitle        : str,
                      dateTimeAxis       : bool,
                      curveLegend        : str) -> None:
        """
        Methods called once the data are downloaded to add a plot of the data.
        Discriminate between 1d and 2d plot through the length of data list.
        For 1d plot, data having the sample plotRef do not launch a new plot
        window but instead are plotted in the window sharing the same plotRef.
        Once the data are plotted, run updateList1dCurvesLabels.

        Parameters
        ----------
        plotRef : str
            Reference of the plot.
        progressBar : str
            Key to the progress bar in the dict progressBars.
        data : list
            For 1d plot: [xData, yData]
            For 2d plot: [xData, yData, zData]
        xLabelText : str
            Label text for the xAxix.
        xLabelUnits : str
            Label units for the xAxix.
        yLabelText : str
            Label text for the yAxix.
        yLabelUnits : str
            Label units for the yAxix.
        runId : int
            Data run id in the current database
        curveId : str
            Id of the curve, see getCurveId.
        plotTitle : str
            Plot title, see getPlotTitle.
        windowTitle : str
            Window title, see getWindowTitle.
        zLabelText : str, default None
            Only for 2d data.
            Label text for the zAxis.
        zLabelUnits : str, default None
            Only for 2d data.
            Label units for the zAxis.
        """

        # If data is None it means the data download encounter an error.
        # We do not add plot
        if data is None:
            return

        self.signalSendStatusBarMessage.emit('Launching '+str(len(data)-1)+'d plot', 'orange')


        # If some parameters are not given, we find then from the GUI
        # if cleanCheckBox is None:
        #     cleanCheckBox = self.cleanCheckBox


        # 1D plot
        if len(data)==2:

            # If the plotRef is not stored we launched a new window
            # Otherwise we add a new PlotDataItem on an existing WidgetPlot1d
            if plotRef not in self._plotRefs:


                p = WidgetPlot1d(x                  = data[0],
                              y                  = data[1],
                              title              = plotTitle,
                              xLabelText         = xLabelText,
                              xLabelUnits        = xLabelUnits,
                              yLabelText         = yLabelText,
                              yLabelUnits        = yLabelUnits,
                              windowTitle        = windowTitle,
                              runId              = runId,
                              plotRef            = plotRef,
                              databaseAbsPath    = databaseAbsPath,
                              curveId            = curveId,
                              curveLegend        = curveLegend,
                              dateTimeAxis       = dateTimeAxis)

                # Through interaction, we open new plot
                p.signal2MainWindowAddPlot.connect(self.slotFromPlotAddPlot)
                # When a plot is closed, all its sub-interaction plot are closed
                p.signalClose1dPlot.connect(self.slotClose1dPlot)
                p.signalUpdateCurve.connect(self.slotUpdateCurve)


                # self.signalAddSliceItem.connect(p.addSliceItem)


                # When use uncheck a parameter in tableWidgetParameter, we
                # propagate the event to plot
                self.tableWidgetParameter.signalRemoveCurve.connect(p.slotRemoveCurve)

                # If the plot comes from 2dplot, we connect signal
                for plot in self._plotRefs.values():
                    if plot.plotType=='2d':
                        plot.signalRemoveCurve.connect(p.slotRemoveCurve)

                self._plotRefs[plotRef] = p

                # self._plotRefs[plotRef].show()
            else:

                self._plotRefs[plotRef].addPlotDataItem(x                  = data[0],
                                                        y                  = data[1],
                                                        curveId            = curveId,
                                                        curveXLabel        = xLabelText,
                                                        curveXUnits        = xLabelUnits,
                                                        curveYLabel        = yLabelText,
                                                        curveYUnits        = yLabelUnits,
                                                        curveLegend        = curveLegend)
            self.updateList1dCurvesLabels()

        # 2D plot
        elif len(data)==3:

            # Determine if we should open a new WidgetPlot2d
            if plotRef not in self._plotRefs:
                p = WidgetPlot2d(x               = data[0],
                              y               = data[1],
                              z               = data[2],
                              title           = plotTitle,
                              xLabelText      = xLabelText,
                              xLabelUnits     = xLabelUnits,
                              yLabelText      = yLabelText,
                              yLabelUnits     = yLabelUnits,
                              zLabelText      = zLabelText,
                              zLabelUnits     = zLabelUnits,
                              windowTitle     = windowTitle,
                              runId           = runId,
                              curveId         = curveId,
                              plotRef         = plotRef,
                              databaseAbsPath = databaseAbsPath)

                # p.signalGet1dColorIndex.connect(self.slotGet1dColorIndex)
                p.signal2MainWindowAddPlot.connect(self.slotFromPlotAddPlot)
                p.signalUpdateCurve.connect(self.slotUpdateCurve)
                p.signalClose1dPlot.connect(self.slotClose1dPlot)
                p.signalClose2dPlot.connect(self.slotClose2dPlot)

                self._plotRefs[plotRef] = p
                self._plotRefs[plotRef].show()

        self.signalSendStatusBarMessage.emit('Ready', 'green')



    QtCore.pyqtSlot(str, str, str)
    def slotUpdatePlotProperty(self, plotRef: str,
                                     prop: str,
                                     value: str) -> None:

        self._plotRefs[plotRef].updatePlotProperty(prop,
                                                   value)



    QtCore.pyqtSlot(str, str, str, np.ndarray, np.ndarray, bool, bool)
    def slotUpdateCurve(self, plotRef: str,
                              curveId: str,
                              curveLegend: str,
                              x: np.ndarray,
                              y: np.ndarray,
                              autoRange: bool,
                              interactionUpdateAll: bool) -> None:

        if len(x)!=len(y):
            self.signalSendStatusBarMessage('Curve update failed: x and y do not have the same length',
                                            'red')
        else:
            self._plotRefs[plotRef].updatePlotDataItem(x,
                                                       y,
                                                       curveId,
                                                       curveLegend,
                                                       autoRange,
                                                       interactionUpdateAll)



    QtCore.pyqtSlot(str, str, str, np.ndarray, np.ndarray)
    def slotUpdate2d(self, plotRef: str,
                             x: np.ndarray,
                             y: np.ndarray,
                             z: np.ndarray) -> None:

        self._plotRefs[plotRef].livePlotUpdate(x=x,
                                               y=y,
                                               z=z)


    def updateList1dCurvesLabels(self) -> None:
        """
        Is called when the user add or delete a plot.
        See addPlot and removePlot
        The method creates a list of all displayed 1d plot window object and
        send it to all displayed 1d plot windows via the updatePlottedCurvesList
        method.
        """

        if len(self._plotRefs) > 0:
            # Build the list of 1d plot windows
            plots = [plot for plot in self._plotRefs.values() if plot.plotType=='1d']

            # Send the list to every 1d plot windows
            # [plot.widgetTabCurve.updateList1dCurvesLabels(plot, plots) for plot in plots]
            for plot in plots:
                plot.widgetTabCurve.updateList1dCurvesLabels(plot.plotRef,
                                                             list(plot.curves.keys()),
                                                             plots)



    @QtCore.pyqtSlot(str)
    def slotClose1dPlot(self, plotRef: str) -> None:

        # We uncheck all curves from the tableWidgetParameter
        curvesId = list(self._plotRefs[plotRef].curves.keys())
        for curveId in curvesId:
            self.tableWidgetParameter.slotUncheck(curveId)


        # We check for all possible interaction plots from that 1d plot
        for curveType in ('fft',
                          'fftnodc',
                          'ifft',
                          'derivative',
                          'primitive',
                          'unwrap',
                          'unslop',
                          'histogram'):

            # If sub-interaction plot, we uncheck all curves from the plot
            if curveType in plotRef:
                if plotRef[:-len(curveType)] in self._plotRefs.keys():
                    self._plotRefs[plotRef[:-len(curveType)]].interactionCurveClose(curveType)

            # If mother plot, we close all sub-interaction plot
            if plotRef+curveType in self._plotRefs.keys():
                self._plotRefs[plotRef+curveType].deleteLater()
                del(self._plotRefs[plotRef+curveType])


        # We check if that 1d plot was an interaction from a 2d plot
        for curveType in ('vertical',
                          'horizontal',
                          'anyvertical',
                          'anyhorizontal',
                          ):

            # We get the curveId of the closed curved and remove their attached
            # sliceItem
            if curveType in plotRef:
                for curveId in self._plotRefs[plotRef].curves.keys():
                    self._plotRefs[plotRef[:-len(curveType)]].removeSliceItem(curveId)

        # We check for any interaction that should be uncheck
        for curveType in ('minimum',
                          'maximum',
                          ):
            if curveType in plotRef:
                for curveId in self._plotRefs[plotRef].curves.keys():
                    self._plotRefs[plotRef[:-len(curveType)]].interactionCurveClose(curveType)


        # We close the plot
        self._plotRefs[plotRef]._allowClosing = True
        self._plotRefs[plotRef].deleteLater()
        del(self._plotRefs[plotRef])

        self.updateList1dCurvesLabels()



    @QtCore.pyqtSlot(str, str)
    def slotClose2dPlot(self, plotRef: str,
                              curveId: str) -> None:

        # We uncheck the tableWidgetParameter
        self.tableWidgetParameter.slotUncheck(curveId)

        for curveType in ('vertical',
                          'horizontal',
                          'anyvertical',
                          'anyhorizontal',
                          'minimum',
                          'maximum',
                          ):

            if plotRef+curveType in self._plotRefs.keys():
                self._plotRefs[plotRef+curveType].deleteLater()
                del(self._plotRefs[plotRef+curveType])

        # special case for the 3d
        if hasattr(self._plotRefs[plotRef], 'widget3d'):
            self._plotRefs[plotRef].widget3d.close()

        # We close the plot
        self._plotRefs[plotRef]._allowClosing = True
        self._plotRefs[plotRef].deleteLater()
        del(self._plotRefs[plotRef])

        self.updateList1dCurvesLabels()

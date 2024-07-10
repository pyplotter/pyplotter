import os
import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets
from typing import Optional, Tuple

# from .mainWindowui import Ui_MainWindow
from .mainWindowui_r2c2 import Ui_MainWindow
from .plot.plot1d.widgetPlot1d import WidgetPlot1d
from .plot.plot2d.widgetPlot2d import WidgetPlot2d
from .hBoxLayoutLabelPath import HBoxLayoutLabelPath
from .widgetCSV import WidgetCSV
from .widgetNpz import WidgetNpz
from .widgetBlueFors import WidgetBlueFors

from ..sources.config import loadConfigCurrent
config = loadConfigCurrent()

# Get the folder path for pictures
PICTURESPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../ui/pictures/')


class MainApp(QtWidgets.QMainWindow):

    signalSendStatusBarMessage = QtCore.pyqtSignal(str, str)
    signalRemoveProgressBar    = QtCore.pyqtSignal(int)
    signalEnableCheck          = QtCore.pyqtSignal(QtWidgets.QCheckBox)
    signalAddRow               = QtCore.pyqtSignal(int, dict, str, str, str, str, str, str, str, str, int, bool)

    signalRunClickDone = QtCore.pyqtSignal()


    def __init__(self, QApplication,
                       parent=None):

        super(MainApp, self).__init__(parent)

        # Build the UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.qapp = QApplication
        self.widgetCSV = WidgetCSV(None)
        self.widgetNpz = WidgetNpz(None)
        self.widgetBlueFors = WidgetBlueFors(None)


        # Can't promote layout on qtdesigner...
        self.hBoxLayoutPath = HBoxLayoutLabelPath()
        self.ui.verticalLayout_12.addLayout(self.hBoxLayoutPath)


        self.signalRemoveProgressBar.connect(self.ui.statusBarMain.removeProgressBar)
        self.signalEnableCheck.connect(self.ui.tableWidgetParameter.enableCheck)
        self.signalSendStatusBarMessage.connect(self.ui.statusBarMain.setStatusBarMessage)
        self.signalAddRow.connect(self.ui.tableWidgetParameter.slotAddRow)
        self.signalRunClickDone.connect(self.ui.tableWidgetDataBase.slotRunClickDone)




        self.ui.lineEditFilterSnapshot.signallineEditFilterSnapshotTextEdited.connect(self.ui.treeViewSnapshot.searchItem)


        # Connect menuBar signal
        self.ui.menuBarMain.signalUpdateStyle.connect(self.updateStyle)
        self.ui.menuBarMain.signalUpdateTableWidgetDatabase.connect(self.ui.tableWidgetDataBase.slotUpdate)
        self.ui.menuBarMain.signalAddLivePlot.connect(self.slotFromLivePlotAddPlot)
        self.ui.menuBarMain.signalCloseLivePlot.connect(self.slotFromLivePlotClosePlot)
        self.ui.menuBarMain.signalUpdate1d.connect(self.slotUpdateCurve)
        self.ui.menuBarMain.signalUpdate2d.connect(self.slotUpdate2d)
        self.ui.menuBarMain.signalUpdatePlotProperty.connect(self.slotUpdatePlotProperty)
        self.ui.menuBarMain.signalCloseAllPlot.connect(self.slotCloseAllPlots)



        self.hBoxLayoutPath.signalButtonClick.connect(self.ui.tableWidgetFolder.folderOpened)

        self.ui.treeViewSnapshot.signalLineEditSnapshotClean.connect(self.ui.lineEditFilterSnapshot.clean)
        self.ui.checkBoxHidden.signalcheckBoxHiddenClick.connect(self.ui.tableWidgetDataBase.slotFromCheckBoxHiddenCheckBoxHiddenClick)
        self.ui.checkBoxStared.signalCheckBoxStaredClick.connect(self.ui.tableWidgetDataBase.slotFromCheckBoxStaredCheckBoxStaredClick)

        self.ui.pushButtonOpenFolder.signalFolderOpened.connect(self.ui.tableWidgetFolder.folderOpened)

        self.widgetCSV.signalClearTableWidgetDatabase.connect(self.ui.tableWidgetDataBase.slotClearTable)
        self.widgetCSV.signalClearTableWidgetParameter.connect(self.ui.tableWidgetParameter.slotClearTable)
        self.widgetCSV.signalClearSnapshot.connect(self.ui.treeViewSnapshot.cleanSnapshot)
        self.widgetCSV.signalUpdateLabelCurrentSnapshot.connect(self.ui.labelCurrentSnapshot.setText)
        self.widgetCSV.signalUpdateLabelCurrentRun.connect(self.ui.labelCurrentRun.setText)
        self.widgetCSV.signalLineEditSnapshotEnabled.connect(self.ui.lineEditFilterSnapshot.enabled)
        self.widgetCSV.signalAddSnapshot.connect(self.ui.treeViewSnapshot.addSnapshot)
        self.widgetCSV.signalLabelSnapshotEnabled.connect(self.ui.labelSnapshot.enabled)
        self.widgetCSV.signalSendStatusBarMessage.connect(self.ui.statusBarMain.setStatusBarMessage)
        self.widgetCSV.signalFillTableWidgetParameter.connect(self.ui.tableWidgetParameter.slotFillTableWidgetParameter)
        self.widgetCSV.signalUpdateProgressBar.connect(self.ui.statusBarMain.updateProgressBar)
        self.widgetCSV.signalRemoveProgressBar.connect(self.ui.statusBarMain.removeProgressBar)
        self.widgetCSV.signalLoadedDataFull.connect(self.loadedDataFull)

        self.widgetNpz.signalClearTableWidgetDatabase.connect(self.ui.tableWidgetDataBase.slotClearTable)
        self.widgetNpz.signalClearTableWidgetParameter.connect(self.ui.tableWidgetParameter.slotClearTable)
        self.widgetNpz.signalClearSnapshot.connect(self.ui.treeViewSnapshot.cleanSnapshot)
        self.widgetNpz.signalUpdateLabelCurrentSnapshot.connect(self.ui.labelCurrentSnapshot.setText)
        self.widgetNpz.signalUpdateLabelCurrentRun.connect(self.ui.labelCurrentRun.setText)
        self.widgetNpz.signalLineEditSnapshotEnabled.connect(self.ui.lineEditFilterSnapshot.enabled)
        self.widgetNpz.signalLabelSnapshotEnabled.connect(self.ui.labelSnapshot.enabled)
        self.widgetNpz.signalSendStatusBarMessage.connect(self.ui.statusBarMain.setStatusBarMessage)
        self.widgetNpz.signalFillTableWidgetParameter.connect(self.ui.tableWidgetParameter.slotFillTableWidgetParameter)
        self.widgetNpz.signalUpdateProgressBar.connect(self.ui.statusBarMain.updateProgressBar)
        self.widgetNpz.signalRemoveProgressBar.connect(self.ui.statusBarMain.removeProgressBar)
        self.widgetNpz.signalLoadedDataFull.connect(self.loadedDataFull)
        self.widgetNpz.signalNpzIncorrectSize.connect(self.ui.tableWidgetParameter.slotNpzIncorrectSize)

        self.widgetBlueFors.signalClearTableWidgetDatabase.connect(self.ui.tableWidgetDataBase.slotClearTable)
        self.widgetBlueFors.signalClearTableWidgetParameter.connect(self.ui.tableWidgetParameter.slotClearTable)
        self.widgetBlueFors.signalClearSnapshot.connect(self.ui.treeViewSnapshot.cleanSnapshot)
        self.widgetBlueFors.signalUpdateLabelCurrentSnapshot.connect(self.ui.labelCurrentSnapshot.setText)
        self.widgetBlueFors.signalUpdateLabelCurrentRun.connect(self.ui.labelCurrentRun.setText)
        self.widgetBlueFors.signalLineEditSnapshotEnabled.connect(self.ui.lineEditFilterSnapshot.enabled)
        self.widgetBlueFors.signalLabelSnapshotEnabled.connect(self.ui.labelSnapshot.enabled)
        self.widgetBlueFors.signalSendStatusBarMessage.connect(self.ui.statusBarMain.setStatusBarMessage)
        self.widgetBlueFors.signalFillTableWidgetParameter.connect(self.ui.tableWidgetParameter.slotFillTableWidgetParameter)
        self.widgetBlueFors.signalUpdateProgressBar.connect(self.ui.statusBarMain.updateProgressBar)
        self.widgetBlueFors.signalRemoveProgressBar.connect(self.ui.statusBarMain.removeProgressBar)
        self.widgetBlueFors.signalLoadedDataFull.connect(self.loadedDataFull)

        self.ui.statusBarMain.signalExportRunLoad.connect(self.ui.tableWidgetDataBase.exportRunLoad)
        self.ui.statusBarMain.signalCsvLoad.connect(self.widgetCSV.csvLoad)
        self.ui.statusBarMain.signalNpzLoad.connect(self.widgetNpz.npzLoad)
        self.ui.statusBarMain.signalBlueForsLoad.connect(self.widgetBlueFors.blueForsLoad)
        self.ui.statusBarMain.signalDatabaseLoad.connect(self.ui.tableWidgetDataBase.databaseClick)
        self.ui.statusBarMain.signalAddCurve.connect(self.ui.tableWidgetParameter.getData)

        self.ui.tableWidgetFolder.signalSendStatusBarMessage.connect(self.ui.statusBarMain.setStatusBarMessage)
        self.ui.tableWidgetFolder.signalBlueForsClick.connect(self.ui.statusBarMain.blueForsLoad)
        self.ui.tableWidgetFolder.signalCSVClick.connect(self.ui.statusBarMain.csvLoad)
        self.ui.tableWidgetFolder.signalNpzClick.connect(self.ui.statusBarMain.npzLoad)
        self.ui.tableWidgetFolder.signalDatabaseClick.connect(self.ui.statusBarMain.databaseLoad)
        self.ui.tableWidgetFolder.signalDatabaseClick.connect(self.ui.checkBoxHidden.databaseClick)
        self.ui.tableWidgetFolder.signalDatabaseClick.connect(self.ui.checkBoxStared.databaseClick)
        self.ui.tableWidgetFolder.signalUpdateLabelPath.connect(self.hBoxLayoutPath.updateLabelPath)
        self.ui.tableWidgetFolder.signalDatabasePathUpdate.connect(self.ui.tableWidgetDataBase.updateDatabasePath)
        self.ui.tableWidgetFolder.first_call()


        self.ui.tableWidgetFolder.signalClearTableWidget.connect(self.ui.tableWidgetDataBase.slotClearTable)
        self.ui.tableWidgetFolder.signalAddRows.connect(self.ui.tableWidgetDataBase.databaseClickAddRows)
        self.ui.tableWidgetFolder.signalLabradDataClickDone.connect(self.ui.tableWidgetDataBase.labradDatabaseClickDone)


        self.ui.tableWidgetDataBase.signalRemoveProgressBar.connect(self.ui.statusBarMain.removeProgressBar)
        self.ui.tableWidgetDataBase.signalSendStatusBarMessage.connect(self.ui.statusBarMain.setStatusBarMessage)
        self.ui.tableWidgetDataBase.signalAddStatusBarMessage.connect(self.ui.statusBarMain.addStatusBarMessage)
        self.ui.tableWidgetDataBase.signalUpdateProgressBar.connect(self.ui.statusBarMain.updateProgressBar)
        self.ui.tableWidgetDataBase.signal2StatusBarDatabaseUpdate.connect(self.ui.statusBarMain.databaseLoad)
        self.ui.tableWidgetDataBase.signalExportRunAddProgressBar.connect(self.ui.statusBarMain.exportRunAddProgressBar)

        self.ui.tableWidgetDataBase.signalDatabaseClickDone.connect(self.ui.tableWidgetFolder.databaseClickDone)
        self.ui.tableWidgetDataBase.signalDatabaseStars.connect(self.ui.tableWidgetFolder.slotFromTableWidgetDataBaseDatabaseStars)
        self.ui.tableWidgetDataBase.signalDatabaseUnstars.connect(self.ui.tableWidgetFolder.slotFromTableWidgetDataBaseDatabaseUnstars)

        self.ui.tableWidgetDataBase.signalDatabaseClickDone.connect(self.ui.checkBoxHidden.databaseClickDone)
        self.ui.tableWidgetDataBase.signalCheckBoxHiddenHideRow.connect(self.ui.checkBoxHidden.hideRow)
        self.ui.tableWidgetDataBase.signalCheckBoxStaredChecked.connect(self.ui.checkBoxHidden.checkBoxStaredChecked)

        self.ui.tableWidgetDataBase.signalDatabaseClickDone.connect(self.ui.checkBoxStared.databaseClickDone)
        self.ui.tableWidgetDataBase.signalCheckBoxHiddenChecked.connect(self.ui.checkBoxStared.checkBoxHiddenChecked)

        self.ui.tableWidgetDataBase.signalUpdateCurrentDatabase.connect(self.ui.labelCurrentDataBase.setText)

        self.ui.tableWidgetDataBase.signalRunClick.connect(self.ui.tableWidgetParameter.slotFillTableWidgetParameter)


        self.ui.tableWidgetDataBase.first_call()



        self.ui.tableWidgetParameter.signalSendStatusBarMessage.connect(self.ui.statusBarMain.setStatusBarMessage)
        self.ui.tableWidgetParameter.signalRemoveProgressBar.connect(self.ui.statusBarMain.removeProgressBar)
        self.ui.tableWidgetParameter.signalUpdateProgressBar.connect(self.ui.statusBarMain.updateProgressBar)
        self.ui.tableWidgetParameter.signalAddCurve.connect(self.ui.statusBarMain.addCurve)
        self.ui.tableWidgetParameter.signalAddPlot.connect(self.slotFromLivePlotAddPlot)
        self.ui.tableWidgetParameter.signalUpdate1d.connect(self.slotUpdateCurve)
        self.ui.tableWidgetParameter.signalUpdate2d.connect(self.slotUpdate2d)

        self.ui.tableWidgetParameter.signalCleanSnapshot.connect(self.ui.treeViewSnapshot.cleanSnapshot)
        self.ui.tableWidgetParameter.signalAddSnapshot.connect(self.ui.treeViewSnapshot.addSnapshot)
        self.ui.tableWidgetParameter.signalLineEditSnapshotEnabled.connect(self.ui.lineEditFilterSnapshot.enabled)
        self.ui.tableWidgetParameter.signalLabelSnapshotEnabled.connect(self.ui.labelSnapshot.enabled)
        self.ui.tableWidgetParameter.signalUpdateLabelCurrentSnapshot.connect(self.ui.labelCurrentSnapshot.setText)
        self.ui.tableWidgetParameter.signalUpdateLabelCurrentRun.connect(self.ui.labelCurrentRun.setText)
        self.ui.tableWidgetParameter.signalLoadedDataFull.connect(self.loadedDataFull)
        self.ui.tableWidgetParameter.signalLoadedDataEmpty.connect(self.loadedDataEmpty)
        self.ui.tableWidgetParameter.signalCSVLoadData.connect(self.widgetCSV.loadData)
        self.ui.tableWidgetParameter.signalNpzLoadData.connect(self.widgetNpz.loadData)
        self.ui.tableWidgetParameter.signalBlueForsLoadData.connect(self.widgetBlueFors.loadData)
        self.ui.tableWidgetParameter.signaladdRow.connect(self.addRow)
        self.ui.tableWidgetParameter.first_call()

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



    @QtCore.pyqtSlot(int, dict, str, str, str, str, str, str, str, str, int)
    def addRow(self, runId: int,
                     paramDependent: dict,
                     experimentName: str,
                     shape: str,
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
                               shape,
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
                plot.plotWidget.updateStyle()



    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Method called when closing the main app.
        Close every 1d and 2d plot opened.
        """

        if hasattr(self.ui.menuBarMain, 'DialogLiveplot'):
            self.ui.menuBarMain.DialogLiveplot.close()

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

        if hasattr(self.ui.tableWidgetDataBase, 'dialogComment'):
            self.ui.tableWidgetDataBase.dialogComment._allowClosing = True
            self.ui.tableWidgetDataBase.dialogComment.deleteLater()
            del(self.ui.tableWidgetDataBase.dialogComment)



    ###########################################################################
    #
    #
    #                           Plotting
    #
    #
    ###########################################################################



    @QtCore.pyqtSlot(QtWidgets.QCheckBox, int)
    def loadedDataEmpty(self, cb: QtWidgets.QCheckBox,
                              progressBarId: int) -> None:
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
        self.signalRemoveProgressBar.emit(progressBarId)
        self.signalRunClickDone.emit()



    @QtCore.pyqtSlot(int, str, str, str, str, str, QtWidgets.QCheckBox, int, tuple, str, str, str, str, str, str, bool)
    def loadedDataFull(self, runId          : int,
                             curveId        : str,
                             plotTitle      : str,
                             windowTitle    : str,
                             plotRef        : str,
                             databaseAbsPath: str,
                             cb             : QtWidgets.QCheckBox,
                             progressBarId    : int,
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

        self.signalRemoveProgressBar.emit(progressBarId)
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




    @QtCore.pyqtSlot(int, str, str, str, str, str, tuple, str, str, str, str, str, str, int, int, int, int)
    def slotFromLivePlotAddPlot(self, runId           : int,
                                      curveId         : str,
                                      plotTitle       : str,
                                      windowTitle     : str,
                                      plotRef         : str,
                                      databaseAbsPath : str,
                                      data            : Tuple[np.ndarray, ...],
                                      xLabelText      : str,
                                      xLabelUnits     : str,
                                      yLabelText      : str,
                                      yLabelUnits     : str,
                                      zLabelText      : str,
                                      zLabelUnits     : str,
                                      dialogX         : int,
                                      dialogY         : int,
                                      dialogWidth     : int,
                                      dialogHeight    : int,
                                      ) -> None:
        """
        Call from livePlot dialog to add plot.
        """

        self.addPlot(plotRef         = plotRef,
                     databaseAbsPath = databaseAbsPath,
                     data            = data,
                     xLabelText      = xLabelText,
                     xLabelUnits     = xLabelUnits,
                     yLabelText      = yLabelText,
                     yLabelUnits     = yLabelUnits,
                     zLabelText      = zLabelText,
                     zLabelUnits     = zLabelUnits,
                     runId           = runId,
                     curveId         = curveId,
                     plotTitle       = plotTitle,
                     windowTitle     = windowTitle,
                     dateTimeAxis    = False,
                     curveLegend     = yLabelText,
                     dialogX         = dialogX,
                     dialogY         = dialogY,
                     dialogWidth     = dialogWidth,
                     dialogHeight    = dialogHeight)

    @QtCore.pyqtSlot(tuple, bool, tuple)
    def slotFromLivePlotClosePlot(self, plotRefs        : Tuple[str,...],
                                        is2dPlot        : bool,
                                        curveIds        : Tuple[str,...],
                                        ) -> None:
        if is2dPlot:
            for plotRef, curveId in zip(plotRefs, curveIds):
                self.slotClose2dPlot(plotRef, curveId)
        else:
            self.slotClose1dPlot(plotRefs[0])


    @QtCore.pyqtSlot()
    def slotCloseAllPlots(self):
        print('Close all plots')
        plotRefs = []
        plotTypes = []
        curveIds = []
        for plotRef, p in self._plotRefs.items():
            plotRefs.append(plotRef)
            plotTypes.append(p.plotType)
            if p.plotType == '1d':
                curveIds.extend(p.curves.keys())
            elif p.plotType == '2d':
                curveIds.append(p.curveId)
            else:
                curveIds.append(None)
        
        for plotRef, plotType, curveId in zip(plotRefs, plotTypes, curveIds):
            if plotType == '1d' and curveId is not None:
                self.slotClose1dPlot(plotRef)
            elif plotType == '2d':
                self.slotClose2dPlot(plotRef, curveId=curveId)

    def addPlot(self, plotRef         : str,
                      databaseAbsPath : str,
                      data            : Tuple[np.ndarray, ...],
                      xLabelText      : str,
                      xLabelUnits     : str,
                      yLabelText      : str,
                      yLabelUnits     : str,
                      zLabelText      : str,
                      zLabelUnits     : str,
                      runId           : int,
                      curveId         : str,
                      plotTitle       : str,
                      windowTitle     : str,
                      dateTimeAxis    : bool,
                      curveLegend     : str,
                      dialogX         : Optional[int]=None,
                      dialogY         : Optional[int]=None,
                      dialogWidth     : Optional[int]=None,
                      dialogHeight    : Optional[int]=None) -> None:
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


                p = WidgetPlot1d(x               = data[0],
                                 y               = data[1],
                                 title           = plotTitle,
                                 xLabelText      = xLabelText,
                                 xLabelUnits     = xLabelUnits,
                                 yLabelText      = yLabelText,
                                 yLabelUnits     = yLabelUnits,
                                 windowTitle     = windowTitle,
                                 runId           = runId,
                                 plotRef         = plotRef,
                                 databaseAbsPath = databaseAbsPath,
                                 curveId         = curveId,
                                 curveLegend     = curveLegend,
                                 dateTimeAxis    = dateTimeAxis,
                                 dialogX         = dialogX,
                                 dialogY         = dialogY,
                                 dialogWidth     = dialogWidth,
                                 dialogHeight    = dialogHeight)

                # Through interaction, we open new plot
                p.signal2MainWindowAddPlot.connect(self.slotFromPlotAddPlot)
                # When a plot is closed, all its sub-interaction plot are closed
                p.signalClose1dPlot.connect(self.slotClose1dPlot)
                p.signalUpdateCurve.connect(self.slotUpdateCurve)


                # self.signalAddSliceItem.connect(p.addSliceItem)


                # When use uncheck a parameter in tableWidgetParameter, we
                # propagate the event to plot
                self.ui.tableWidgetParameter.signalRemoveCurve.connect(p.slotRemoveCurve)

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
                                 databaseAbsPath = databaseAbsPath,
                                 dialogX         = dialogX,
                                 dialogY         = dialogY,
                                 dialogWidth     = dialogWidth,
                                 dialogHeight    = dialogHeight)

                # p.signalGet1dColorIndex.connect(self.slotGet1dColorIndex)
                p.signal2MainWindowAddPlot.connect(self.slotFromPlotAddPlot)
                p.signalUpdateCurve.connect(self.slotUpdateCurve)
                p.signalUpdate2dFitResult.connect(self.slotUpdate2d)
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
        self.signalRunClickDone.emit()


    QtCore.pyqtSlot(str, str, str, np.ndarray, np.ndarray)
    def slotUpdate2d(self, plotRef: str,
                           x: np.ndarray,
                           y: np.ndarray,
                           z: np.ndarray) -> None:
        self._plotRefs[plotRef].updatePlotData(x=x,
                                               y=y,
                                               z=z)
        self.signalRunClickDone.emit()


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
            for plot in plots:
                plot.ui.widgetTabCurve.updateList1dCurvesLabels(plot.plotRef,
                                                                list(plot.curves.keys()),
                                                                plots)



    @QtCore.pyqtSlot(str)
    def slotClose1dPlot(self, plotRef: str) -> None:

        # We uncheck all curves from the tableWidgetParameter
        curvesId = list(self._plotRefs[plotRef].curves.keys())
        for curveId in curvesId:
            print(f'close 1D plots {plotRef}-{curveId}')
            self.ui.tableWidgetParameter.slotUncheck(curveId)


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
                          'anyVertical',
                          'anyHorizontal',
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
        self.ui.tableWidgetParameter.slotUncheck(curveId)

        for curveType in ('vertical',
                          'horizontal',
                          'anyVertical',
                          'anyHorizontal',
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

# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtWidgets
import numpy as np
from typing import Tuple

from .groupBoxStatisticsUi import Ui_groupBoxStatistics
from ...sources.functions import parse_number
from ...sources.pyqtgraph import pg

class GroupBoxStatistics(QtWidgets.QGroupBox, Ui_groupBoxStatistics):


    signalUpdateCurve = QtCore.pyqtSignal(str, str, str, np.ndarray, np.ndarray, bool)
    signal2MainWindowAddPlot   = QtCore.pyqtSignal(int, str, str, str, str, str, tuple, str, str, str, str, str, str)
    signalClose1dPlot  = QtCore.pyqtSignal(str)


    def __init__(self, parent: QtWidgets.QGroupBox,
                       config: dict,
                       databaseAbsPath: str,
                       plotItem: pg.PlotItem,
                       plotRef:str,
                       windowTitle: str) -> None:

        QtWidgets.QGroupBox.__init__(self, parent)
        self.setupUi(self)

        self.config = config
        self.databaseAbsPath = databaseAbsPath
        self.plotItem = plotItem
        self.plotRef = plotRef
        self._windowTitle = windowTitle

        self.checkBoxStatistics.clicked.connect(self.clickStatistics)
        self.spinBoxStatistics.valueChanged.connect(self.statisticsUpdateCurve)



    ####################################
    #
    #           Slots
    #
    ####################################



    @QtCore.pyqtSlot(bool)
    def slotCheckBoxStatisticsSetChecked(self, state: bool):
        self.checkBoxStatistics.setChecked(state)
        self.statisticsLabel.setMaximumHeight(0)
        del(self.statisticsPlotRef)
        del(self.statisticsCurveId)



    @QtCore.pyqtSlot(np.ndarray, str, str, np.ndarray, str, str)
    def slotGetSelectedData(self, selectedX,
                                  selectedXLabel,
                                  selectedXUnits,
                                  selectedY,
                                  selectedYLabel,
                                  selectedYUnits):
        self.selectedX = selectedX
        self.selectedXLabel = selectedXLabel
        self.selectedXUnits = selectedXUnits
        self.selectedY = selectedY
        self.selectedYLabel = selectedYLabel
        self.selectedYUnits = selectedYUnits


    @QtCore.pyqtSlot()
    def slotUpdate(self):
        self.statisticsUpdateCurve()


    @QtCore.pyqtSlot()
    def slotClosePlot(self):
        self.statisticsClosePlot()



    ####################################
    #
    #           Internal methods
    #
    ####################################



    def statisticsGetData(self) -> Tuple[np.ndarray, np.ndarray]:

        y, binEdges   = np.histogram(self.selectedY, bins=self.spinBoxStatistics.value())
        x = np.mean(np.vstack([binEdges[0:-1],binEdges[1:]]), axis=0)

        return x, y



    def statisticsUpdateCurve(self) -> None:
        if hasattr(self, 'statisticsPlotRef'):
            x, y = self.statisticsGetData()
            self.statisticsUpdateLabel()

            self.signalUpdateCurve.emit(self.statisticsPlotRef,
                                        self.statisticsCurveId,
                                        '',
                                        x,
                                        y,
                                        False)


    def statisticsUpdateLabel(self) -> None:
        if hasattr(self, 'statisticsPlotRef'):

            mean   = np.nanmean(self.selectedY)
            std    = np.nanstd(self.selectedY)
            median = np.nanmedian(self.selectedY)
            xLabelUnits = self.plotItem.axes['left']['item'].labelUnits

            # We add some statistics info on the GUI
            txt = 'mean: {}{}<br/>'\
                  'std: {}{}<br/>'\
                  'median: {}{}'.format(parse_number(mean, self.config['fitParameterNbNumber'], unified=True),
                                        xLabelUnits,
                                        parse_number(std, self.config['fitParameterNbNumber'], unified=True),
                                        xLabelUnits,
                                        parse_number(median, self.config['fitParameterNbNumber'], unified=True),
                                        xLabelUnits)

            self.statisticsLabel.setText(txt)
            self.statisticsLabel.setMaximumHeight(16777215)




    def clickStatistics(self) -> None:
        """
        Method called when user click on the integrate checkbox.
        Add a plot containing the histogram of the chosen data.
        """

        # If user wants to plot the histogram, we add a new plotWindow
        if self.checkBoxStatistics.isChecked():

            xLabelText  = self.plotItem.axes['left']['item'].labelText
            xLabelUnits = self.plotItem.axes['left']['item'].labelUnits
            yLabelText  = 'Count'
            yLabelUnits = ''

            title   = self._windowTitle+' - histogram'
            self.statisticsCurveId = self.selectedYLabel+'histogram'
            self.statisticsPlotRef = self.plotRef+'histogram'

            self.statisticsUpdateLabel()

            self.signal2MainWindowAddPlot.emit(1, # runId
                                               self.statisticsCurveId, # curveId
                                               title, # plotTitle
                                               title, # windowTitle
                                               self.statisticsPlotRef, # plotRef
                                               self.databaseAbsPath, # databaseAbsPath
                                               self.statisticsGetData(), # data
                                               xLabelText, # xLabelText
                                               xLabelUnits, # xLabelUnits
                                               yLabelText, # yLabelText
                                               yLabelUnits, # yLabelUnits
                                               '', # zLabelText
                                               '') # zLabelUnits
        # Otherwise, we close the existing one
        else:
            self.statisticsClosePlot()



    def statisticsClosePlot(self) -> None:
        if hasattr(self, 'statisticsPlotRef'):
            self.signalClose1dPlot.emit(self.statisticsPlotRef)
            self.statisticsLabel.setMaximumHeight(0)
